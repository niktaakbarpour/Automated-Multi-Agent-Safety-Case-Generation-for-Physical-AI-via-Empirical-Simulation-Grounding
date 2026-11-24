"""Shared pieces of the RQ4 planted-defect repair experiment (M4). CPU only.

Three planted unsupported-guarantee defects (RQ3 mutations P1-M1a, P1-M1b, P2-M1c) each have one real Critic
finding. Two methods propose a repair for that finding through the existing revision engine
(drafter.revision): the deterministic template adapter and Qwen3-32B. Both get exactly the same permitted
information, and the engine checks and applies every edit the same way for both.

Nothing in drafter/revision or critic/ is changed. The Qwen replies come from a GPU batch run by run_batch.py
(rq3/experiment, unchanged frozen settings); here they are replayed through a recorded model adapter.
"""
from copy import deepcopy
from pathlib import Path
import csv
import hashlib
import json
import re
import sys

from critic import checks, contract as K, critic as CR, llm as L
from drafter.revision import adapters as A, contract as C, engine as E

HERE = Path(__file__).resolve().parent
RQ4 = HERE.parent
M4 = RQ4.parent
RQ3 = M4 / 'rq3'
ROOT = M4.parents[1]
sys.path.insert(0, str(RQ3 / 'experiment'))
import run_batch as RB  # noqa: E402  (rq3 runner, also used for the RQ4 GPU stages)
import settings as RQ3_SETTINGS  # noqa: E402

EXPERIMENT_VERSION = 'rq4-planted-repair/0.1.0'
PROMPT_VERSION = 'rq4-revision-prompt/v1'
PROMPT_PATH = HERE / 'revision_prompt.md'
USER_PREFIX = 'Revise the argument as the approved findings require. Input JSON:\n'
REPEATS = 3            # Qwen revision samples per case
STAGE2_REPEATS = 3     # second Critic reviews per original bundle and per template revision
FROZEN = RQ3_SETTINGS.SETTINGS
# Human finding decisions: filled in by hand by the approver, read here, never generated.
APPROVALS_PATH = RQ4 / 'FINDING_APPROVALS.csv'
APPROVAL_COLUMNS = ('case_id', 'critic_report_sha256', 'criticism_id', 'finding_source', 'check_id', 'category',
                    'object_id', 'node_id', 'explanation', 'on_planted_defect_node', 'decision', 'approver',
                    'approved_on', 'attestation')
HUMAN_COLUMNS = ('decision', 'approver', 'approved_on', 'attestation')
ATTESTATION = 'I read this finding and its target node myself and made this decision.'
APPROVAL_RULE = ('The fixed rule in rq4/RQ4_PROTOCOL.md, set before any revision output existed: approve the '
                 'finding on the node of the planted defect whose category is acceptable for the defect type.')
RQ3_RESPONSES = RQ3 / 'experiment' / 'real_run_20261122T142300Z' / 'RQ3_RESPONSES.jsonl'

# report_source: 'rules_only' = critic.review with no model (the finding is the rule finding);
# 'rq3_r_reply' = critic.review replaying the saved RQ3 reply whose prompt equals the production prompt.
CASES = (
    {'case_id': 'P1-M1a', 'report_source': 'rules_only', 'rq3_run_id': None},
    {'case_id': 'P1-M1b', 'report_source': 'rq3_r_reply', 'rq3_run_id': 'P1-M1b:R:r3'},
    {'case_id': 'P2-M1c', 'report_source': 'rules_only', 'rq3_run_id': None},
)


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dumps(value):
    return json.dumps(value, indent=1, ensure_ascii=False) + '\n'


def rq3_tables():
    with open(RQ3 / 'MUTATION_MANIFEST.csv', encoding='utf-8') as fh:
        manifest = {r['case_id']: r for r in csv.DictReader(fh)}
    labels = {x['case_id']: x for x in load_json(RQ3 / 'mutations' / 'gold_labels.json')}
    return manifest, labels


def load_case(case_id):
    """(critic request, label) of one planted-defect case, checked against the RQ3 manifest hash."""
    manifest, labels = rq3_tables()
    request = load_json(ROOT / manifest[case_id]['case_file'])
    if K.digest(request) != manifest[case_id]['request_sha256']:
        raise ValueError(case_id + ': case file does not match rq3/MUTATION_MANIFEST.csv')
    return request, labels[case_id]


def saved_rq3_attempt(run_id):
    """The scored RQ3 attempt for one request: the first attempt that got a reply."""
    for line in RB.read_jsonl(RQ3_RESPONSES):
        if line['run_id'] == run_id and line['reply'] is not None:
            return line
    raise ValueError(run_id + ': no saved reply')


class ReplayLLM(L._Backend):
    """Gives critic.review a reply that was saved from a real model call, with its server metadata."""
    backend = 'replayed_saved_response'

    def __init__(self, attempt):
        self.attempt = attempt
        self.name = attempt['settings'].get('model') or attempt['backend']  # scripted test replies have no model

    def call(self, system, user):
        return self.attempt['reply'], deepcopy(self.attempt['response'])

    def settings(self):
        return deepcopy(self.attempt['settings'])


def replayed_report(request, attempt):
    """critic.review on request with a saved reply. Refuses when the reply was made for another input."""
    report = CR.review(deepcopy(request), ReplayLLM(attempt))
    if report['llm']['input_sha256'] != attempt['input_sha256']:
        raise ValueError(attempt['run_id'] + ': the saved reply was made for a different Critic input')
    report['llm']['latency_s'] = attempt['latency_s']  # the original call's latency, not the replay's
    return report


def critic_report(case):
    request, _ = load_case(case['case_id'])
    if case['report_source'] == 'rules_only':
        return CR.review(deepcopy(request))
    return replayed_report(request, saved_rq3_attempt(case['rq3_run_id']))


def matches_label(criticism, label):
    location = label['expected_location']
    return (location is not None and criticism['object_id'] == location['object_id']
            and criticism['node_id'] == location['node_id']
            and criticism['category'] in label['acceptable_model_categories'])


def approval_form_rows(case_id, report, label):
    """Rows of FINDING_APPROVALS.csv for one case, with the human columns empty. on_planted_defect_node only
    helps the approver find the finding; it is not a decision."""
    return [{'case_id': case_id, 'critic_report_sha256': K.digest(report), 'criticism_id': c['criticism_id'],
             'finding_source': c['finding_source'], 'check_id': c['check_id'], 'category': c['category'],
             'object_id': c['object_id'] or '', 'node_id': c['node_id'] or '', 'explanation': c['explanation'],
             'on_planted_defect_node': 'yes' if matches_label(c, label) else 'no',
             **{k: '' for k in HUMAN_COLUMNS}} for c in report['criticisms']]


def read_csv(path):
    """(header, rows) of a CSV file."""
    with open(path, encoding='utf-8', newline='') as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def load_approvals(path=None):
    path = Path(path or APPROVALS_PATH)
    if not path.exists():
        raise ValueError(f'{path.name} is missing: the finding decisions must be recorded by hand first '
                         '(build_approval_form.py writes the blank form)')
    header, rows = read_csv(path)
    if tuple(header) != APPROVAL_COLUMNS:
        raise ValueError(f'{path.name}: the columns must be exactly {", ".join(APPROVAL_COLUMNS)}')
    return rows


def approval_decisions(case_id, report, label, rows):
    """The recorded human decisions for one case, as revision-request finding_decisions.

    Every finding of the report must have exactly one row, bound to this report by its digest. A row with a
    decision must carry the approver, an ISO date and the attestation sentence. Exactly one finding must be
    approved, and it must be the one the fixed rule names; any other finding may stay undecided (carried forward
    untouched) or be declined. Raises ValueError listing every problem."""
    problems, decisions = [], []
    mine = [r for r in rows if r['case_id'] == case_id]
    by_id = {}
    for r in mine:
        if r['criticism_id'] in by_id:
            problems.append(f"{case_id} {r['criticism_id']}: more than one row")
        by_id[r['criticism_id']] = r
    criticisms = {c['criticism_id']: c for c in report['criticisms']}
    for cid in sorted(set(by_id) - set(criticisms)):
        problems.append(f'{case_id} {cid}: no such finding in the Critic report')
    for cid in sorted(set(criticisms) - set(by_id)):
        problems.append(f'{case_id} {cid}: finding has no row')
    digest = K.digest(report)
    for cid, r in sorted(by_id.items()):
        if cid not in criticisms:
            continue
        c = criticisms[cid]
        if r['critic_report_sha256'] != digest:
            problems.append(f'{case_id} {cid}: the row was made for a different Critic report')
        for field in ('finding_source', 'check_id', 'category', 'object_id', 'node_id'):
            if r[field] != (c[field] or ''):
                problems.append(f'{case_id} {cid}: {field} differs from the report')
        decision = r['decision'].strip()
        if decision == '':
            if any(r[k].strip() for k in HUMAN_COLUMNS):
                problems.append(f'{case_id} {cid}: approver, date or attestation given without a decision')
            continue
        if decision not in ('approved', 'declined'):
            problems.append(f'{case_id} {cid}: decision must be approved, declined or empty')
            continue
        if not r['approver'].strip():
            problems.append(f'{case_id} {cid}: the approver is not named')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', r['approved_on'].strip()):
            problems.append(f'{case_id} {cid}: approved_on must be a date like 2026-11-23')
        if r['attestation'].strip() != ATTESTATION:
            problems.append(f'{case_id} {cid}: the attestation must read exactly: {ATTESTATION}')
        if decision == 'approved' and not matches_label(c, label):
            problems.append(f'{case_id} {cid}: approved, but the fixed rule does not name this finding')
        decisions.append({'criticism_id': cid, 'decision': decision, 'decided_by': 'human_review',
                          'reviewer': r['approver'].strip(),
                          'note': f"{APPROVAL_RULE} Recorded by hand on {r['approved_on'].strip()} in "
                                  f'rq4/FINDING_APPROVALS.csv.'})
    approved = [d for d in decisions if d['decision'] == 'approved']
    if not problems and len(approved) != 1:
        problems.append(f'{case_id}: exactly one finding must be approved, found {len(approved)}')
    if problems:
        raise ValueError('; '.join(problems))
    return decisions


class ProtectedFileError(ValueError):
    pass


def write_files(targets, replace=False):
    """Write {path: text}. An existing file with different content is never changed unless replace is True;
    without it, nothing is written and ProtectedFileError lists the files that would change."""
    targets = {Path(p): t for p, t in targets.items()}
    changed = [p for p, t in targets.items() if p.exists() and p.read_text(encoding='utf-8') != t]
    if changed and not replace:
        raise ProtectedFileError('refusing to change existing files: ' + ', '.join(str(p) for p in changed))
    for path, text in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8')


def stale_files(targets):
    """Paths whose saved content is missing or differs from the given text."""
    return [str(p) for p, t in targets.items() if not Path(p).exists() or Path(p).read_text(encoding='utf-8') != t]


def expected_settings_problems(settings):
    """Differences between the client settings recorded with an attempt and the frozen settings."""
    problems = []
    for key in ('model', 'temperature', 'max_tokens', 'extra_body'):
        if settings.get(key) != FROZEN[key]:
            problems.append(f'{key} {settings.get(key)!r} is not the frozen {FROZEN[key]!r}')
    if settings.get('timeout_s') != FROZEN['timeout_s']:
        problems.append(f"timeout_s {settings.get('timeout_s')!r} is not the frozen {FROZEN['timeout_s']!r}")
    if settings.get('system_in_user') is not False:
        problems.append('the system prompt was not sent as a system message')
    if FROZEN['model'] not in settings.get('accepted_models', []):
        problems.append('the accepted model names do not include the frozen model')
    return problems


def checked_attempts(responses, requests, system, allow_scripted=False):
    """{run_id: (attempt to score or None, number of attempts)} for every request of a batch.

    Refuses (ValueError listing every problem) an unknown run ID, a request answered more than once, an
    attempt made for another input (user, system or message digest), a reply whose digest is wrong, a scripted
    reply unless allow_scripted (tests only), client settings that differ from the frozen ones, and more than
    one model revision in one stage. A request with no attempt is kept as missing."""
    by_id = {r['run_id']: r for r in requests}
    problems, attempts = [], {}
    for line in responses:
        if line.get('kind') == 'run_meta':
            continue
        rid = line.get('run_id')
        if rid not in by_id:
            problems.append(f'{rid}: not a request of this batch')
            continue
        attempts.setdefault(rid, []).append(line)
    revisions = set()
    out = {}
    for rid, request in by_id.items():
        mine = attempts.get(rid, [])
        replied = [a for a in mine if a['reply'] is not None]
        if len(replied) > 1:
            problems.append(f'{rid}: answered {len(replied)} times; a request is sent again only without a reply')
        for a in mine:
            if (a['user_sha256'], a['system_sha256']) != (request['user_sha256'], request['system_sha256']):
                problems.append(f"{rid} attempt {a['attempt']}: made for a different input")
            messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': request['user']}]
            if a['input_sha256'] != K.digest(messages):
                problems.append(f"{rid} attempt {a['attempt']}: the sent messages differ from the batch")
            if a['reply'] is not None and a['reply_sha256'] != sha256_text(a['reply']):
                problems.append(f"{rid} attempt {a['attempt']}: the reply does not match its recorded digest")
            if a['backend'] == 'scripted':
                if not allow_scripted:
                    problems.append(f"{rid} attempt {a['attempt']}: a scripted test reply is not a model result")
            elif a['backend'] != 'openai_compatible':
                problems.append(f"{rid} attempt {a['attempt']}: unexpected backend {a['backend']!r}")
            else:
                problems += [f"{rid} attempt {a['attempt']}: {p}" for p in expected_settings_problems(a['settings'])]
                revisions.add(a.get('model_revision'))
        if [a['attempt'] for a in mine] != list(range(1, len(mine) + 1)):
            problems.append(f'{rid}: attempts are not numbered 1..{len(mine)} in order')
        out[rid] = ((replied[0] if replied else (mine[-1] if mine else None)), len(mine))
    if len(revisions) > 1:
        problems.append(f'more than one model revision in one stage: {sorted(map(str, revisions))}')
    if None in revisions or '' in revisions:
        problems.append('a model attempt has no recorded model revision')
    if problems:
        raise ValueError('; '.join(problems))
    return out


def revision_request(case_id, critic_request, report, decisions):
    return C.build_request(f'rq4-{case_id}', critic_request, report, finding_decisions=decisions, max_rounds=1)


def permitted_evidence(critic_request):
    """The evidence part of the permitted information: what the Critic's own model view shows (records,
    checker admission log, retrieval context), with no rule finding."""
    _, info = checks.run_all(deepcopy(critic_request))
    _, user = L.build_messages(critic_request, [], info['records'], info['checker_admission'])
    view = json.loads(user.split('\n', 1)[1])
    return {'evidence': view['evidence'], 'checker_assessments': view['checker_assessments'],
            'retrieval_context': view['retrieval_context']}


class SamePermittedInformation:
    """Wraps any adapter so that it receives the engine's context plus the same permitted evidence.
    Both methods go through this wrapper; `seen` keeps what the inner adapter was given."""

    def __init__(self, adapter, evidence):
        self.inner, self.evidence, self.seen = adapter, deepcopy(evidence), None
        self.name, self.version, self.kind = adapter.name, adapter.version, adapter.kind

    def propose(self, context):
        context = deepcopy(context)
        context['permitted_evidence'] = deepcopy(self.evidence)
        self.seen = deepcopy(context)
        return self.inner.propose(deepcopy(context))


def information_sha256(context):
    return K.digest(context)


BOOKKEEPING = ('revision_id', 'round', 'max_rounds', 'history')


def render_user(context):
    """The Qwen user message: the permitted information the template also gets, verbatim, except the run
    bookkeeping (revision_id, round, max_rounds and history, which is empty in this experiment)."""
    if context['history']:
        raise ValueError('this experiment has one round; a revision history is not expected')
    view = {k: v for k, v in context.items() if k not in BOOKKEEPING}
    return USER_PREFIX + json.dumps(view, indent=1, ensure_ascii=False)


class CaptureAdapter:
    """Records the context a model adapter would get. Proposes nothing."""
    name, version, kind = RQ3_SETTINGS.SETTINGS['model'], PROMPT_VERSION, 'model'

    def __init__(self):
        self.context = None

    def propose(self, context):
        self.context = deepcopy(context)
        return {'edits': [], 'declined': []}


_THINK = re.compile(r'<think>.*?</think>', re.S)


def parse_reply(text):
    """The first JSON object in a reply with an "edits" or "declined" key, unchanged. The engine checks its
    shape, so a malformed answer is refused there and counted. ValueError when there is no such object."""
    text = _THINK.sub('', text or '')
    decoder = json.JSONDecoder()
    for match in re.finditer(r'\{', text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and ({'edits', 'declined'} & set(value)):
            return value
    raise ValueError('no JSON object with "edits" or "declined" in the reply')


class RecordedQwenAdapter:
    """Replays one saved Qwen reply. Refuses if the context differs from the one the prompt was built from."""
    name, version, kind = RQ3_SETTINGS.SETTINGS['model'], PROMPT_VERSION, 'model'

    def __init__(self, reply, user_sha256):
        self.reply, self.user_sha256 = reply, user_sha256

    def propose(self, context):
        if sha256_text(render_user(context)) != self.user_sha256:
            raise ValueError('the revision context differs from the one the Qwen prompt was built from')
        return parse_reply(self.reply)


class CaseState:
    """Everything fixed for one case before any revision output exists."""

    def __init__(self, case, approvals=None):
        self.case = case
        self.case_id = case['case_id']
        self.critic_request, self.label = load_case(self.case_id)
        self.report = critic_report(case)
        rows = approvals if approvals is not None else load_approvals()
        self.decisions = approval_decisions(self.case_id, self.report, self.label, rows)
        self.request = revision_request(self.case_id, self.critic_request, self.report, self.decisions)
        self.evidence = permitted_evidence(self.critic_request)

    def revise(self, adapter):
        """(revision result, sha256 of the permitted information the adapter was given)."""
        wrapped = SamePermittedInformation(adapter, self.evidence)
        result = E.revise(deepcopy(self.request), wrapped)
        return result, (information_sha256(wrapped.seen) if wrapped.seen is not None else None)

    def qwen_prompt(self):
        """(user message, sha256 of the permitted information) for the Qwen batch."""
        capture = CaptureAdapter()
        _, info_sha = self.revise(capture)
        context = deepcopy(capture.context)
        return render_user(context), info_sha


def states(approvals=None):
    rows = approvals if approvals is not None else load_approvals()
    return [CaseState(c, rows) for c in CASES]


def approved_finding(state):
    approved = {d['criticism_id'] for d in state.decisions if d['decision'] == 'approved'}
    return next(c for c in state.report['criticisms'] if c['criticism_id'] in approved)


def classify_output(result):
    """What happened to one revision output, for scoring."""
    if result['outcome'] == 'revised':
        return 'revised'
    if result['outcome'] == 'failed':
        detail = result.get('status_detail') or ''
        return 'invalid_unparseable' if 'adapter failed' in detail else 'invalid_malformed'
    if result['rejected_edits']:
        return 'edit_refused'
    if any(v['issues'] for v in result['validators']):
        return 'validation_failed'
    proposal = result.get('proposal') or {}
    if proposal.get('declined') and not proposal.get('edits'):
        return 'abstained'
    return 'no_answer'
