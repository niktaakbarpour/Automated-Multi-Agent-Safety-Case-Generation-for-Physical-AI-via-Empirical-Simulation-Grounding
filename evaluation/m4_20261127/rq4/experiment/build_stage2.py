"""Apply the Qwen revisions and build the second Critic batch (RQ4 stage 2). CPU only, no model.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/build_stage2.py --responses STAGE1_RESPONSES.jsonl
    (add --check to compare with the saved files)

For every Qwen request it takes the first attempt with a server reply (as in RQ3), refuses a reply that did not
finish normally or names another model, and otherwise replays it through the revision engine with the same
permitted information the template got. Results go to results/qwen/.

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


def first_reply(attempts):
    with_reply = [a for a in attempts if a['reply'] is not None]
    return (with_reply[0] if with_reply else attempts[-1]), len(attempts)


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


def qwen_results(responses):
    _, _, requests = CM.RB.load_batch(HERE / 'batch_stage1')
    by_state = {s.case_id: s for s in CM.states()}
    attempts = {}
    for line in responses:
        attempts.setdefault(line['run_id'], []).append(line)
    out = {}
    for request in requests:
        record = {'method': 'qwen', 'run_id': request['run_id'], 'case_id': request['case_id'],
                  'repeat': request['repeat'], 'attempts': 0, 'status': None, 'status_detail': None,
                  'reply_sha256': None, 'permitted_information_sha256': None, 'result': None}
        if request['run_id'] not in attempts:
            record['status'] = 'missing'
        else:
            attempt, count = first_reply(attempts[request['run_id']])
            if attempt['user_sha256'] != request['user_sha256'] or attempt['system_sha256'] != request['system_sha256']:
                raise ValueError(request['run_id'] + ': the response was made for a different request')
            record.update(attempts=count, reply_sha256=attempt['reply_sha256'])
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


def build(responses):
    files, lines = {}, []
    qwen = qwen_results(responses)
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
    files = build(responses)
    if args.check:
        stale = [n for n, t in files.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding='utf-8') != t]
        print('differs from a fresh build: ' + ', '.join(stale) if stale else 'stage 2 matches a fresh build')
        return 1 if stale else 0
    for name, text in files.items():
        path = HERE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
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
