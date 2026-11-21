"""Build the matched RQ3 batch: every semantic case x T/R/C x repeat (M4 task A3). CPU only, no model.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/build_batch.py          write the batch
    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/build_batch.py --check  compare with a fresh build

Writes experiment/batch/requests.jsonl (one model request per line), experiment/batch/system_prompt.txt,
experiment/batch/BATCH.json and rq3/MATCHED_RUN_MANIFEST.csv. No label, case type or rule-based finding is in a
model request: the batch is built from the case files alone, and the stratum is read only to leave out the
validation-stratum cases, which never reach a model.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys

from critic import contract as K, llm as L
from critic.critic import CRITIC_VERSION

HERE = Path(__file__).resolve().parent
RQ3 = HERE.parent
ROOT = RQ3.parents[2]
sys.path.insert(0, str(HERE))
import conditions as CND  # noqa: E402
import settings as S  # noqa: E402

BATCH_DIR = HERE / 'batch'
MANIFEST = RQ3 / 'MATCHED_RUN_MANIFEST.csv'
COLUMNS = ('run_id', 'case_id', 'condition', 'repeat', 'parent_group_id', 'c_availability', 'case_request_sha256',
           'system_sha256', 'user_sha256', 'user_chars')


def cases():
    """[(case_id, parent_group_id, request)] for the semantic stratum, in manifest order."""
    with open(RQ3 / 'MUTATION_MANIFEST.csv', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        if row['stratum'] != 'semantic':
            continue
        request = json.loads((ROOT / row['case_file']).read_text(encoding='utf-8'))
        if K.digest(request) != row['request_sha256']:
            raise ValueError(row['case_id'] + ': case file does not match MUTATION_MANIFEST.csv')
        out.append((row['case_id'], row['parent_group_id'], request))
    return out


def build(repeats=S.REPEATS):
    """{relative path: text} for every file this script writes."""
    lines, rows, systems = [], [], set()
    for case_id, group, request in cases():
        system, users, meta = CND.build(request)
        systems.add(system)
        for condition in CND.CONDITIONS:
            for repeat in range(1, repeats + 1):
                run_id = f'{case_id}:{condition}:r{repeat}'
                user = users[condition]
                line = {'run_id': run_id, 'case_id': case_id, 'condition': condition, 'repeat': repeat,
                        'c_availability': meta['c_availability'], 'case_request_sha256': K.digest(request),
                        'system_sha256': CND.sha256_text(system), 'user_sha256': CND.sha256_text(user),
                        'user': user}
                lines.append(json.dumps(line, ensure_ascii=False))
                rows.append({**{k: line[k] for k in COLUMNS if k in line}, 'parent_group_id': group,
                             'user_chars': len(user)})
    if len(systems) != 1:
        raise ValueError('the system prompt must be the same for every request')
    system = systems.pop()
    requests_text = '\n'.join(lines) + '\n'
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    groups = sorted({r['parent_group_id'] for r in rows})
    summary = {
        'batch_version': S.BATCH_VERSION, 'benchmark': json.loads((RQ3 / 'mutations' / 'BENCHMARK.json')
                                                                  .read_text())['benchmark_version'],
        'critic_version': CRITIC_VERSION, 'prompt_version': L.PROMPT_VERSION,
        'prompt_sha256': hashlib.sha256(L.PROMPT_PATH.read_bytes()).hexdigest(),
        'system_sha256': CND.sha256_text(system), 'conditions': list(CND.CONDITIONS), 'repeats': repeats,
        'cases': len(rows) // (len(CND.CONDITIONS) * repeats), 'requests': len(rows),
        'canonical_source_groups': len(groups), 'independent_cases': 0, 'data_role': 'development_only',
        'model_sees_rule_findings': False,
        'c_availability': sorted({r['c_availability'] for r in rows}),
        'requests_sha256': CND.sha256_text(requests_text),
        'settings': S.SETTINGS,
    }
    return {'batch/requests.jsonl': requests_text, 'batch/system_prompt.txt': system,
            'batch/BATCH.json': json.dumps(summary, indent=1) + '\n', '../MATCHED_RUN_MANIFEST.csv': out.getvalue()}


def main(argv):
    files = build()
    if argv == ['--check']:
        stale = [n for n, text in files.items()
                 if not (HERE / n).exists() or (HERE / n).read_text(encoding='utf-8') != text]
        if stale:
            print('differs from a fresh build:', ', '.join(stale))
            return 1
        print(f'the saved batch matches a fresh build ({json.loads(files["batch/BATCH.json"])["requests"]} requests)')
        return 0
    if argv:
        print(__doc__)
        return 2
    BATCH_DIR.mkdir(exist_ok=True)
    for name, text in files.items():
        path = (HERE / name).resolve()
        path.write_text(text, encoding='utf-8')
        print('wrote', path.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
