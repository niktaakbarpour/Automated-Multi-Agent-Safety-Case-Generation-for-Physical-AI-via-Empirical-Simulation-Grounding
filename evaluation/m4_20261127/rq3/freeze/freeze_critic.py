"""Freeze, or check, the Critic rule and prompt bundle used for RQ3 (M4 task A3). CPU only.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/freeze/freeze_critic.py --write   record the bundle
    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/freeze/freeze_critic.py           check it, exit 1 on any change

The bundle is every code, prompt, schema and case file under critic/ (not tests, examples, caches, or the README
and audit reports directly in critic/), plus the versions the
Critic reports. Any RQ3 model run must use a Critic that passes the check, and the check must be run before any
held-out model answer is inspected.
"""
import hashlib
import json
import sys
from pathlib import Path

import critic
from critic import claims, contract as K, llm as L

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).with_name('CRITIC_FREEZE.json')
SKIP = ('critic/tests/', 'critic/examples/', '__pycache__')


def bundle():
    files = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'critic').rglob('*')
                   if p.is_file() and not any(s in p.relative_to(ROOT).as_posix() for s in SKIP)
                   and p.suffix in ('.py', '.md', '.json', '.txt')
                   and not (p.suffix == '.md' and p.parent == ROOT / 'critic'))
    return {
        'critic_version': critic.CRITIC_VERSION, 'rule_version': claims.RULE_VERSION,
        'prompt_version': L.PROMPT_VERSION,
        'prompt_sha256': hashlib.sha256(L.PROMPT_PATH.read_bytes()).hexdigest(),
        'request_schema_version': K.REQUEST_SCHEMA_VERSION, 'report_schema_version': K.REPORT_SCHEMA_VERSION,
        'files': {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files},
    }


def main(argv):
    current = bundle()
    if argv == ['--write']:
        OUT.write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
        print(f'wrote {OUT.relative_to(ROOT)}: {len(current["files"])} files, Critic {current["critic_version"]}')
        return 0
    if argv:
        print(__doc__)
        return 2
    frozen = json.loads(OUT.read_text(encoding='utf-8'))
    changed = sorted(k for k in set(frozen) | set(current) if k != 'files' and frozen.get(k) != current.get(k))
    files = sorted(f for f in set(frozen['files']) | set(current['files'])
                   if frozen['files'].get(f) != current['files'].get(f))
    if changed or files:
        print('the Critic differs from the frozen bundle:', ', '.join(changed + files))
        return 1
    print(f'the Critic matches the frozen bundle ({len(frozen["files"])} files, '
          f'Critic {frozen["critic_version"]}, rule {frozen["rule_version"]}, prompt {frozen["prompt_version"]})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
