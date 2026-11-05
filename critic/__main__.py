"""Command line: python3 -m critic --request FILE [--backend none|openai] [--model NAME]

Examples
  python3 -m critic --request critic/cases/case_a_unsupported_claim.json
  python3 -m critic --request critic/cases/case_a_unsupported_claim.json \
      --backend openai --base-url http://localhost:8000/v1 --model openai/gpt-oss-20b
"""
import argparse
import json
import sys

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
                                 max_tokens=args.max_tokens, extra_body=extra)


def main(argv=None):
    p = argparse.ArgumentParser(prog='python3 -m critic', description='Review one R1 argument bundle.')
    p.add_argument('--request', required=True, help='critic-request/0.1.0 JSON file')
    p.add_argument('--backend', choices=['none', 'openai', 'scripted'], default='none',
                   help='none = rule checks only; openai = any OpenAI-compatible server such as vLLM')
    p.add_argument('--base-url', default=None, help='default $CRITIC_LLM_BASE_URL or http://localhost:8000/v1')
    p.add_argument('--model', default=None, help='default $CRITIC_LLM_MODEL')
    p.add_argument('--temperature', type=float, default=None,
                   help="default: the model card's setting (see llm.MODEL_PRESETS)")
    p.add_argument('--max-tokens', type=int, default=8192)
    p.add_argument('--json-mode', action='store_true', help='ask the server for response_format=json_object')
    p.add_argument('--scripted-reply', help='file with a fixed model reply (used with --backend scripted)')
    p.add_argument('--out', help='write the report here instead of stdout')
    args = p.parse_args(argv)
    if args.backend == 'scripted' and not args.scripted_reply:
        p.error('--backend scripted needs --scripted-reply FILE')
    with open(args.request, encoding='utf-8') as fh:
        request = json.load(fh)
    report = review(request, make_llm(args))
    text = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fh:
            fh.write(text)
        s = report['summary']
        print(f"{args.out}: {len(report['criticisms'])} criticisms, blocking={s['blocking_defects']}, "
              f"llm={report['llm']['backend']} ok={report['llm']['ok']}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
