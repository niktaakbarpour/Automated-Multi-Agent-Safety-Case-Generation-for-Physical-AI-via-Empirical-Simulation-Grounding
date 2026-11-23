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
APPROVER = 'Alex Hashemi'
APPROVAL_NOTE = ('Approved under the fixed rule in rq4/RQ4_PROTOCOL.md, set before any revision output existed: '
                 'the finding is on the node of the planted defect and its category is acceptable for the '
                 'defect type. The approver wrote the planted defects and their labels.')
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


def approval_decisions(report, label):
    """The fixed approval rule: approve exactly the findings on the planted defect. Others get no decision,
    so the revision carries them forward untouched."""
    return [{'criticism_id': c['criticism_id'], 'decision': 'approved', 'decided_by': 'human_review',
             'reviewer': APPROVER, 'note': APPROVAL_NOTE}
            for c in report['criticisms'] if matches_label(c, label)]


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

    def __init__(self, case):
        self.case = case
        self.case_id = case['case_id']
        self.critic_request, self.label = load_case(self.case_id)
        self.report = critic_report(case)
        self.decisions = approval_decisions(self.report, self.label)
        if len(self.decisions) != 1:
            raise ValueError(f'{self.case_id}: expected exactly one finding on the planted defect, '
                             f'found {len(self.decisions)}')
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


def states():
    return [CaseState(c) for c in CASES]


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
