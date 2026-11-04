"""Small exploratory model comparison on the three cases (run on Hestia).

Start one vLLM server per model, then:

    python3 -m critic.compare_models \
        --model openai/gpt-oss-20b=http://localhost:8000/v1 \
        --model Qwen/Qwen3-32B=http://localhost:8001/v1 \
        --repeats 3 --out critic/examples/model_comparison.md

Per model and case it records whether the LLM added an expected finding, whether it
criticised the correct unresolved argument (false positive), whether it cited
invented evidence/nodes, whether its JSON parsed, and latency. Three synthetic
cases are an exploratory comparison, not a benchmark.
"""
import argparse
import json
import statistics
from pathlib import Path

from . import llm as L
from .critic import review

CASES = Path(__file__).parent / 'cases'


def evaluate(model, base_url, repeats, max_tokens, json_mode):
    expected = json.loads((CASES / 'expected.json').read_text())
    extra = {'response_format': {'type': 'json_object'}} if json_mode else {}
    client = L.OpenAICompatibleLLM(base_url=base_url, model=model, max_tokens=max_tokens, extra_body=extra)
    rows = []
    for name, exp in expected.items():
        request = json.loads((CASES / name).read_text())
        for run in range(repeats):
            report = review(request, client)
            llm_findings = [c for c in report['criticisms'] if c['finding_source'] == 'llm_proposed']
            invented = [r for r in report['rejected_llm_findings']
                        if any(s in r['reason'] for s in ('not in the package', 'does not exist', 'not a configured'))]
            wanted = set(exp['llm_should_add_any_of'])
            rows.append({
                'model': model, 'case': name, 'run': run,
                'json_ok': report['llm']['ok'], 'error': report['llm']['error'],
                'latency_s': report['llm']['latency_s'],
                'llm_findings': len(llm_findings),
                'categories': sorted({c['category'] for c in llm_findings}),
                'hit_expected': bool(wanted & {c['category'] for c in llm_findings}) if wanted else None,
                'false_positive': bool(llm_findings) if not exp['blocking_expected'] else None,
                'invented_refs': len(invented),
                'rejected_total': len(report['rejected_llm_findings']),
            })
    return rows


COLUMNS = ('Model', 'Case', 'JSON valid', 'Expected issue found', 'False positive on Case C',
           'Invented IDs', 'LLM categories', 'Median latency (s)')


def _share(runs, key):
    """'2/3' style count of runs where key is true, or 'n/a' if the metric does not apply to this case."""
    if runs[0][key] is None:
        return 'n/a'
    return f'{sum(bool(r[key]) for r in runs)}/{len(runs)}'


def table(rows):
    """Markdown table with one line per model and case."""
    lines = ['| ' + ' | '.join(COLUMNS) + ' |', '|' + '---|' * len(COLUMNS)]
    grouped = {}
    for r in rows:
        grouped.setdefault((r['model'], r['case']), []).append(r)
    for (model, case), runs in grouped.items():
        latencies = [r['latency_s'] for r in runs if r['latency_s'] is not None]
        cells = [
            model,
            case.replace('.json', ''),
            _share(runs, 'json_ok'),
            _share(runs, 'hit_expected'),
            _share(runs, 'false_positive'),
            str(sum(r['invented_refs'] for r in runs)),
            ', '.join(sorted({c for r in runs for c in r['categories']})) or '-',
            str(statistics.median(latencies)) if latencies else '-',
        ]
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(prog='python3 -m critic.compare_models')
    p.add_argument('--model', action='append', required=True, help='NAME=BASE_URL (repeatable)')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--max-tokens', type=int, default=8192)
    p.add_argument('--json-mode', action='store_true')
    p.add_argument('--out', default='critic/examples/model_comparison.md')
    args = p.parse_args(argv)
    rows = []
    for spec in args.model:
        name, _, url = spec.partition('=')
        rows += evaluate(name, url or None, args.repeats, args.max_tokens, args.json_mode)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix('.json').write_text(json.dumps(rows, indent=1) + '\n')
    out.write_text('# Exploratory Critic model comparison (3 synthetic cases)\n\n' + table(rows) +
                   '\n\nExploratory only: three synthetic cases, not a benchmark. Raw rows in '
                   + out.with_suffix('.json').name + '.\n')
    print(table(rows))


if __name__ == '__main__':
    main()
