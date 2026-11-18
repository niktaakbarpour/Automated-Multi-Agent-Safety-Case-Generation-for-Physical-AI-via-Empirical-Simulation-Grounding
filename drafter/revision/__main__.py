"""Command line: python3 -m drafter.revision COMMAND ...   (CPU only, no model, no network)

  build-request  wrap a Critic request and its report into a revision request
  revise         run one revision round on a revision request
  verify         replay a saved result against its request
  cycle          revise, re-criticise and repeat until a stop reason

Examples, from the repository root
  python3 -m drafter.revision revise \
      --request drafter/revision/examples/synthetic_actionable.revision_request.json \
      --out /tmp/result.json --out-bundle /tmp/revised_bundle.json --out-diff /tmp/diff.json
  python3 -m drafter.revision verify \
      --request drafter/revision/examples/synthetic_actionable.revision_request.json \
      --result drafter/revision/examples/synthetic_actionable.revision_result.json
  python3 -m drafter.revision cycle \
      --request drafter/revision/examples/synthetic_actionable.revision_request.json --out-dir /tmp/cycle

Exit codes
  0  revise/cycle: revised or no change; verify: the result holds; build-request: written
  1  revise/cycle: unresolved, nothing was changed; verify: the result does not hold
  2  bad command line (argparse)
  3  the request is not usable (see request_issues), or build-request found issues
  5  the adapter or the module failed; nothing was applied
  6  a file could not be read as JSON
"""
import argparse
import json
import sys
from pathlib import Path

from . import contract as C, engine as G

EXIT = {'revised': 0, 'no_change': 0, 'unresolved': 1, 'rejected_invalid_input': 3, 'failed': 5}
EXIT_UNREADABLE = 6


class Unreadable(Exception):
    pass


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise Unreadable(f'cannot read {path}: {error}')


def _write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                          encoding='utf-8')


def _line(result):
    m = result['metrics']
    return (f"round {result['round']}: {result['outcome']}, stop_reason={result['stop_reason']}, "
            f"edits={m['edits_applied']}, findings addressed {m['findings_addressed']}/{m['findings_total']}. "
            f"{result['status_detail']}")


def build_request(args):
    try:
        request = C.build_request(
            args.revision_id, _read(args.critic_request), _read(args.critic_report),
            finding_decisions=_read(args.decisions) if args.decisions else (),
            synthetic_label=args.synthetic_label, max_rounds=args.max_rounds,
            repair_invalid_evidence_links=args.repair_evidence_links)
    except ValueError as error:
        print('revision request not usable: ' + str(error), file=sys.stderr)
        return 3
    if args.out:
        _write(args.out, request)
        print(f'{args.out}: revision request written', file=sys.stderr)
    else:
        sys.stdout.write(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
    return 0


def revise(args):
    request = _read(args.request)
    result = G.revise(request)
    if args.out:
        _write(args.out, result)
        print(f'{args.out}: {_line(result)}', file=sys.stderr)
    else:
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    if result['outcome'] == 'revised':
        if args.out_bundle:
            _write(args.out_bundle, result['revised_argument_bundle'])
        if args.out_recriticism_request:
            _write(args.out_recriticism_request, G.recriticism_request(request, result))
    if args.out_diff:
        _write(args.out_diff, {'edits': result['edits'], 'diff': result['diff'],
                               'dispositions': result['dispositions']})
    return EXIT[result['outcome']]


def verify(args):
    issues = G.verify_result(_read(args.request), _read(args.result))
    print('the result holds: replaying its proposal on the request gives the same result' if not issues
          else 'the result does not hold: ' + '; '.join(issues))
    return 1 if issues else 0


def cycle(args):
    import critic
    from critic import llm as L
    request = _read(args.request)
    replies = [Path(p).read_text(encoding='utf-8') for p in args.scripted_reply]

    def review(critic_request):
        return critic.review(critic_request, L.ScriptedLLM(replies.pop(0)) if replies else None)

    def decide(report, round_number):
        return [{'criticism_id': c['criticism_id'], 'decision': 'approved',
                 'decided_by': 'synthetic_test_label', 'reviewer': None,
                 'note': 'Approved only as a labelled synthetic test input.'}
                for c in report['criticisms']
                if c['phase'] == 'review' and (c['finding_source'] != 'deterministic'
                                               or c['human_review_required'])]

    run = G.run_cycle(request, review=review, decide=decide if args.approve_as_synthetic_test else None)
    out = Path(args.out_dir)
    for index, (req, result) in enumerate(zip(run['requests'], run['results']), start=1):
        _write(out / f'request_{index}.revision_request.json', req)
        _write(out / f'request_{index}.revision_result.json', result)
        if index <= len(run['reports']):
            _write(out / f'request_{index}.recriticism_request.json', G.recriticism_request(req, result))
            _write(out / f'request_{index}.recriticism_report.json', run['reports'][index - 1])
        print(_line(result), file=sys.stderr)
    revised = [r for r in run['results'] if r['outcome'] == 'revised']
    if revised:
        _write(out / 'final_argument_bundle.json', revised[-1]['revised_argument_bundle'])
    _write(out / 'cycle.json', run['cycle'])
    summary = run['cycle']
    print(f"{out / 'cycle.json'}: {summary['revision_rounds']} revision round(s), "
          f"stop_reason={summary['stop_reason']}, final_outcome={summary['final_outcome']}", file=sys.stderr)
    return EXIT[summary['final_outcome']]


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python3 -m drafter.revision',
                                     description='Bounded GSN revision from a Critic report.')
    commands = parser.add_subparsers(dest='command', required=True)

    p = commands.add_parser('build-request', help='wrap a Critic request and report into a revision request')
    p.add_argument('--critic-request', required=True, help='the critic-request/0.3.0 file that was reviewed')
    p.add_argument('--critic-report', required=True, help='the critic-report/0.4.0 file returned for it')
    p.add_argument('--revision-id', required=True)
    p.add_argument('--decisions', help='JSON file with a list of finding decisions')
    p.add_argument('--synthetic-label', help='required when the report comes from a scripted reply')
    p.add_argument('--max-rounds', type=int, default=2)
    p.add_argument('--repair-evidence-links', action='store_true',
                   help='allow removal of broken Solution citations when they are the only input problem')
    p.add_argument('--out', help='write the request here instead of stdout')
    p.set_defaults(run=build_request)

    p = commands.add_parser('revise', help='run one revision round')
    p.add_argument('--request', required=True, help='revision request JSON file')
    p.add_argument('--out', help='write the result here instead of stdout')
    p.add_argument('--out-bundle', help='also write the revised argument bundle (only when revised)')
    p.add_argument('--out-recriticism-request', help='also write the Critic request for the revised bundle')
    p.add_argument('--out-diff', help='also write the edits, the node-level diff and the dispositions')
    p.set_defaults(run=revise)

    p = commands.add_parser('verify', help='replay a saved result against its request')
    p.add_argument('--request', required=True)
    p.add_argument('--result', required=True)
    p.set_defaults(run=verify)

    p = commands.add_parser('cycle', help='revise, re-criticise with the Critic rules, repeat until a stop')
    p.add_argument('--request', required=True, help='round-1 revision request JSON file')
    p.add_argument('--out-dir', required=True, help='directory for every request, result, report and cycle.json')
    p.add_argument('--scripted-reply', action='append', default=[], metavar='FILE',
                   help='fixed Critic model reply for the next re-criticism, in order; repeatable. For '
                        'synthetic demonstrations only. Without it the re-criticism uses the Critic rules only')
    p.add_argument('--approve-as-synthetic-test', action='store_true',
                   help='approve later findings that need a decision with a synthetic_test_label decision. '
                        'Allowed only when the request carries the synthetic label; never a scientific approval')
    p.set_defaults(run=cycle)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except Unreadable as error:
        print(str(error), file=sys.stderr)
        return EXIT_UNREADABLE


if __name__ == '__main__':
    raise SystemExit(main())
