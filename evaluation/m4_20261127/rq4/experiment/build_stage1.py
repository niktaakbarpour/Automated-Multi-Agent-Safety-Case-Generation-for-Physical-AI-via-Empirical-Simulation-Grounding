"""Build everything fixed before any revision output exists (RQ4 stage 1). CPU only, no model.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/build_stage1.py          write
    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/build_stage1.py --check  compare with a fresh build

Writes, under rq4/experiment/:
  cases/<case>.critic_report.json       the real Critic report for the planted defect
  cases/<case>.revision_request.json    with the approved finding (fixed rule) and every other finding untouched
  results/template/<case>.revision_result.json   the template adapter's revision (no GPU needed)
  batch_stage1/                         the Qwen revision batch for run_batch.py (rq3/experiment)
  ../CASE_MANIFEST.csv                  one row per case
"""
from pathlib import Path
import csv
import io
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM  # noqa: E402
from critic import contract as K  # noqa: E402
from critic.critic import CRITIC_VERSION  # noqa: E402
from drafter.revision import adapters as A  # noqa: E402

MANIFEST_COLUMNS = ('case_id', 'parent_group_id', 'defect_type', 'target_object', 'target_node', 'target_node_type',
                    'finding_source', 'finding_check_id', 'finding_category', 'report_source', 'rq3_run_id',
                    'other_findings_carried_forward', 'critic_request_sha256', 'critic_report_sha256',
                    'revision_request_sha256', 'permitted_information_sha256')


def build():
    files, lines, rows, systems = {}, [], [], set()
    system = CM.PROMPT_PATH.read_text(encoding='utf-8')
    for state in CM.states():
        cid = state.case_id
        approved = state.decisions[0]['criticism_id']
        finding = next(c for c in state.report['criticisms'] if c['criticism_id'] == approved)
        template, info_t = state.revise(A.DeterministicAdapter())
        user, info_q = state.qwen_prompt()
        if info_t != info_q:
            raise ValueError(cid + ': the two methods would not get the same permitted information')
        files[f'cases/{cid}.critic_report.json'] = CM.dumps(state.report)
        files[f'cases/{cid}.revision_request.json'] = CM.dumps(state.request)
        files[f'results/template/{cid}.revision_result.json'] = CM.dumps(
            {'method': 'template', 'case_id': cid, 'permitted_information_sha256': info_t, 'result': template})
        for repeat in range(1, CM.REPEATS + 1):
            lines.append(json.dumps({
                'run_id': f'{cid}:Q:r{repeat}', 'case_id': cid, 'condition': 'Q', 'repeat': repeat,
                'case_request_sha256': K.digest(state.critic_request),
                'revision_request_sha256': K.digest(state.request), 'permitted_information_sha256': info_q,
                'system_sha256': CM.sha256_text(system), 'user_sha256': CM.sha256_text(user), 'user': user},
                ensure_ascii=False))
        node = next(n for g in state.critic_request['argument_bundle']['graphs'] if g['object_id'] == finding['object_id']
                    for n in g['graph']['nodes'] if n['id'] == finding['node_id'])
        rows.append({'case_id': cid, 'parent_group_id': state.label['parent_group_id'],
                     'defect_type': state.label['mutation_operator'], 'target_object': finding['object_id'],
                     'target_node': finding['node_id'], 'target_node_type': node['type'],
                     'finding_source': finding['finding_source'], 'finding_check_id': finding['check_id'],
                     'finding_category': finding['category'], 'report_source': state.case['report_source'],
                     'rq3_run_id': state.case['rq3_run_id'] or '',
                     'other_findings_carried_forward': len(state.report['criticisms']) - 1,
                     'critic_request_sha256': K.digest(state.critic_request),
                     'critic_report_sha256': K.digest(state.report), 'revision_request_sha256': K.digest(state.request),
                     'permitted_information_sha256': info_q})
    requests_text = '\n'.join(lines) + '\n'
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=MANIFEST_COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    summary = {
        'batch_version': CM.EXPERIMENT_VERSION + ':stage1', 'experiment': CM.EXPERIMENT_VERSION,
        'what': 'Qwen revision proposals for the approved planted-defect findings',
        'critic_version': CRITIC_VERSION, 'prompt_version': CM.PROMPT_VERSION,
        'system_sha256': CM.sha256_text(system), 'conditions': ['Q'], 'repeats': CM.REPEATS,
        'cases': len(rows), 'requests': len(lines),
        'canonical_source_groups': len({r['parent_group_id'] for r in rows}), 'independent_cases': 0,
        'data_role': 'development_only', 'requests_sha256': CM.sha256_text(requests_text),
        'settings': CM.RQ3_SETTINGS.SETTINGS,
    }
    files['batch_stage1/requests.jsonl'] = requests_text
    files['batch_stage1/system_prompt.txt'] = system
    files['batch_stage1/BATCH.json'] = json.dumps(summary, indent=1) + '\n'
    files['../CASE_MANIFEST.csv'] = out.getvalue()
    return files


def main(argv):
    files = build()
    if argv == ['--check']:
        stale = [n for n, t in files.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding='utf-8') != t]
        print('differs from a fresh build: ' + ', '.join(stale) if stale else
              f'stage 1 matches a fresh build ({json.loads(files["batch_stage1/BATCH.json"])["requests"]} requests)')
        return 1 if stale else 0
    if argv:
        print(__doc__)
        return 2
    for name, text in files.items():
        path = (HERE / name).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        print('wrote', path.relative_to(CM.ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
