"""Validate a Drafter fixture; this command performs no inference."""
import argparse
import json
from .validation import ContractError, read_json, validate_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-request', required=True, metavar='JSON')
    args = parser.parse_args()
    try:
        report = validate_request(read_json(args.validate_request))
    except (ContractError, ValueError, TypeError, OSError) as error:
        report = {'contract_status': 'rejected', 'model_called': False,
                  'diagnostics': getattr(error, 'issues', [str(error)])}
        print(json.dumps(report, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
