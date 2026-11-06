"""Validate a fixture, check a model, generate a draft, or run an explicit mock."""
import argparse
import json
from pathlib import Path
from .validation import ContractError, read_json, validate_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--validate-request', metavar='JSON')
    actions.add_argument('--check-model', action='store_true')
    actions.add_argument('--smoke-test-model', action='store_true')
    actions.add_argument('--generate', metavar='JSON', help='Generate a GSN draft from a validated fixture request.')
    actions.add_argument('--mock-demo', metavar='JSON', help='Run the deployment-blocked mock without a model or network.')
    actions.add_argument('--adapt-phase5', metavar='JSON', help='Prepare a validated Drafter request from saved Phase 5 adapter inputs; no model or database call.')
    actions.add_argument('--prepare-registry', metavar='JSON', help='Prepare a configurable request from supplied R1 configuration and original registry records.')
    parser.add_argument('--model-config', metavar='JSON')
    parser.add_argument('--out', metavar='JSON', help='Write a new report file; never overwrite an existing file.')
    parser.add_argument('--argument-out', metavar='JSON', help='Save the live draft or mock envelope separately.')
    parser.add_argument('--review-out', metavar='MD', help='Save a readable live or mock review copy.')
    args = parser.parse_args()
    if (args.check_model or args.smoke_test_model or args.generate) and not args.model_config:
        parser.error('--model-config is required for a model operation')
    if (args.validate_request or args.mock_demo or args.adapt_phase5 or args.prepare_registry) and args.model_config:
        parser.error('--model-config is only used by model operations')
    if (args.argument_out or args.review_out) and not (args.generate or args.mock_demo):
        parser.error('--argument-out and --review-out require --generate or --mock-demo')
    if (args.generate or args.mock_demo) and not args.out:
        parser.error('--out is required with --generate or --mock-demo to preserve the run record')
    try:
        destinations = [Path(p) for p in (args.out, args.argument_out, args.review_out) if p]
        if len({p.resolve() for p in destinations}) != len(destinations):
            raise ValueError('Report, argument and review paths must be different.')
        for path in destinations:
            if path.exists():
                raise FileExistsError('Output file already exists; choose a new report path.')
            if (args.generate or args.mock_demo) and not path.parent.is_dir():
                raise FileNotFoundError('Create the output folder before running a model operation.')
        if args.adapt_phase5 or args.prepare_registry:
            if args.adapt_phase5:
                from .phase5_adapter import adapt_phase5_request as prepare
            else:
                from .request_profiles import build_supplied_request as prepare
            report = prepare(**read_json(args.adapt_phase5 or args.prepare_registry))
            success = True
        elif args.validate_request:
            report = validate_request(read_json(args.validate_request))
            success = True
        elif args.mock_demo:
            from .mock_demo import run_mock_demo
            report = run_mock_demo(read_json(args.mock_demo))
            success = report['status'] == 'mock_demonstration'
        elif args.generate:
            from .generation import generate_argument
            from .llm import load_local_model_config
            report = generate_argument(read_json(args.generate), load_local_model_config(args.model_config))
            success = report['status'] == 'accepted'
        else:
            from .connection import check_connection
            from .llm import load_local_model_config
            report = check_connection(load_local_model_config(args.model_config), args.smoke_test_model)
            success = report['status'] in ('ready', 'passed')
    except (ContractError, ValueError, TypeError, OSError, RecursionError) as error:
        report = {'contract_status': 'rejected', 'model_called': False,
                  'diagnostics': getattr(error, 'issues', [str(error)])}
        success = False
    if args.out:
        from evaluation.r1_v4.provenance import canonical
        try:
            with Path(args.out).open('xb') as stream:
                stream.write(canonical(report) + b'\n')
            if args.argument_out and report.get('argument') is not None:
                with Path(args.argument_out).open('xb') as stream:
                    stream.write(canonical(report['argument']) + b'\n')
            if args.review_out:
                from .generation import render_review
                with Path(args.review_out).open('x', encoding='utf-8') as stream:
                    stream.write(render_review(report))
        except OSError as error:
            report['output_write_error'] = {'code': 'report_not_saved', 'message': str(error)}
            print(json.dumps(report, indent=2))
            return 1
    print(json.dumps(report, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
