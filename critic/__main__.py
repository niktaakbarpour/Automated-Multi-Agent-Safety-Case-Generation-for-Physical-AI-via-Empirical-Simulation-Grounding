"""Command line: python3 -m critic --request FILE [--backend none|openai] [--model NAME]

Examples
  python3 -m critic --request critic/cases/case_a_unsupported_claim.json
  python3 -m critic --request critic/cases/case_a_unsupported_claim.json \
      --backend openai --base-url http://localhost:8000/v1 --model openai/gpt-oss-20b

Exit codes (the report is written in every case)
  0  review completed, no blocking criticism
  1  review completed, with blocking criticisms
  2  bad command line (argparse)
  3  input rejected: it failed validation, so no review was run (review_status rejected_invalid_input)
  4  rule-based review completed but the LLM step failed (completed_llm_failed)
  5  internal error: the report failed its own schema
  6  the request file could not be read as JSON
"""
import argparse
import json
import sys

EXIT_CODES = {'completed': 0, 'rejected_invalid_input': 3, 'completed_llm_failed': 4, 'internal_error': 5}
EXIT_BLOCKING, EXIT_UNREADABLE = 1, 6


def exit_code(report):
    if report['review_status'] == 'completed' and report['summary']['blocking_defects']:
        return EXIT_BLOCKING
    return EXIT_CODES[report['review_status']]

from . import llm as L
from .critic import review


def make_llm(args):
    if args.backend == 'none':
        return L.NullLLM()
    if args.backend == 'scripted':
        with open(args.scripted_reply, encoding='utf-8') as fh:
            return L.ScriptedLLM(fh.read())
    extra = {'response_format': {'type': 'json_object'}} if args.json_mode else {}
    return L.OpenAICompatibleLLM(base_url=args.base_url, model=args.model, temperature=args.temperature,
                                 max_tokens=args.max_tokens, extra_body=extra, accepted_models=args.accept_model)


def main(argv=None):
    p = argparse.ArgumentParser(prog='python3 -m critic', description='Review one R1 argument bundle.')
    p.add_argument('--request', required=True,
                   help='review request JSON file for R1 v2 or R1 v3')
    p.add_argument('--backend', choices=['none', 'openai', 'scripted'], default='none',
                   help='none = rule checks only (including R1 v3); openai = an OpenAI-compatible server for R1 v2')
    p.add_argument('--base-url', default=None, help='default $CRITIC_LLM_BASE_URL or http://localhost:8000/v1')
    p.add_argument('--model', default=None, help='default $CRITIC_LLM_MODEL')
    p.add_argument('--temperature', type=float, default=None,
                   help="default: the model card's setting (see llm.MODEL_PRESETS)")
    p.add_argument('--max-tokens', type=int, default=8192)
    p.add_argument('--json-mode', action='store_true', help='ask the server for response_format=json_object')
    p.add_argument('--accept-model', action='append', default=[], metavar='NAME',
                   help='another model name the server may answer as (e.g. its served-model-name); repeatable. '
                        'By default the reply must name the requested model')
    p.add_argument('--scripted-reply', help='file with a fixed model reply (used with --backend scripted)')
    p.add_argument('--out', help='write the report here instead of stdout')
    args = p.parse_args(argv)
    if args.backend == 'scripted' and not args.scripted_reply:
        p.error('--backend scripted needs --scripted-reply FILE')
    try:
        with open(args.request, encoding='utf-8') as fh:
            request = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f'cannot read {args.request}: {exc}', file=sys.stderr)
        return EXIT_UNREADABLE
    try:
        backend = make_llm(args)
    except ValueError as exc:
        p.error(str(exc))
    report = review(request, backend)
    text = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fh:
            fh.write(text)
        s = report['summary']
        print(f"{args.out}: {report['review_status']}, {len(report['criticisms'])} criticisms, "
              f"blocking={s['blocking_defects']}, llm={report['llm']['backend']} ok={report['llm']['ok']}",
              file=sys.stderr)
    else:
        sys.stdout.write(text)
    return exit_code(report)


if __name__ == '__main__':
    raise SystemExit(main())
