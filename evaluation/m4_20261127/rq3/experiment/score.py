"""Score RQ3 model outputs in three channels: rule-only, model-only T/R/C, rules + model (M4 tasks A3/A4).

    PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/score.py \\
        --responses RESPONSES.jsonl --out-dir evaluation/m4_20261127/rq3

CPU only. Reads the batch, the case files, the labels (mutations/gold_labels.json) and the runner's JSONL, and
writes RQ3_PER_CASE_RESULTS.csv (one row per request) and RQ3_SUMMARY.csv (one row per channel, condition,
subset and metric). Model findings are screened with the Critic's own screen (critic.llm.screen) against the
full case, with no rule-based finding given, in every condition. So the grounding gates are the same for T, R
and C, and a model finding is never removed only because a rule found the same defect.

Definitions (also in EXPERIMENT_CONFIG.md):
- An output is valid when the server replied, the reply finished normally (finish_reason "stop") as an accepted
  model name, and it holds a JSON object with a "findings" list. Missing and invalid outputs are counted, never
  treated as negatives: rates below use valid outputs as the denominator.
- Target hit: an accepted model finding on the labelled node (object_id equal to the label, or null when the node
  ID is unique). Detection: a target hit whose category is acceptable for the mutation's operator.
- Clean-control false positive: a valid output on a clean control with at least one accepted finding.
- Abstention: a valid output with an empty findings list.
- Rule-only detection: a rule-based finding (critic.checks.run_all) on the target with an acceptable category.
  Rules + model: rule-only detection or model detection, so each defect counts once.
- Reference-based correctness: a valid output whose result agrees with the reference label: the mutation is
  detected, or the clean control gets no accepted finding.
- Reference-supported findings: of the accepted model findings on mutation cases, those that are a detection
  (labelled node, acceptable category). The others have no reference label; they are not called wrong.
- Evidence-link correctness: of the model findings that cite evidence and whose citations were actually checked
  (not rejected earlier for format, category, object or node), those not rejected for a citation ("cites ...").
"""
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import argparse
import csv
import json
import statistics
import sys

from critic import checks, llm as L, schema as SCHEMA

HERE = Path(__file__).resolve().parent
RQ3 = HERE.parent
ROOT = RQ3.parents[2]
sys.path.insert(0, str(HERE))
import conditions as CND  # noqa: E402
import run_batch as RB  # noqa: E402

HALLUCINATED = 'cites evidence IDs that are not in the package'
RULE_ONLY_REJECTED = 'is decided by the rule-based checks only'
CITATION_REJECTED = 'cites '
# critic.llm._rejection_reason checks these before any citation, so a finding rejected for them had its
# citations never checked.
BEFORE_CITATIONS = ('does not match the finding format', 'missing explanation', 'category ', 'object ', 'node ')
SUBSETS = ('M1', 'M2', 'M3', 'all_mutations', 'clean_controls')
CASE_COLUMNS = (
    'run_id', 'case_id', 'condition', 'repeat', 'parent_group_id', 'case_type', 'mutation_operator',
    'c_availability', 'backend', 'model', 'model_revision', 'status', 'status_detail', 'attempts',
    'n_raw_findings', 'n_accepted', 'n_rejected', 'raw_target_hit', 'target_hit', 'detected',
    'target_categories', 'off_target_accepted', 'rule_only_category_at_target', 'hallucinated_citations',
    'abstained', 'clean_control_false_positive', 'reference_correct', 'reference_supported_accepted',
    'cited_findings_checked', 'citation_rejections', 'rule_only_findings', 'rule_only_detected',
    'rules_plus_model_detected', 'rules_plus_model_false_positive',
    'prompt_tokens', 'completion_tokens', 'latency_s', 'reply_sha256')
SUMMARY_COLUMNS = ('channel', 'condition', 'c_availability', 'subset', 'metric', 'numerator', 'denominator',
                   'rate', 'repeats', 'mean_over_repeats', 'sd_over_repeats', 'n_cases', 'n_groups', 'note')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def at(finding, location):
    """True when a finding names the labelled node: same node, and the same object or none given."""
    return (location is not None and finding.get('node_id') == location['node_id']
            and finding.get('object_id') in (location['object_id'], None))


def choose_attempt(attempts):
    """The first attempt that got a server reply; else the last attempt (a transport error)."""
    with_reply = [a for a in attempts if a['reply'] is not None]
    return (with_reply[0] if with_reply else attempts[-1]), len(attempts)


def citation_counts(accepted_raw, rejected):
    """(cited findings whose citations were checked, of which rejected for a citation)."""
    def cites(f):
        return isinstance(f, dict) and isinstance(f.get('evidence_ids'), list) and bool(f['evidence_ids'])
    checked = [f for f in accepted_raw if cites(f)]
    failed = 0
    for x in rejected:
        if cites(x['finding']) and not x['reason'].startswith(BEFORE_CITATIONS):
            checked.append(x['finding'])
            failed += x['reason'].startswith(CITATION_REJECTED)
    return len(checked), failed


def output_problem(attempt):
    """Why an attempt that got a reply is not a valid output, or None. Mirrors critic.llm.run."""
    response = attempt['response']
    if response is not None:  # a server reply; scripted test replies have no metadata
        accepted = attempt['settings'].get('accepted_models', [])
        if response.get('finish_reason') != 'stop':
            return f"finish_reason {response.get('finish_reason')!r}"
        if response.get('model') not in accepted:
            return f"answered as model {response.get('model')!r}"
    try:
        parsed = L.extract_json(attempt['reply'])
    except ValueError as exc:
        return str(exc)
    problems = SCHEMA.errors(parsed, L.REPLY_SCHEMA, limit=3)
    return '; '.join(problems) if problems else None


def score_rows(batch_dir, responses):
    summary, system, requests = RB.load_batch(batch_dir)
    labels = {x['case_id']: x for x in load(RQ3 / 'mutations' / 'gold_labels.json')}
    with open(RQ3 / 'MUTATION_MANIFEST.csv', encoding='utf-8') as fh:
        manifest = {r['case_id']: r for r in csv.DictReader(fh)}
    cases, screening, rules = {}, {}, {}
    for case_id in {r['case_id'] for r in requests}:
        cases[case_id] = load(ROOT / manifest[case_id]['case_file'])
        screening[case_id] = CND.screening_inputs(cases[case_id])
        rules[case_id] = checks.run_all(deepcopy(cases[case_id]))[0]
    attempts = defaultdict(list)
    for line in responses:
        attempts[line['run_id']].append(line)
    rows = []
    for request in requests:
        case_id, label = request['case_id'], labels[request['case_id']]
        location, acceptable = label['expected_location'], set(label['acceptable_model_categories'])
        mutation = label['case_type'] == 'mutation'
        rule_detected = mutation and any(at(f, location) and f['category'] in acceptable for f in rules[case_id])
        row = {k: '' for k in CASE_COLUMNS}
        row.update(run_id=request['run_id'], case_id=case_id, condition=request['condition'],
                   repeat=request['repeat'], parent_group_id=label['parent_group_id'],
                   case_type=label['case_type'], mutation_operator=label['mutation_operator'] or '',
                   c_availability=request['c_availability'],
                   rule_only_findings=len(rules[case_id]),
                   rule_only_detected=int(rule_detected) if mutation else '')
        if request['run_id'] not in attempts:
            row.update(status='missing', attempts=0)
            rows.append(row)
            continue
        attempt, count = choose_attempt(attempts[request['run_id']])
        if attempt['user_sha256'] != request['user_sha256'] or attempt['system_sha256'] != request['system_sha256']:
            raise ValueError(request['run_id'] + ': the response was made for a different request')
        response = attempt['response'] or {}
        usage = response.get('usage') or {}
        row.update(attempts=count, backend=attempt['backend'], model=attempt['settings'].get('model', ''),
                   model_revision=attempt.get('model_revision') or '', latency_s=attempt.get('latency_s', ''),
                   reply_sha256=attempt['reply_sha256'] or '', prompt_tokens=usage.get('prompt_tokens', ''),
                   completion_tokens=usage.get('completion_tokens', ''))
        if attempt['reply'] is None:
            row.update(status='no_reply', status_detail=attempt['error'] or '')
            rows.append(row)
            continue
        problem = output_problem(attempt)
        if problem:
            row.update(status='invalid_output', status_detail=problem)
            rows.append(row)
            continue
        raw = L.extract_json(attempt['reply'])['findings']
        records, admission = screening[case_id]
        accepted, rejected = L.screen(raw, cases[case_id], records, [], admission)
        hits = [f for f in accepted if at(f, location)]
        detected = mutation and any(f['category'] in acceptable for f in hits)
        rejected_ids = {id(x['finding']) for x in rejected}
        checked, citation_failed = citation_counts([f for f in raw if id(f) not in rejected_ids], rejected)
        row.update(
            status='valid', n_raw_findings=len(raw), n_accepted=len(accepted), n_rejected=len(rejected),
            raw_target_hit=int(any(isinstance(f, dict) and at(f, location) for f in raw)),
            target_hit=int(bool(hits)), detected=int(detected) if mutation else '',
            target_categories=';'.join(sorted({f['category'] for f in hits})),
            off_target_accepted=sum(not at(f, location) for f in accepted),
            rule_only_category_at_target=int(any(
                RULE_ONLY_REJECTED in x['reason'] and isinstance(x['finding'], dict) and at(x['finding'], location)
                for x in rejected)),
            hallucinated_citations=sum(x['reason'].startswith(HALLUCINATED) for x in rejected),
            abstained=int(not raw),
            clean_control_false_positive=int(bool(accepted)) if not mutation else '',
            reference_correct=int(detected) if mutation else int(not accepted),
            reference_supported_accepted=sum(f['category'] in acceptable for f in hits) if mutation else '',
            cited_findings_checked=checked, citation_rejections=citation_failed,
            rules_plus_model_detected=int(rule_detected or detected) if mutation else '',
            rules_plus_model_false_positive=int(bool(accepted) or bool(rules[case_id])) if not mutation else '')
        rows.append(row)
    return summary, rows


def in_subset(row, subset):
    if subset == 'clean_controls':
        return row['case_type'] == 'clean_control'
    if subset == 'all_mutations':
        return row['case_type'] == 'mutation'
    return row['mutation_operator'] == subset


def rate_row(channel, condition, availability, subset, metric, rows, value, note='', weight=None):
    """A summary row: pooled rate over the given rows, and mean and SD of the per-repeat rates.

    Without weight the denominator is the number of rows (outputs). With weight it is the sum of weight(row),
    for finding-level rates; a repeat with a zero denominator has no rate and is left out of the mean and SD.
    """
    weight = weight or (lambda r: 1)
    numerator, denominator = sum(value(r) for r in rows), sum(weight(r) for r in rows)
    by_repeat = defaultdict(lambda: [0, 0])
    for r in rows:
        by_repeat[r['repeat']][0] += value(r)
        by_repeat[r['repeat']][1] += weight(r)
    rates = [n / d for _, (n, d) in sorted(by_repeat.items()) if d]
    return {'channel': channel, 'condition': condition, 'c_availability': availability, 'subset': subset,
            'metric': metric, 'numerator': numerator, 'denominator': denominator,
            'rate': round(numerator / denominator, 4) if denominator else '',
            'repeats': len(rates), 'mean_over_repeats': round(statistics.mean(rates), 4) if rates else '',
            'sd_over_repeats': round(statistics.stdev(rates), 4) if len(rates) >= 2 else '',
            'n_cases': len({r['case_id'] for r in rows}), 'n_groups': len({r['parent_group_id'] for r in rows}),
            'note': note}


def summarize(rows):
    out = []
    first_repeat = [r for r in rows if r['repeat'] == min(x['repeat'] for x in rows)]
    for subset in SUBSETS:  # rule-only: one result per case, the same in every condition
        group = [r for r in first_repeat if r['condition'] == 'T' and in_subset(r, subset)]
        if not group:
            continue
        if subset == 'clean_controls':
            out.append(rate_row('rule_only', '', '', subset, 'false_positive', group,
                                lambda r: int(r['rule_only_findings'] > 0), 'deterministic; no model, no repeats'))
        else:
            out.append(rate_row('rule_only', '', '', subset, 'detection', group,
                                lambda r: r['rule_only_detected'], 'deterministic; no model, no repeats'))
    for condition in CND.CONDITIONS:
        here = [r for r in rows if r['condition'] == condition]
        availability = ';'.join(sorted({r['c_availability'] for r in here})) if condition == 'C' else ''
        note_c = 'C carries checker status only; no requirement-checked verdict' \
            if condition == 'C' and availability == 'status_only' else ''
        out.append(rate_row('model_only', condition, availability, 'all_requests', 'valid_output', here,
                            lambda r: r['status'] == 'valid',
                            'missing, no-reply and invalid outputs count against validity only'))
        valid = [r for r in here if r['status'] == 'valid']
        if valid:
            out.append(rate_row('model_only', condition, availability, 'all_cases', 'reference_correct', valid,
                                lambda r: r['reference_correct'], note_c))
            out.append(rate_row('rules_plus_model', condition, availability, 'all_cases', 'reference_correct',
                                valid, lambda r: r['rules_plus_model_detected'] if r['case_type'] == 'mutation'
                                else int(not r['rules_plus_model_false_positive']), note_c))
            out.append(rate_row('model_only', condition, availability, 'all_cases', 'evidence_link_correct', valid,
                                lambda r: r['cited_findings_checked'] - r['citation_rejections'],
                                'finding level: cited findings whose citations were checked' +
                                ('; ' + note_c if note_c else ''), weight=lambda r: r['cited_findings_checked']))
            mutations = [r for r in valid if r['case_type'] == 'mutation']
            out.append(rate_row('model_only', condition, availability, 'all_mutations',
                                'accepted_findings_reference_supported', mutations,
                                lambda r: r['reference_supported_accepted'],
                                'finding level: accepted findings on mutation cases; the rest have no reference, '
                                'not a wrong label' + ('; ' + note_c if note_c else ''),
                                weight=lambda r: r['n_accepted']))
        for subset in SUBSETS:
            group = [r for r in valid if in_subset(r, subset)]
            if not group:
                continue
            if subset == 'clean_controls':
                out.append(rate_row('model_only', condition, availability, subset, 'false_positive', group,
                                    lambda r: r['clean_control_false_positive'], note_c))
                out.append(rate_row('rules_plus_model', condition, availability, subset, 'false_positive', group,
                                    lambda r: r['rules_plus_model_false_positive'], note_c))
            else:
                out.append(rate_row('model_only', condition, availability, subset, 'detection', group,
                                    lambda r: r['detected'], note_c))
                out.append(rate_row('model_only', condition, availability, subset, 'target_hit_any_category',
                                    group, lambda r: r['target_hit'], note_c))
                out.append(rate_row('rules_plus_model', condition, availability, subset, 'detection', group,
                                    lambda r: r['rules_plus_model_detected'], note_c))
            out.append(rate_row('model_only', condition, availability, subset, 'abstention', group,
                                lambda r: r['abstained'], note_c))
            out.append(rate_row('model_only', condition, availability, subset, 'outputs_with_hallucinated_citation',
                                group, lambda r: int(r['hallucinated_citations'] > 0), note_c))
    return out


def write(path, columns, rows):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    p = argparse.ArgumentParser(prog='score.py', description='Score RQ3 model outputs.')
    p.add_argument('--batch', default=str(HERE / 'batch'))
    p.add_argument('--responses', required=True, nargs='+', help='JSONL files written by run_batch.py')
    p.add_argument('--out-dir', required=True)
    args = p.parse_args(argv)
    responses = [line for path in args.responses for line in RB.read_jsonl(path)]
    summary, rows = score_rows(args.batch, responses)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write(out / 'RQ3_PER_CASE_RESULTS.csv', CASE_COLUMNS, rows)
    write(out / 'RQ3_SUMMARY.csv', SUMMARY_COLUMNS, summarize(rows))
    statuses = defaultdict(int)
    for r in rows:
        statuses[r['status']] += 1
    backends = sorted({r['backend'] for r in rows if r['backend']})
    print(f"{len(rows)} requests: {dict(statuses)}; backends {backends}", file=sys.stderr)
    if 'scripted' in backends:
        print('WARNING: scripted replies are test inputs, not model results', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
