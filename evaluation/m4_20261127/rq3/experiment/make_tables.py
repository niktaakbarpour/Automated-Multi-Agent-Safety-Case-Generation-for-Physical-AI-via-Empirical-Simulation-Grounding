"""Turn the RQ3 scorer output into Markdown tables (M4 task A4). CPU only.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/make_tables.py \\
        --results-dir evaluation/m4_20261127/rq3 --out evaluation/m4_20261127/rq3/RQ3_TABLES.md

Reads RQ3_PER_CASE_RESULTS.csv and RQ3_SUMMARY.csv written by score.py and prints nothing new: every number is
copied from those files or counted from the per-case rows. Four tables:

1. Output validity per condition (missing, no reply, invalid, valid).
2. Detection and false positives per channel and condition, as pooled k/n with mean and SD over repeats.
3. Per case: how many of the valid repeats detected the mutation (or, for clean controls, raised a finding),
   in each condition, next to the rule-only result. With 12 cases from 2 parents this is the table to read first.
4. Rejected model findings: hallucinated citations and rule-only categories put on the target.
5. Reference-based correctness, reference-supported findings and evidence-link correctness.
"""
from collections import defaultdict
from pathlib import Path
import argparse
import csv
import sys

CONDITIONS = ('T', 'R', 'C')
STATUSES = ('valid', 'invalid_output', 'no_reply', 'missing')
SUBSET_ORDER = ('M1', 'M2', 'M3', 'all_mutations', 'clean_controls')


def read(path):
    with open(path, encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def table(header, rows):
    lines = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    lines += ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows]
    return '\n'.join(lines)


def fraction(row):
    if row is None:
        return 'n/a'
    if row['denominator'] in ('', '0'):
        return 'none (0/0)'
    text = f"{row['numerator']}/{row['denominator']}"
    if row['mean_over_repeats'] != '':
        text += f" (mean {float(row['mean_over_repeats']):.2f}"
        text += f", SD {float(row['sd_over_repeats']):.2f})" if row['sd_over_repeats'] != '' else ')'
    return text


def validity(cases):
    counts = defaultdict(lambda: defaultdict(int))
    for r in cases:
        counts[r['condition']][r['status']] += 1
    rows = [[c] + [counts[c][s] for s in STATUSES] + [sum(counts[c].values())] for c in CONDITIONS]
    return table(['Condition', 'Valid', 'Invalid output', 'No reply', 'Missing', 'Requests'], rows)


def rates(summary):
    index = {(r['channel'], r['condition'], r['subset'], r['metric']): r for r in summary}
    rows = []
    for subset in SUBSET_ORDER:
        metric = 'false_positive' if subset == 'clean_controls' else 'detection'
        rule = index.get(('rule_only', '', subset, metric))
        row = [subset.replace('_', ' '), metric.replace('_', ' '),
               f"{rule['numerator']}/{rule['denominator']}" if rule else 'n/a']
        row += [fraction(index.get(('model_only', c, subset, metric))) for c in CONDITIONS]
        row += [fraction(index.get(('rules_plus_model', c, subset, metric))) for c in CONDITIONS]
        rows.append(row)
    header = ['Cases', 'Metric', 'Rule-only'] + [f'Model {c}' for c in CONDITIONS] + [f'Rules + model {c}'
                                                                                   for c in CONDITIONS]
    return table(header, rows)


def per_case(cases):
    by = defaultdict(list)
    for r in cases:
        by[(r['case_id'], r['condition'])].append(r)
    order = []
    for r in cases:
        if r['case_id'] not in order:
            order.append(r['case_id'])
    rows = []
    for case_id in order:
        first = by[(case_id, 'T')][0]
        mutation = first['case_type'] == 'mutation'
        key = 'detected' if mutation else 'clean_control_false_positive'
        cells = []
        for c in CONDITIONS:
            valid = [r for r in by[(case_id, c)] if r['status'] == 'valid']
            text = f"{sum(int(r[key]) for r in valid)}/{len(valid)}"
            if len(valid) < len(by[(case_id, c)]):
                text += f" ({len(by[(case_id, c)]) - len(valid)} not valid)"
            cells.append(text)
        rule = ('yes' if first['rule_only_detected'] == '1' else 'no') if mutation else (
            'finding' if first['rule_only_findings'] != '0' else 'none')
        rows.append([case_id, first['mutation_operator'] or 'clean control', first['parent_group_id'].split(':')[0],
                     rule] + cells)
    return table(['Case', 'Operator', 'Parent source', 'Rule-only'] + [f'{c}: hits/valid' for c in CONDITIONS], rows)


def rejections(cases):
    rows = []
    for c in CONDITIONS:
        valid = [r for r in cases if r['condition'] == c and r['status'] == 'valid']
        rows.append([c, len(valid), sum(int(r['n_raw_findings']) for r in valid),
                     sum(int(r['n_accepted']) for r in valid), sum(int(r['n_rejected']) for r in valid),
                     sum(int(r['hallucinated_citations']) > 0 for r in valid),
                     sum(int(r['rule_only_category_at_target']) for r in valid),
                     sum(int(r['target_hit']) and not int(r['detected'] or 0) for r in valid
                         if r['case_type'] == 'mutation')])
    return table(['Condition', 'Valid outputs', 'Raw findings', 'Accepted', 'Rejected',
                  'Outputs citing an invented ID', 'Rule-only category on target',
                  'Target hit, wrong category'], rows)


def correctness(summary):
    index = {(r['channel'], r['condition'], r['metric']): r for r in summary}
    rows = []
    for c in CONDITIONS:
        rows.append([c] + [fraction(index.get(key)) for key in (
            ('model_only', c, 'reference_correct'), ('rules_plus_model', c, 'reference_correct'),
            ('model_only', c, 'accepted_findings_reference_supported'), ('model_only', c, 'evidence_link_correct'))])
    return table(['Condition', 'Reference-correct outputs, model', 'Reference-correct outputs, rules + model',
                  'Accepted findings on mutations matching the label', 'Checked citations that hold'], rows)


def build(results_dir):
    results_dir = Path(results_dir)
    cases = read(results_dir / 'RQ3_PER_CASE_RESULTS.csv')
    summary = read(results_dir / 'RQ3_SUMMARY.csv')
    backends = sorted({r['backend'] for r in cases if r['backend']})
    parts = ['# RQ3 tables', '',
             'Generated by `experiment/make_tables.py` from RQ3_PER_CASE_RESULTS.csv and RQ3_SUMMARY.csv. '
             'Do not edit by hand; rerun the script.', '',
             f"Backends in the results: {', '.join(backends) or 'none'}. Development only: 12 cases from 2 parent "
             'groups, 0 independent cases. Rates use valid outputs as the denominator; SD is over the 3 repeats.', '']
    if 'scripted' in backends:
        parts += ['**These tables come from scripted test replies, not model results.**', '']
    parts += ['## 1. Output validity', '', validity(cases), '',
              '## 2. Detection and clean-control false positives', '',
              'Rule-only is deterministic (one result per case). Model cells: pooled k/n over valid outputs, '
              'with mean and SD of the per-repeat rates. C is status only for both parents.', '',
              rates(summary), '',
              '## 3. Per case', '',
              'Mutations: valid repeats that detected the mutation. Clean controls: valid repeats with at least '
              'one accepted finding (a false positive).', '', per_case(cases), '',
              '## 4. Rejected and misplaced model findings', '', rejections(cases), '',
              '## 5. Reference-based correctness and evidence links', '',
              'Reference-correct: the mutation is detected, or the clean control gets no accepted finding (all '
              'valid outputs). Matching the label: accepted findings on mutation cases that are a detection; the '
              'others have no reference label and are not called wrong. Citations: model findings that cite '
              'evidence and reached the citation check, not rejected for a citation.', '', correctness(summary), '']
    return '\n'.join(parts), backends


def main(argv=None):
    p = argparse.ArgumentParser(prog='make_tables.py', description='Markdown tables from the RQ3 scorer output.')
    p.add_argument('--results-dir', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args(argv)
    text, backends = build(args.results_dir)
    Path(args.out).write_text(text, encoding='utf-8')
    if 'scripted' in backends:
        print('WARNING: scripted replies are test inputs, not model results', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
