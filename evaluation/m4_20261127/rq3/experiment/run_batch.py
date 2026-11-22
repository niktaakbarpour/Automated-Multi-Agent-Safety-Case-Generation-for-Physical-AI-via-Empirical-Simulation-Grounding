"""Send the RQ3 batch to a model server and save every raw reply (M4 task A3). For Nikta's GPU runs.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/run_batch.py \\
        --batch evaluation/m4_20261127/rq3/experiment/batch \\
        --out RESPONSES.jsonl --base-url http://127.0.0.1:PORT/v1 --model-revision REVISION

It uses the Critic's own OpenAI-compatible client (critic.llm.OpenAICompatibleLLM) with the frozen settings in
settings.py, the same for every request. It only calls the model and saves what comes back: parsing and screening
happen later, on CPU, in score.py. Every attempt is appended to --out as one JSON line, so a stopped run can be
started again with the same command: requests that already have a line are skipped. A request that got no server
reply at all (connection or HTTP failure) is retried only with --retry-transport-errors; a request that got a
reply is never sent again, whatever the reply was.

--scripted FILE replaces the server with fixed replies ({run_id: reply text}, or {"*": text}), for CPU tests of
this script. Such output is labelled backend "scripted" and is never a model result.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import platform
import subprocess
import sys
import time

from critic import contract as K, llm as L

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import conditions as CND  # noqa: E402
import settings as S  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def load_batch(folder):
    folder = Path(folder)
    summary = json.loads((folder / 'BATCH.json').read_text(encoding='utf-8'))
    system = (folder / 'system_prompt.txt').read_text(encoding='utf-8')
    text = (folder / 'requests.jsonl').read_text(encoding='utf-8')
    if CND.sha256_text(text) != summary['requests_sha256'] or CND.sha256_text(system) != summary['system_sha256']:
        raise SystemExit('the batch files do not match BATCH.json; rebuild with build_batch.py')
    requests = [json.loads(line) for line in text.splitlines()]
    for r in requests:
        if CND.sha256_text(r['user']) != r['user_sha256'] or r['system_sha256'] != summary['system_sha256']:
            raise SystemExit(r['run_id'] + ': request hash mismatch')
    return summary, system, requests


def hardware():
    info = {'python': sys.version.split()[0], 'platform': platform.platform(), 'host': platform.node()}
    try:
        info['nvidia_smi'] = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,driver_version', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=20).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        info['nvidia_smi'] = None
    return info


def client(args, seed):
    if args.scripted:
        replies = json.loads(Path(args.scripted).read_text(encoding='utf-8'))
        return lambda run_id: L.ScriptedLLM(replies.get(run_id, replies.get('*')), name='scripted')
    extra = json.loads(json.dumps(S.SETTINGS['extra_body']))
    if seed is not None:
        extra['seed'] = seed
    llm = L.OpenAICompatibleLLM(base_url=args.base_url, model=args.model, temperature=args.temperature,
                                max_tokens=args.max_tokens, timeout=args.timeout, extra_body=extra,
                                accepted_models=args.accept_model)
    return lambda run_id: llm


def main(argv=None):
    p = argparse.ArgumentParser(prog='run_batch.py', description='Send the RQ3 batch to a model server.')
    p.add_argument('--batch', required=True, help='experiment/batch folder')
    p.add_argument('--out', required=True, help='JSONL file; attempts are appended')
    p.add_argument('--base-url', default=None, help='default $CRITIC_LLM_BASE_URL or http://localhost:8000/v1')
    p.add_argument('--model', default=S.SETTINGS['model'])
    p.add_argument('--model-revision', default=None, help='checkpoint or revision actually served (recorded)')
    p.add_argument('--accept-model', action='append', default=[], metavar='NAME',
                   help='another name the server may answer as (e.g. its served-model-name); repeatable')
    p.add_argument('--temperature', type=float, default=S.SETTINGS['temperature'])
    p.add_argument('--max-tokens', type=int, default=S.SETTINGS['max_tokens'])
    p.add_argument('--timeout', type=int, default=S.SETTINGS['timeout_s'])
    p.add_argument('--seed-base', type=int, default=None,
                   help='send seed = base + repeat in each request; whether the server enforces it is not checked')
    p.add_argument('--limit', type=int, default=None, help='send at most this many requests (for a smoke test)')
    p.add_argument('--retry-transport-errors', action='store_true',
                   help='send again only requests whose earlier attempts got no server reply')
    p.add_argument('--scripted', help='CPU test only: JSON file of fixed replies; never a model result')
    args = p.parse_args(argv)

    summary, system, requests = load_batch(args.batch)
    done = {}
    for line in read_jsonl(args.out):
        done.setdefault(line['run_id'], []).append(line)
    meta = {'kind': 'run_meta', 'started_utc': now(), 'argv': sys.argv[1:] if argv is None else argv,
            'batch_requests_sha256': summary['requests_sha256'], 'model_revision': args.model_revision,
            'scripted': bool(args.scripted), 'hardware': hardware(),
            'settings_deviate_from_frozen': {k: v for k, v in (('model', args.model),
                                                                 ('temperature', args.temperature),
                                                                 ('max_tokens', args.max_tokens),
                                                                 ('timeout_s', args.timeout))
                                             if v != S.SETTINGS[k]}}
    with open(str(args.out) + '.meta.jsonl', 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(meta) + '\n')

    sent = 0
    with open(args.out, 'a', encoding='utf-8') as out:
        for request in requests:
            earlier = done.get(request['run_id'], [])
            got_reply = any(a['reply'] is not None for a in earlier)
            if earlier and (got_reply or not args.retry_transport_errors):
                continue
            if args.limit is not None and sent >= args.limit:
                break
            seed = None if args.seed_base is None else args.seed_base + request['repeat']
            llm = client(args, seed)(request['run_id'])
            started, clock = now(), time.monotonic()
            record = {'run_id': request['run_id'], 'case_id': request['case_id'],
                      'condition': request['condition'], 'repeat': request['repeat'],
                      'attempt': len(earlier) + 1, 'user_sha256': request['user_sha256'],
                      'system_sha256': request['system_sha256'], 'backend': llm.backend,
                      'model_revision': args.model_revision, 'seed_sent': seed,
                      'settings': llm.settings(), 'input_sha256': K.digest(llm.messages(system, request['user'])),
                      'started_utc': started, 'reply': None, 'reply_sha256': None, 'response': None,
                      'error': None}
            try:
                reply, metadata = llm.call(system, request['user'])
                record.update(reply=reply, response=metadata,
                              reply_sha256=CND.sha256_text(reply) if isinstance(reply, str) else None)
            except Exception as exc:  # recorded, never hidden; the run goes on
                record['error'] = f'{type(exc).__name__}: {exc}'
            record.update(finished_utc=now(), latency_s=round(time.monotonic() - clock, 3))
            out.write(json.dumps(record, ensure_ascii=False) + '\n')
            out.flush()
            sent += 1
            print(f"{request['run_id']}: {'error ' + record['error'] if record['error'] else 'reply received'}",
                  file=sys.stderr)
    print(f'{sent} request(s) sent; {len(requests)} in the batch', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
