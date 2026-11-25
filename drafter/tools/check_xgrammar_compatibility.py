"""CPU-only EOS-aware schema check; no model weights, inference or GPU required.

Run in the serving environment that already contains XGrammar 0.1.25. This uses
an explicit tiny ASCII tokenizer to test schema-language acceptance, not the
model's tokenizer or the complete server integration. A real server rerun remains
necessary. The optional --plan replays supplied JSON through both schema engines.
"""
import argparse
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator
from drafter.plan_schema import build_plan_schema
from drafter.validation import read_json


def eos_accepts(xgr, grammar, text, stop_token):
    matcher = xgr.GrammarMatcher(grammar, override_stop_tokens=[stop_token])
    prefix = bool(matcher.accept_string(text))
    eos = bool(matcher.accept_token(stop_token)) if prefix else False
    return {'prefix_accepted': prefix, 'eos_accepted': eos,
            'complete': bool(eos and matcher.is_terminated())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, default=ROOT / 'drafter/cases/scenario_a.request.json')
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--expected-xgrammar-version', default='0.1.25')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Choose a new output path; existing results are never overwritten.')
    try:
        actual_version = version('xgrammar')
    except PackageNotFoundError:
        parser.error('XGrammar is not installed. Run this check in the recorded serving environment.')
    if actual_version != args.expected_xgrammar_version:
        parser.error('XGrammar version mismatch: installed ' + actual_version)
    import xgrammar as xgr

    vocab = [chr(i) for i in range(32, 127)] + ['\n', '\t', '\r', '<eos>']
    stop_token = len(vocab) - 1
    tokenizer = xgr.TokenizerInfo(vocab, xgr.VocabType.RAW, stop_token_ids=[stop_token])
    compiler = xgr.GrammarCompiler(tokenizer, max_threads=1, cache_enabled=False)
    request = read_json(args.request)
    if request.get('schema_version') == 'drafter-request/0.2.0':  # R1 v3: check the schema actually sent
        from drafter import r1v3_generation as G
        schema = G.decoder_schema(G.plan_schema(request))
    else:
        schema = build_plan_schema(request)
    old_text = {'type': 'string', 'minLength': 1, 'maxLength': 1600, 'pattern': r'\S'}
    text_schemas = {'original_text': old_text, 'corrected_text': schema['$defs']['text']}
    report = {'xgrammar_version': actual_version, 'model_called': False, 'gpu_used': False,
              'tokenizer': 'explicit tiny ASCII vocabulary; not the Qwen tokenizer',
              'checks': {}, 'full_plan_schema_compiled': False}
    examples = ('R', 'R1', 'R1 remains unresolved for all protected objects.')
    for name, text_schema in text_schemas.items():
        grammar = compiler.compile_json_schema(text_schema)
        report['checks'][name] = [
            {'value': value,
             'json_schema_valid': Draft202012Validator(text_schema).is_valid(value),
             **eos_accepts(xgr, grammar, json.dumps(value), stop_token)}
            for value in examples
        ]
    full_grammar = compiler.compile_json_schema(schema)
    report['full_plan_schema_compiled'] = True
    if args.plan:
        plan = read_json(args.plan)
        report['supplied_plan'] = {
            'json_schema_valid': Draft202012Validator(schema).is_valid(plan),
            **eos_accepts(xgr, full_grammar, json.dumps(plan), stop_token),
        }
    corrected = report['checks']['corrected_text']
    report['passed'] = (report['full_plan_schema_compiled']
                        and corrected[2]['complete'] and not corrected[0]['complete'])
    if args.plan:
        report['passed'] = (report['passed'] and
                            report['supplied_plan']['json_schema_valid'] ==
                            report['supplied_plan']['complete'])
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
