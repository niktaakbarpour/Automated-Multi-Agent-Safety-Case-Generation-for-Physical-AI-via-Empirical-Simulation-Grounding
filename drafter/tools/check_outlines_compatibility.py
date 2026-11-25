"""CPU-only check: can Outlines compile the R1 v3 plan schemas with the model's tokenizer in time?

No model weights, inference or GPU. Run it where the serving tokenizer is available, before a GPU run:

    python drafter/tools/check_outlines_compatibility.py \\
        --request evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json \\
        --tokenizer <tokenizer directory or Hugging Face name> --out outlines-check.json

It builds the Outlines index for the full plan schema and for the decoder schema the Drafter sends, each in a
separate process with a time limit (default 60 s, the limit reported by the server). It measures compilation only;
the server's own Outlines integration may build its vocabulary differently, so a real server run is still needed.
Needs outlines-core and transformers in the environment that runs it.
"""
import argparse
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _vocabulary(tokenizer_name):
    from outlines_core import Vocabulary
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    tokens = {}
    for token, token_id in tokenizer.get_vocab().items():
        if token_id == tokenizer.eos_token_id:
            continue
        text = tokenizer.convert_tokens_to_string([token])
        if text:
            tokens.setdefault(text, []).append(token_id)
    return Vocabulary(tokenizer.eos_token_id, tokens), len(tokens)


def _build(schema_text, tokenizer_name, queue):
    from outlines_core import Index
    from outlines_core.json_schema import build_regex_from_schema
    vocabulary, size = _vocabulary(tokenizer_name)
    regex = build_regex_from_schema(schema_text)
    started = time.monotonic()
    Index(regex, vocabulary)
    queue.put({'compiled': True, 'seconds': round(time.monotonic() - started, 2), 'vocabulary_tokens': size,
               'regex_characters': len(regex)})


def compile_within(schema, tokenizer_name, limit):
    queue = mp.Queue()
    process = mp.Process(target=_build, args=(json.dumps(schema), tokenizer_name, queue))
    process.start()
    process.join(limit + 120)  # loading the tokenizer is not part of the limit
    if process.is_alive():
        process.terminate()
        process.join()
        return {'compiled': False, 'seconds': None, 'note': 'still compiling at the time limit'}
    result = queue.get() if not queue.empty() else {
        'compiled': False, 'seconds': None,
        'note': f'the compile process ended without a result (exit code {process.exitcode}, for example out of memory)'}
    if result.get('compiled') and result['seconds'] > limit:
        result.update(compiled=False, note=f'compiled after {result["seconds"]} s, over the {limit} s limit')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--tokenizer', required=True)
    parser.add_argument('--limit-seconds', type=float, default=60.0)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Choose a new output path; existing results are never overwritten.')
    from drafter import r1v3_generation as G
    from drafter.validation import read_json
    full = G.plan_schema(read_json(args.request))
    report = {'model_called': False, 'gpu_used': False, 'tokenizer': args.tokenizer,
              'limit_seconds': args.limit_seconds,
              'decoder_schema': compile_within(G.decoder_schema(full), args.tokenizer, args.limit_seconds),
              'full_plan_schema': compile_within(full, args.tokenizer, args.limit_seconds)}
    report['passed'] = report['decoder_schema']['compiled']
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
