"""LLM step: prompt construction, model backends and strict screening of model output.

Backends are interchangeable, so the model can change without touching the Critic:
  NullLLM              no model; rule-based checks only
  ScriptedLLM          returns fixed text (tests and offline demos)
  OpenAICompatibleLLM  any /v1/chat/completions server, e.g. vLLM on Hestia

LLM findings are always labelled llm_proposed, always need human review and are never
blocking on their own. A finding that cites an unknown object, node or evidence ID is
rejected and kept in the report for inspection.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import contract as K
from .checks import _list, _scope, finding

PROMPT_VERSION = 'critic-prompt/v1'
PROMPT_PATH = Path(__file__).with_name('prompts') / 'critic_system_v1.md'


class NullLLM:
    """No model: the Critic runs its rule-based checks only."""
    name = None
    backend = 'none'

    def complete(self, system, user):
        return None


class ScriptedLLM:
    """Returns a fixed reply. For tests and offline demonstrations, never for results."""
    backend = 'scripted'

    def __init__(self, text, name='scripted'):
        self.text, self.name = text, name

    def complete(self, system, user):
        return self.text


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


class OpenAICompatibleLLM:
    """Chat-completions client using only the standard library.

    Sampling follows the named model's card (MODEL_PRESETS) unless overridden;
    unknown models use temperature 0.
    """
    backend = 'openai_compatible'

    def __init__(self, base_url=None, model=None, api_key=None, temperature=None,
                 max_tokens=8192, timeout=600, extra_body=None):
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

    def complete(self, system, user):
        system += self.system_suffix
        if self.system_in_user:
            messages = [{'role': 'user', 'content': system + '\n\n' + user}]
        else:
            messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]
        body = {'model': self.name, 'temperature': self.temperature, 'max_tokens': self.max_tokens,
                'messages': messages, **self.extra_body}
        request = urllib.request.Request(
            self.base_url + '/chat/completions', data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.api_key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'LLM server returned HTTP {exc.code}: {exc.read()[:300]!r}') from exc
        return payload['choices'][0]['message'].get('content') or ''


# ------------------------------------------------------------------ prompt

NODE_FIELDS = ('id', 'type', 'statement', 'validation_status', 'origin', 'evidence_id', 'physical_claim')
RECORD_FIELDS = ('execution_id', 'object_id', 'kind', 'measurement_type', 'interval', 'validation_status',
                 'capability', 'uncertainty', 'limitations')
CONTEXT_FIELDS = ('requirement_id', 'requirement_version', 'execution_id', 'protected_objects',
                  'support_surfaces', 'monitored_interval')
ASSESSMENT_FIELDS = ('assessment_id', 'authority', 'object_id', 'applicability', 'outcome', 'interval')


def build_messages(req, deterministic, records):
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
        'checker_assessments': [{k: a.get(k) for k in ASSESSMENT_FIELDS} for a in req['checker_assessments']],
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


def screen(raw_findings, req, records, deterministic):
    """Keep only well-formed findings that reference real objects, nodes and evidence.

    Returns (accepted findings, rejected [{reason, finding}]).
    """
    if not isinstance(raw_findings, list):
        return [], [{'reason': 'findings is not a list', 'finding': raw_findings}]
    configured = set(req['evaluation_context']['protected_objects'])
    nodes_by_object = {}
    for item in req['argument_bundle']['graphs']:
        g = item['graph'] if isinstance(item.get('graph'), dict) else {}
        nodes = _list(g.get('nodes'))
        nodes_by_object[item['object_id']] = {
            n['id'] for n in nodes if isinstance(n, dict) and isinstance(n.get('id'), str)}
    all_nodes = set().union(*nodes_by_object.values())
    known_ids = set(records) | {a.get('assessment_id') for a in req['checker_assessments']
                                if isinstance(a.get('assessment_id'), str)}
    taken = {(f['object_id'], f['node_id'], f['category']) for f in deterministic}

    accepted, rejected = [], []
    for f in raw_findings:
        reason = _rejection_reason(f, configured, nodes_by_object, all_nodes, known_ids, taken)
        if reason:
            rejected.append({'reason': reason, 'finding': f})
            continue
        taken.add((f.get('object_id'), f.get('node_id'), f['category']))
        accepted.append(finding(
            'LLM', f['category'], f['explanation'].strip(), f['suggested_action'].strip(),
            severity=f.get('severity') if f.get('severity') in K.SEVERITIES else 'medium', blocking=False,
            object_id=f.get('object_id'), node_id=f.get('node_id'), evidence_ids=f.get('evidence_ids') or [],
            requirement_refs=[PROMPT_VERSION], source='llm_proposed', human_review_required=True))
    return accepted, rejected


def _rejection_reason(f, configured, nodes_by_object, all_nodes, known_ids, taken):
    """Why a model finding cannot be used, or None if it is acceptable."""
    if not isinstance(f, dict):
        return 'finding is not an object'
    if f.get('category') not in K.CATEGORIES:
        return f'unknown category {f.get("category")!r}'
    if not all(isinstance(f.get(k), str) and f[k].strip() for k in ('explanation', 'suggested_action')):
        return 'missing explanation or suggested_action'
    oid, nid, evidence = f.get('object_id'), f.get('node_id'), f.get('evidence_ids') or []
    if not all(x is None or isinstance(x, str) for x in (oid, nid)):
        return 'object_id and node_id must be strings or null'
    if oid is not None and oid not in configured:
        return f'object {oid!r} is not a configured protected object'
    if nid is not None and nid not in (nodes_by_object.get(oid, set()) if oid else all_nodes):
        return f'node {nid!r} does not exist in the cited graph'
    if not isinstance(evidence, list) or not all(isinstance(e, str) and e in known_ids for e in evidence):
        return 'cites evidence IDs that are not in the package (possible invention)'
    if (oid, nid, f['category']) in taken:
        return 'duplicate of a deterministic finding'
    return None


def run(llm, req, deterministic, records):
    """Ask the model once and screen its reply. Returns (accepted, rejected, status)."""
    status = {'backend': llm.backend, 'model': llm.name, 'prompt_version': PROMPT_VERSION,
              'called': False, 'ok': False, 'latency_s': None, 'error': None}
    if isinstance(llm, NullLLM):
        status['ok'] = True
        return [], [], status
    system, user = build_messages(req, deterministic, records)
    started = time.monotonic()
    status['called'] = True
    try:
        reply = llm.complete(system, user)
        parsed = extract_json(reply)
    except Exception as exc:  # a failed model call is reported, never allowed to break the review
        status['error'] = f'{type(exc).__name__}: {exc}'
        return [], [], status
    finally:
        status['latency_s'] = round(time.monotonic() - started, 3)
    accepted, rejected = screen(parsed['findings'], req, records, deterministic)
    status['ok'] = True
    return accepted, rejected, status
