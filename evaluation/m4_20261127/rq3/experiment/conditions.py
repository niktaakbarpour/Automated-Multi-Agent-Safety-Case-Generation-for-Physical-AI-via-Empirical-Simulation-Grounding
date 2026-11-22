"""Model inputs for the RQ3 model-only comparison under T, R and C (M4 task A3). CPU only.

The Critic's own prompt builder (critic.llm.build_messages) makes the full view of a case, with no rule-based
finding in it (`already_found` is empty, as critic.llm.run does with rq3_rule_blind=True). Each condition then
removes what it may not see:

    T  text only: graphs, execution conclusion and evaluation context. No evidence records, no checker
       assessments, no retrieval context.
    R  retrieval only: T plus the evidence records and the retrieval context. No checker assessments.
    C  requirement-checked: R plus the checker-admission log and a checker status. When no checker assessment
       is admitted, C carries only that status ("status only") and no verdict.

The system prompt, the user-message wording and the keys of the view are the same in all three conditions,
except that C adds one key, checker_status; only the values above differ. With an empty admission log (both R1
parents), R is exactly what critic.llm.run(..., rq3_rule_blind=True) sends, and so is C without checker_status. Screening of model findings (scoring) always uses the full case, so the
grounding gates are identical across conditions.
"""
from copy import deepcopy
import hashlib
import json

from critic import checks, llm as L

CONDITIONS = ('T', 'R', 'C')
USER_PREFIX = 'Review this argument bundle. Input JSON:\n'
STATUS_NONE_ADMITTED = ('No checker assessment is admitted for this execution. Admission of R1 checker results as '
                        'physical evidence is blocked in this project, so no requirement-checked verdict is '
                        'available.')
STATUS_SYNTHETIC = ('The admitted checker assessments listed under checker_assessments are synthetic test-fixture '
                    'outputs, not validated empirical results.')
STATUS_ADMITTED = 'The admitted checker assessments are listed under checker_assessments.'


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def screening_inputs(case):
    """(records, checker admission) of the full case, used to screen model findings in every condition."""
    findings, info = checks.run_all(deepcopy(case))
    if not info['input_valid']:
        raise ValueError('the case fails the Critic input checks; it belongs to the validation stratum')
    return info['records'], info['checker_admission']


def c_availability(admission):
    """'status_only' (nothing admitted), 'synthetic_only' or 'admitted'."""
    admitted = [a for a in admission if a['admitted']]
    if not admitted:
        return 'status_only'
    if all(a['route'] == 'synthetic_test_fixture' for a in admitted):
        return 'synthetic_only'
    return 'admitted'


def build(case):
    """(system prompt, {condition: user message}, metadata) for one case."""
    records, admission = screening_inputs(case)
    system, user = L.build_messages(case, [], records, admission)
    if not user.startswith(USER_PREFIX):
        raise ValueError('critic.llm.build_messages changed its user-message wording')
    full = json.loads(user[len(USER_PREFIX):])
    if full.get('already_found') != []:
        raise ValueError('rule-based findings must not reach the model')
    availability = c_availability(admission)
    views = {}
    views['T'] = {**deepcopy(full), 'evidence': [], 'checker_assessments': [], 'retrieval_context': None}
    views['R'] = {**deepcopy(full), 'checker_assessments': []}
    status = {'status_only': STATUS_NONE_ADMITTED, 'synthetic_only': STATUS_SYNTHETIC,
              'admitted': STATUS_ADMITTED}[availability]
    views['C'] = {**deepcopy(full), 'checker_status': status}
    users = {c: USER_PREFIX + json.dumps(views[c], indent=1, ensure_ascii=False) for c in CONDITIONS}
    meta = {'c_availability': availability, 'n_records_in_r': len(views['R']['evidence']),
            'n_admitted_checker_assessments': sum(a['admitted'] for a in admission),
            'retrieval_context_in_r': views['R']['retrieval_context'] is not None}
    return system, users, meta
