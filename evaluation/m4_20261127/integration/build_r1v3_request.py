"""Build the Drafter R1 v3 request (drafter-request/0.2.0) for the original execution.

    python3 -m evaluation.m4_20261127.integration.build_r1v3_request          # write the request
    python3 -m evaluation.m4_20261127.integration.build_r1v3_request --check  # confirm the committed file

The request carries ORIGINAL_EXECUTION_EVIDENCE_PACKAGE.json unchanged and is fully derived from it and the frozen
R1 v3 files, so rebuilding it gives the same bytes. Generation (GPU):

    python -m drafter --generate evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json \\
        --model-config <frozen local model config> --out <run report .json> \\
        --argument-out <argument .json> --review-out <review .md>
"""
import argparse
import json
from pathlib import Path
import sys

from drafter import r1v3_profile as P

HERE = Path(__file__).resolve().parent
PACKAGE = HERE / 'ORIGINAL_EXECUTION_EVIDENCE_PACKAGE.json'
REQUEST = HERE / 'DRAFTER_R1V3_REQUEST.json'
REQUEST_ID = 'm4-e2e-original-r1v3'


def build():
    request = P.build_request(json.loads(PACKAGE.read_text(encoding='utf-8')), request_id=REQUEST_ID)
    P.validate_request(request)
    return json.dumps(request, indent=2, ensure_ascii=False) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true', help='fail if the committed request differs from a rebuild')
    args = parser.parse_args(argv)
    text = build()
    if args.check:
        if not REQUEST.exists() or REQUEST.read_text(encoding='utf-8') != text:
            print('DRAFTER_R1V3_REQUEST.json differs from a rebuild', file=sys.stderr)
            return 1
        print('DRAFTER_R1V3_REQUEST.json matches a rebuild')
        return 0
    REQUEST.write_text(text, encoding='utf-8')
    print('wrote', REQUEST.relative_to(HERE.parents[2]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
