"""LLM step: prompt construction, model backends and strict screening of model output.

Backends are interchangeable, so the model can change without touching the Critic:
  NullLLM              no model; rule-based checks only
  ScriptedLLM          returns fixed text (tests and offline demos)
  OpenAICompatibleLLM  any /v1/chat/completions server, e.g. vLLM on Hestia

LLM findings are always labelled llm_proposed, always need human review and are never
blocking on their own. Every model finding is checked against FINDING_SCHEMA and the
grounding rules in _rejection_reason; anything that fails is rejected and kept in the
report for inspection. A reply that cannot be used at all makes the review
'completed_llm_failed', never a silent empty critique; so does a server reply that did not
finish (finish_reason other than "stop") or came from another model than the one requested.
Each call leaves a trace in the report (prompt, input and request hashes, effective settings,
raw reply, and the server's response id, model, finish_reason and token usage).
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import contract as K
from . import schema as SCHEMA
from .checks import _interval, _list, _overlaps, _scope, finding

PROMPT_VERSION = 'critic-prompt/v4'
PROMPT_PATH = Path(__file__).with_name('prompts') / 'critic_system_v4.md'
# Node types that state the conclusion side of an argument; an unresolved one keeps its uncertainty open.
CONCLUSION_NODES = {'goal', 'unresolved_claim', 'defeater'}
RAW_RESPONSE_LIMIT = 65536  # characters kept in the report; the hash always covers the whole reply

# Categories the rule-based checks decide (structure, evidence references, scope, coverage, related
# cases). A model may not raise them: on input that passed validation they would be unsupported.
RULE_ONLY_CATEGORIES = {'C01', 'C02', 'C03', 'C04', 'C11'}
MODEL_CATEGORIES = sorted(set(K.CATEGORIES) - RULE_ONLY_CATEGORIES)

FINDING_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['category', 'explanation', 'suggested_action'],
    'properties': {
        'object_id': {'type': ['string', 'null']},
        'node_id': {'type': ['string', 'null']},
        'category': {'enum': sorted(K.CATEGORIES)},
        'severity': {'enum': list(K.SEVERITIES)},
        'explanation': {'type': 'string', 'minLength': 1},
        'evidence_ids': {'type': 'array', 'items': {'type': 'string'}, 'uniqueItems': True},
        'suggested_action': {'type': 'string', 'minLength': 1},
    },
}
REPLY_SCHEMA = {'type': 'object', 'required': ['findings'], 'properties': {'findings': {'type': 'array'}}}


def _sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _without_credentials(url):
    parts = urllib.parse.urlsplit(url)
    if parts.username is None and parts.password is None:
        return url
    host = parts.hostname or ''
    host = f'[{host}]' if ':' in host else host  # IPv6
    netloc = host + (f':{parts.port}' if parts.port else '')
    return urllib.parse.urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _safe_digest(value):
    """Canonical-JSON sha256, or None for a value canonical JSON cannot encode (e.g. NaN inside an opaque field)."""
    try:
        return K.digest(value)
    except (TypeError, ValueError):
        return None


class _Backend:
    def messages(self, system, user):
        """The chat messages this backend sends for (system, user)."""
        return [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]

    def call(self, system, user):
        """(reply text, response metadata). Backends without a server have no metadata (None)."""
        return self.complete(system, user), None

    def response_problem(self, metadata):
        """Why a server reply cannot be used even if its text parses, or None."""
        return None

    def settings(self):
        return {}


class NullLLM(_Backend):
    """No model: the Critic runs its rule-based checks only."""
    name = None
    backend = 'none'

    def complete(self, system, user):
        return None


class ScriptedLLM(_Backend):
    """Returns a fixed reply. For tests and offline demonstrations, never for results."""
    backend = 'scripted'

    def __init__(self, text, name='scripted'):
        self.text, self.name = text, name

    def complete(self, system, user):
        return self.text

    def settings(self):
        return {'scripted_reply_sha256': _sha256_text(self.text) if isinstance(self.text, str) else None}


# Sampling and prompting settings taken from each model's official model card.
# Checked in order; the first key contained in the model name wins.
MODEL_PRESETS = {
    # R1-Distill card: temperature 0.5-0.7 (0.6 recommended); no system prompt, all instructions in the user turn.
    'deepseek-r1-distill': {'temperature': 0.6, 'extra_body': {'top_p': 0.95}, 'system_in_user': True},
    # Qwen3 card (thinking mode): temperature 0.6, top_p 0.95, top_k 20; "DO NOT use greedy decoding".
    'qwen3': {'temperature': 0.6, 'extra_body': {'top_p': 0.95, 'top_k': 20}},
    # gpt-oss card: harmony format (applied by vLLM's chat template); reasoning level set in the system prompt.
    'gpt-oss': {'system_suffix': '\nReasoning: medium'},
}


def preset_for(model_name):
    name = (model_name or '').lower()
    return next((preset for key, preset in MODEL_PRESETS.items() if key in name), {})


class OpenAICompatibleLLM(_Backend):
    """Chat-completions client using only the standard library.

    Sampling follows the named model's card (MODEL_PRESETS) unless overridden;
    unknown models use temperature 0.
    """
    backend = 'openai_compatible'

    def __init__(self, base_url=None, model=None, api_key=None, temperature=None,
                 max_tokens=8192, timeout=600, extra_body=None, accepted_models=()):
        base_url = base_url or os.environ.get('CRITIC_LLM_BASE_URL', 'http://localhost:8000/v1')
        self.base_url = base_url.rstrip('/')
        self.name = model or os.environ.get('CRITIC_LLM_MODEL')
        if not self.name:
            raise ValueError('Set a model name (--model or CRITIC_LLM_MODEL).')
        self.api_key = api_key or os.environ.get('CRITIC_LLM_API_KEY', 'EMPTY')
        preset = preset_for(self.name)
        self.temperature = preset.get('temperature', 0.0) if temperature is None else temperature
        self.max_tokens, self.timeout = max_tokens, timeout
        self.extra_body = {**preset.get('extra_body', {}), **(extra_body or {})}
        self.system_in_user = preset.get('system_in_user', False)
        self.system_suffix = preset.get('system_suffix', '')
        # The server must answer as the requested model, or as an alias the caller names explicitly (e.g. a
        # served-model-name or a pinned checkpoint path); nothing is assumed.
        self.accepted_models = sorted({self.name, *accepted_models})

    def messages(self, system, user):
        system += self.system_suffix
        if self.system_in_user:
            return [{'role': 'user', 'content': system + '\n\n' + user}]
        return [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]

    def settings(self):
        """Every setting that shapes the request. The API key, and any user:password in the URL, are never
        recorded."""
        return {'base_url': _without_credentials(self.base_url), 'model': self.name, 'temperature': self.temperature,
                'max_tokens': self.max_tokens, 'timeout_s': self.timeout, 'extra_body': self.extra_body,
                'system_in_user': self.system_in_user, 'system_suffix': self.system_suffix,
                'accepted_models': self.accepted_models}

    def complete(self, system, user):
        return self.call(system, user)[0]

    def response_problem(self, metadata):
        if metadata['finish_reason'] != 'stop':
            return (f"the server reply did not finish normally (finish_reason {metadata['finish_reason']!r}, not "
                    "'stop'), so it may be cut off or filtered and is not used")
        if metadata['model'] not in self.accepted_models:
            return (f"the server answered as model {metadata['model']!r}, not the requested "
                    f"{', '.join(map(repr, self.accepted_models))}")
        return None

    def call(self, system, user):
        body = {'model': self.name, 'temperature': self.temperature, 'max_tokens': self.max_tokens,
                'messages': self.messages(system, user), **self.extra_body}
        request = urllib.request.Request(
            self.base_url + '/chat/completions', data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.api_key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'LLM server returned HTTP {exc.code}: {exc.read()[:300]!r}') from exc
        return completion(payload)


def completion(payload):
    """(text, metadata) from a chat-completions response; raises ValueError if it is not one."""
    choices = payload.get('choices') if isinstance(payload, dict) else None
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict) \
            or not isinstance(choices[0].get('message'), dict):
        raise ValueError('the server reply is not a chat completion with exactly one choice')
    choice = choices[0]
    content = choice['message'].get('content')
    if content is not None and not isinstance(content, str):
        raise ValueError(f'the server reply content is {type(content).__name__}, not text')
    usage = payload.get('usage') if isinstance(payload.get('usage'), dict) else {}

    def text_or_none(value):
        return value if isinstance(value, str) else None
    metadata = {'id': text_or_none(payload.get('id')), 'model': text_or_none(payload.get('model')),
                'finish_reason': text_or_none(choice.get('finish_reason')),
                'usage': {k: usage[k] if isinstance(usage.get(k), int) and not isinstance(usage.get(k), bool)
                          and usage[k] >= 0 else None
                          for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')}}
    return content or '', metadata


# ------------------------------------------------------------------ prompt

NODE_FIELDS = ('id', 'type', 'statement', 'validation_status', 'origin', 'evidence_id', 'physical_claim')
RECORD_FIELDS = ('execution_id', 'object_id', 'kind', 'measurement_type', 'interval', 'validation_status',
                 'capability', 'uncertainty', 'limitations')
CONTEXT_FIELDS = ('requirement_id', 'requirement_version', 'execution_id', 'protected_objects',
                  'support_surfaces', 'monitored_interval')


def build_messages(req, deterministic, records, admission=()):
    """A compact, self-contained view of the request for the model. Returns (system, user)."""
    graphs = []
    for item in req['argument_bundle']['graphs']:
        g = item['graph'] if isinstance(item.get('graph'), dict) else {}
        nodes = [n for n in _list(g.get('nodes')) if isinstance(n, dict)]
        edges = [e for e in _list(g.get('edges')) if isinstance(e, dict)]
        graphs.append({
            'object_id': item['object_id'],
            'nodes': [{**{k: n.get(k) for k in NODE_FIELDS}, 'interval': _scope(n).get('interval')} for n in nodes],
            'edges': [[e.get('source'), e.get('type'), e.get('target')] for e in edges],
        })
    view = {
        'evaluation_context': {k: req['evaluation_context'].get(k) for k in CONTEXT_FIELDS},
        'graphs': graphs,
        'execution_conclusion': req['argument_bundle']['execution_conclusion'],
        'evidence': [{'id': rid, **{k: r.get(k) for k in RECORD_FIELDS}} for rid, r in records.items()],
        # Only the Critic's admission log is shown: a model never sees an assessment as usable
        # unless the deterministic admission rules accepted it.
        'checker_assessments': [{k: a[k] for k in ('assessment_id', 'object_id', 'outcome', 'applicability',
                                                   'interval', 'admitted', 'route')} for a in admission],
        'retrieval_context': req['retrieval_context'],
        'already_found': [{k: f[k] for k in ('category', 'object_id', 'node_id', 'explanation')}
                          for f in deterministic],
    }
    system = PROMPT_PATH.read_text(encoding='utf-8')
    user = 'Review this argument bundle. Input JSON:\n' + json.dumps(view, indent=1, ensure_ascii=False)
    return system, user


# ------------------------------------------------------------------ parsing and screening

_THINK = re.compile(r'<think>.*?</think>', re.S)


def extract_json(text):
    """Return the first JSON object with a "findings" key in a model reply.

    Tolerates <think> blocks, markdown fences and text around the JSON.
    """
    text = _THINK.sub('', text or '')
    decoder = json.JSONDecoder()
    for match in re.finditer(r'\{', text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and 'findings' in value:
            return value
    raise ValueError('No JSON object with a "findings" list in the model reply.')


def screen(raw_findings, req, records, deterministic, admission=()):
    """Keep only findings that match FINDING_SCHEMA and pass the grounding rules.

    Returns (accepted findings, rejected [{reason, finding}]). raw_findings must be a list.
    """
    ctx = req['evaluation_context']
    configured = set(ctx['protected_objects'])
    nodes_by_object, kinds_by_object = {}, {}
    for item in req['argument_bundle']['graphs']:
        g = item['graph'] if isinstance(item.get('graph'), dict) else {}
        nodes = _list(g.get('nodes'))
        nodes_by_object[item['object_id']] = {
            n['id']: _scope(n) for n in nodes if isinstance(n, dict) and isinstance(n.get('id'), str)}
        kinds_by_object[item['object_id']] = {
            n['id']: (n.get('type'), n.get('validation_status')) for n in nodes
            if isinstance(n, dict) and isinstance(n.get('id'), str)}
    known = {rid: {'execution': r.get('execution_id'), 'object': r.get('object_id'), 'interval': r.get('interval'),
                   'when': (r.get('domain'), r.get('clock'))} for rid, r in records.items()}
    assessments = {a['assessment_id']: a['object_id'] for a in admission if a['admitted']}
    taken = {(f['object_id'], f['node_id'], f['category']) for f in deterministic}
    monitored = ctx['monitored_interval']
    scope = {'configured': configured, 'nodes': nodes_by_object, 'records': known, 'assessments': assessments,
             'execution': ctx['execution_id'], 'taken': taken, 'monitored': _interval(monitored.get('interval')),
             'when': (monitored.get('domain'), monitored.get('clock')), 'kinds': kinds_by_object,
             'conclusion': req['argument_bundle']['execution_conclusion']}

    accepted, rejected = [], []
    for f in raw_findings:
        reason = _rejection_reason(f, scope)
        if reason:
            rejected.append({'reason': reason, 'finding': f})
            continue
        oid, nid = f.get('object_id'), f.get('node_id')
        taken.add((oid, nid, f['category']))
        accepted.append(finding(
            'LLM', f['category'], f['explanation'].strip(), f['suggested_action'].strip(),
            severity=f.get('severity', 'medium'), blocking=False, object_id=oid, node_id=nid,
            evidence_ids=f.get('evidence_ids', []), requirement_refs=[PROMPT_VERSION], source='llm_proposed',
            human_review_required=True))
    return accepted, rejected


def _rejection_reason(f, scope):
    """Why a model finding cannot be used, or None if it is acceptable."""
    problems = SCHEMA.errors(f, FINDING_SCHEMA, limit=3)
    if problems:
        return 'does not match the finding format: ' + '; '.join(problems)
    category, oid, nid = f['category'], f.get('object_id'), f.get('node_id')
    evidence = f.get('evidence_ids', [])
    if not f['explanation'].strip() or not f['suggested_action'].strip():
        return 'missing explanation or suggested_action'
    if category in RULE_ONLY_CATEGORIES:
        return f'category {category} is decided by the rule-based checks only'
    if oid is not None and oid not in scope['configured']:
        return f'object {oid!r} is not a configured protected object'
    target = None  # the graph object the finding is about: its own, or the one graph that has its node
    if nid is not None:
        holders = [o for o, nodes in scope['nodes'].items() if nid in nodes and (oid is None or o == oid)]
        if not holders:
            return f'node {nid!r} does not exist in the cited graph'
        if len(holders) > 1:
            return (f'node {nid!r} exists in the graphs of {", ".join(sorted(holders))}, so without an object_id the '
                    'finding has no unique target')
        target = holders[0]
    about_object = oid if oid is not None else target
    if any(e not in scope['records'] and e not in scope['assessments'] for e in evidence):
        return 'cites evidence IDs that are not in the package (possible invention)'
    for e in evidence:
        rec = scope['records'].get(e) or {'execution': scope['execution'], 'object': scope['assessments'].get(e)}
        if rec['execution'] != scope['execution'] or (about_object is not None and rec['object'] != about_object):
            return (f"cites {e}, which is about {rec['object']} in {rec['execution']}, not the finding's object and "
                    'execution')
        if e in scope['records']:
            reason = _time_reason(e, rec, scope, scope['nodes'][target][nid] if target is not None else None)
            if reason:
                return reason
    if category == 'C09':
        reason = _already_cautious(about_object, target, nid, scope)
        if reason:
            return reason
    if category == 'C07' and (oid is None or not any(scope['assessments'].get(e) == oid for e in evidence)):
        return 'a contradiction (C07) must cite an admitted checker assessment for the same object'
    if (oid, nid, category) in scope['taken']:
        return 'duplicate of a deterministic finding'
    return None


def _already_cautious(oid, target, nid, scope):
    """A C09 (ignored uncertainty) aimed at a conclusion that is already insufficient_information, the most cautious
    outcome, through an unresolved conclusion node or no node at all, has nothing to object to: nothing there
    treats the uncertain evidence as exact. Seen with Qwen3-32B on Case C in the R2 audit."""
    conclusion = scope['conclusion']
    claims = conclusion.get('object_outcomes') if isinstance(conclusion.get('object_outcomes'), dict) else {}
    objects = [oid] if oid is not None else sorted(scope['configured'])
    if not objects or any(claims.get(o) != K.INSUFFICIENT for o in objects):
        return None
    if oid is None and conclusion.get('claimed_outcome') != K.INSUFFICIENT:
        return None
    if nid is not None:
        kind, status = scope['kinds'].get(target, {}).get(nid, (None, None))
        if kind not in CONCLUSION_NODES or status not in ('unresolved', 'proposed'):
            return None
    where = f'node {nid} ({kind}, {status})' if nid is not None else 'the conclusion'
    about = oid if oid is not None else 'every object and the execution'
    return (f'C09 says uncertainty was ignored, but the draft concludes insufficient_information for {about} and '
            f'{where} keeps the question open; a C09 must name a statement that treats uncertain evidence as exact')


def _time_reason(e, rec, scope, node_scope):
    """A cited record must be on the review's clock and overlap the monitored interval, and the cited node's
    temporal scope if it has one (audit R2-05)."""
    span = _interval(rec['interval'])
    if rec['when'] != scope['when'] or span is None or scope['monitored'] is None \
            or not _overlaps(span, scope['monitored']):
        monitored = list(scope['monitored']) if scope['monitored'] else None
        return (f"cites {e}, which covers {rec['when'][0]} {rec['interval']} on {rec['when'][1]}, outside the "
                f"monitored interval {monitored} on {scope['when'][1]}")
    if node_scope and 'interval' in node_scope:
        node_span = _interval(node_scope.get('interval'))
        if (node_scope.get('domain'), node_scope.get('clock')) != rec['when'] or node_span is None \
                or not _overlaps(span, node_span):
            return (f"cites {e}, whose interval {rec['interval']} does not overlap the cited node's "
                    f"{node_scope.get('interval')}")
    return None


def empty_status(llm, error=None):
    """The llm block of a report before (or instead of) a model call."""
    return {'backend': llm.backend, 'model': llm.name, 'prompt_version': PROMPT_VERSION,
            'called': False, 'ok': False, 'latency_s': None, 'error': error,
            'prompt_sha256': None, 'input_sha256': None, 'request_sha256': None, 'settings': None,
            'raw_response': None, 'raw_response_truncated': False, 'response_sha256': None, 'response': None,
            'accepted': 0, 'rejected': 0}


def run(llm, req, deterministic, records, admission=()):
    """Ask the model once and screen its reply. Returns (accepted, rejected, status).

    Nothing in here may break the review: building the prompt, the call, parsing and screening all run
    inside one error boundary, and any failure is reported in status with ok false.
    """
    status = empty_status(llm)
    if isinstance(llm, NullLLM):
        status['ok'] = True
        return [], [], status
    started = time.monotonic()
    try:
        system, user = build_messages(req, deterministic, records, admission)
        status['prompt_sha256'] = _sha256_text(PROMPT_PATH.read_text(encoding='utf-8'))
        status['input_sha256'] = K.digest(llm.messages(system, user))
        status['request_sha256'] = _safe_digest(req)
        status['settings'] = llm.settings()
        status['called'] = True
        reply, status['response'] = llm.call(system, user)
        if not isinstance(reply, str):
            raise ValueError(f'the model returned {type(reply).__name__}, not text')
        status['response_sha256'] = _sha256_text(reply)
        status['raw_response'] = reply[:RAW_RESPONSE_LIMIT]
        status['raw_response_truncated'] = len(reply) > RAW_RESPONSE_LIMIT
        unusable = llm.response_problem(status['response']) if status['response'] is not None else None
        if unusable:
            raise ValueError(unusable)
        parsed = extract_json(reply)
        problems = SCHEMA.errors(parsed, REPLY_SCHEMA, limit=3)
        if problems:
            raise ValueError('the reply is not {"findings": [...]}: ' + '; '.join(problems))
        accepted, rejected = screen(parsed['findings'], req, records, deterministic, admission)
    except Exception as exc:  # a failed model step is reported, never allowed to break the review
        status['error'] = f'{type(exc).__name__}: {exc}'
        return [], [], status
    finally:
        status['latency_s'] = round(time.monotonic() - started, 3)
    status.update(ok=True, accepted=len(accepted), rejected=len(rejected))
    return accepted, rejected, status
