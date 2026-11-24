"""Apply the Qwen revisions and build the second Critic batch (RQ4 stage 2). CPU only, no model.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/build_stage2.py --responses STAGE1_RESPONSES.jsonl
    (add --check to compare with the saved files)

Every one of the 9 requests gets a result record, missing ones included. The responses are refused as a whole
(nothing written) for an unknown run ID, a request answered twice, an attempt made for another input, a reply
that does not match its digest, a scripted reply, client settings that differ from the frozen ones, or more than
one model revision. A reply that did not finish normally or names another model is kept as invalid_server_reply.
Every other reply is replayed through the revision engine with the same permitted information the template got.
Results go to results/qwen/. Saved results and batches are never overwritten.

The second Critic batch (batch_stage2/) is the production Critic (critic.review, not rule-blind, rule findings
shown to the model as in production) on: each original argument (STAGE2_REPEATS times), each template
revision (STAGE2_REPEATS times, as it is the same for every sample) and each Qwen revision (once). So every
method gets STAGE2_REPEATS second reviews per case.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM  # noqa: E402
from critic import contract as K, critic as CR, llm as L  # noqa: E402
from drafter.revision import engine as E  # noqa: E402


def server_problem(attempt):
    response = attempt['response']
    if response is None:
        return None
    if response.get('finish_reason') != 'stop':
        return f"finish_reason {response.get('finish_reason')!r}"
    if response.get('model') not in attempt['settings'].get('accepted_models', []):
        return f"answered as model {response.get('model')!r}"
    return None


class Capture(L._Backend):
    backend = 'capture'
    name = 'capture'

    def __init__(self):
        self.sent = None

    def call(self, system, user):
        self.sent = (system, user)
        return '{"findings": []}', None


def production_prompt(critic_request):
    capture = Capture()
    CR.review(deepcopy(critic_request), capture)
    if capture.sent is None:
        raise ValueError('the Critic did not call the model; the request is not reviewable')
    return capture.sent


def qwen_results(responses, allow_scripted=False):
    summary, system, requests = CM.RB.load_batch(HERE / 'batch_stage1')
    if summary['system_sha256'] != CM.sha256_text(CM.PROMPT_PATH.read_text(encoding='utf-8')):
        raise ValueError('batch_stage1 does not use the frozen revision prompt')
    if len(requests) != CM.REPEATS * len(CM.CASES):
        raise ValueError(f'batch_stage1 must have {CM.REPEATS * len(CM.CASES)} requests, has {len(requests)}')
    by_state = {s.case_id: s for s in CM.states()}
    chosen = CM.checked_attempts(responses, requests, system, allow_scripted)
    out = {}
    for request in requests:
        record = {'method': 'qwen', 'run_id': request['run_id'], 'case_id': request['case_id'],
                  'repeat': request['repeat'], 'attempts': 0, 'status': None, 'status_detail': None,
                  'user_sha256': request['user_sha256'], 'system_sha256': request['system_sha256'],
                  'revision_request_sha256': request['revision_request_sha256'], 'input_sha256': None,
                  'reply_sha256': None, 'backend': None, 'model_revision': None, 'response': None,
                  'permitted_information_sha256': None, 'result': None}
        attempt, count = chosen[request['run_id']]
        if attempt is None:
            record['status'] = 'missing'
        else:
            record.update(attempts=count, reply_sha256=attempt['reply_sha256'], input_sha256=attempt['input_sha256'],
                          backend=attempt['backend'], model_revision=attempt.get('model_revision'),
                          response=attempt['response'])
            problem = server_problem(attempt) if attempt['reply'] is not None else None
            if attempt['reply'] is None:
                record.update(status='no_reply', status_detail=attempt['error'])
            elif problem:
                record.update(status='invalid_server_reply', status_detail=problem)
            else:
                result, info = by_state[request['case_id']].revise(
                    CM.RecordedQwenAdapter(attempt['reply'], request['user_sha256']))
                if info != request['permitted_information_sha256']:
                    raise ValueError(request['run_id'] + ': permitted information changed since stage 1')
                record.update(status=CM.classify_output(result), permitted_information_sha256=info, result=result)
        out[request['run_id']] = record
    return out


def build(responses, allow_scripted=False):
    """{relative path: text} for the Qwen results and the second Critic batch. allow_scripted is for tests."""
    files, lines = {}, []
    qwen = qwen_results(responses, allow_scripted)
    if sorted(qwen) != sorted(f"{c['case_id']}:Q:r{n}" for c in CM.CASES for n in range(1, CM.REPEATS + 1)):
        raise ValueError('the Qwen outputs do not cover exactly the expected requests')
    for run_id, record in qwen.items():
        files[f"results/qwen/{run_id.replace(':', '_')}.revision_result.json"] = CM.dumps(record)
    targets = []
    for state in CM.states():
        cid = state.case_id
        targets.append((f'{cid}:original', cid, 'original', state.critic_request, CM.STAGE2_REPEATS))
        template = CM.load_json(HERE / 'results' / 'template' / f'{cid}.revision_result.json')['result']
        if template['outcome'] == 'revised':
            targets.append((f'{cid}:template', cid, 'template', E.recriticism_request(state.request, template),
                            CM.STAGE2_REPEATS))
        for run_id, record in qwen.items():
            if record['case_id'] == cid and record['status'] == 'revised':
                targets.append((run_id, cid, 'qwen', E.recriticism_request(state.request, record['result']), 1))
    systems = set()
    for target_id, cid, kind, critic_request, repeats in targets:
        system, user = production_prompt(critic_request)
        systems.add(system)
        files[f"stage2_requests/{target_id.replace(':', '_')}.critic_request.json"] = CM.dumps(critic_request)
        for repeat in range(1, repeats + 1):
            lines.append(json.dumps({
                'run_id': f'S2:{target_id}:r{repeat}', 'case_id': cid, 'condition': kind, 'repeat': repeat,
                'target_id': target_id, 'critic_request_sha256': K.digest(critic_request),
                'system_sha256': CM.sha256_text(system), 'user_sha256': CM.sha256_text(user), 'user': user},
                ensure_ascii=False))
    if len(systems) != 1:
        raise ValueError('the second Critic must use one system prompt')
    system = systems.pop()
    if CM.sha256_text(system) != CM.sha256_text(L.PROMPT_PATH.read_text(encoding='utf-8')):
        raise ValueError('the second Critic does not use the frozen Critic prompt')
    text = '\n'.join(lines) + '\n'
    files['batch_stage2/requests.jsonl'] = text
    files['batch_stage2/system_prompt.txt'] = system
    files['batch_stage2/BATCH.json'] = json.dumps({
        'batch_version': CM.EXPERIMENT_VERSION + ':stage2', 'experiment': CM.EXPERIMENT_VERSION,
        'what': 'production Critic review of original and revised arguments',
        'prompt_version': L.PROMPT_VERSION, 'system_sha256': CM.sha256_text(system), 'requests': len(lines),
        'targets': len(targets), 'requests_sha256': CM.sha256_text(text), 'data_role': 'development_only',
        'settings': CM.RQ3_SETTINGS.SETTINGS}, indent=1) + '\n'
    return files


def main(argv=None):
    p = argparse.ArgumentParser(prog='build_stage2.py')
    p.add_argument('--responses', required=True, nargs='+', help='stage 1 JSONL written by run_batch.py')
    p.add_argument('--check', action='store_true')
    args = p.parse_args(argv)
    responses = [line for path in args.responses for line in CM.RB.read_jsonl(path)]
    try:
        files = build(responses)
    except ValueError as exc:
        print(f'stage 2 cannot be built: {exc}', file=sys.stderr)
        return 1
    targets = {HERE / n: t for n, t in files.items()}
    if args.check:
        stale = CM.stale_files(targets)
        print('differs from a fresh build: ' + ', '.join(stale) if stale else 'stage 2 matches a fresh build')
        return 1 if stale else 0
    try:
        CM.write_files(targets)  # saved Qwen results and the second Critic batch are never changed
    except CM.ProtectedFileError as exc:
        print(exc, file=sys.stderr)
        return 1
    summary = json.loads(files['batch_stage2/BATCH.json'])
    statuses = {}
    for name, text in files.items():
        if name.startswith('results/qwen/'):
            s = json.loads(text)['status']
            statuses[s] = statuses.get(s, 0) + 1
    print(f"Qwen outputs: {statuses}; second Critic batch: {summary['requests']} requests on {summary['targets']} arguments",
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
