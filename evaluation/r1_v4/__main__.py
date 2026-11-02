"""python -m evaluation.r1_v4 --input synthetic-bundle.json --output NEW.json"""
import argparse
import sys
from .provenance import load, write_new
from .runtime import assess


def main(argv=None):
    parser = argparse.ArgumentParser(description='R1 V4 synthetic analytical infrastructure; empirical admission disabled')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        result = assess(load(args.input))
        write_new(args.output, result)
    except (OSError, ValueError, TypeError) as e:
        print('input/output error: ' + str(e), file=sys.stderr)
        return 2
    return 0 if result['configuration_status'] == 'valid' and not result.get('missing_requirements') else 1


if __name__ == '__main__':
    raise SystemExit(main())
