"""Score the RQ4 planted-defect repair experiment. CPU only.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/score.py \\
        --stage1-responses RUN/RQ4_STAGE1_RESPONSES.jsonl --stage2-responses RUN/RQ4_STAGE2_RESPONSES.jsonl \\
        --out-dir evaluation/m4_20261127/rq4

Before anything is written, every binding is checked, and any problem stops the run with the full list:
- stage 1 equals a fresh build (frozen inputs, hand-recorded approvals, prompts);
- the saved Qwen results and the second Critic batch are exactly what the stage 1 responses produce;
- every stage 2 reply passes the same response checks as stage 1 (run IDs, input and output digests, model
  identity, frozen settings, one model revision) and is bound to its Critic request by digest;
- the sealed key matches the saved results and the review items, and the review form is complete and valid.

Primary measure: the blinded human review (rq4/REVIEW/REVIEW_FORM.csv, joined to methods through
experiment/sealed/REVIEW_KEY.json). The method comparison (RQ4_SUMMARY.csv, RQ4_TABLES.md, RQ4_PER_OUTPUT.csv,
RQ4_PROVENANCE.json) is written only when the review is complete and valid. With --pre-review, only
RQ4_PRE_REVIEW_FACTS.csv is written: structural and second-Critic facts per output, no human judgments.
Existing output files are never changed unless --replace-outputs is given.

Definitions (also in RQ4_PROTOCOL.md):
- Output: one template revision per case, one Qwen revision per case and sample (9, all kept, missing included).
- Status: revised; abstained (the method declined); invalid (unparseable or malformed answer, an edit the
  host refused, a revision that failed a validator, or a server reply that did not finish normally);
  missing or no_reply. Only revised outputs are reviewed. The others count as not repaired and stay in the
  denominators.
- Correct repair (human): defect fixed "yes", revised claim supported "yes", new problem "no" and scope
  preserved "yes", all four.
- Second Critic (secondary, never decides correctness): the production Critic on the revised argument.
  Target still flagged: a finding on the planted-defect node with a category acceptable for the defect
  type. New objection: any other finding whose (object, node, category) appears in neither the stage 1
  report nor any second review of the original argument. Missing second reviews are counted per output.
"""
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
import argparse
import csv
import io
import json
import statistics
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM  # noqa: E402
import build_review as BR  # noqa: E402
import build_stage1 as B1  # noqa: E402
import build_stage2 as B2  # noqa: E402
from critic import llm as L  # noqa: E402
from drafter.revision import engine as E  # noqa: E402

INVALID = ('invalid_unparseable', 'invalid_malformed', 'edit_refused', 'validation_failed', 'invalid_server_reply')
OUTPUT_COLUMNS = ('output_id', 'method', 'case_id', 'sample', 'status', 'stop_reason', 'new_statement',
                  'validators_failed', 'refused_edit_reasons', 'second_reviews', 'second_reviews_missing',
                  'second_reviews_target_flagged', 'second_reviews_with_new_objection', 'new_objections',
                  'blind_item_id', 'defect_fixed', 'revised_claim_supported_by_evidence', 'new_problem_introduced',
                  'scope_preserved', 'correct_repair')
GROUPS = {c['case_id']: CM.rq3_tables()[1][c['case_id']]['parent_group_id'] for c in CM.CASES}
SUMMARY_COLUMNS = ('method', 'metric', 'numerator', 'denominator', 'rate', 'samples', 'mean_over_samples',
                   'sd_over_samples', 'n_cases', 'n_groups', 'note')


def check_frozen_stage1(problems):
    try:
        stale = CM.stale_files({(HERE / n).resolve(): t for n, t in B1.build().items()})
    except ValueError as exc:
        problems.append(f'stage 1 cannot be rebuilt: {exc}')
        return
    problems += [f'stage 1 file differs from a fresh build: {p}' for p in stale]


def check_stage2_files(base, stage1_responses, allow_scripted, problems):
    """The saved Qwen results and second Critic batch must be exactly what the stage 1 responses give."""
    for cid in [c['case_id'] for c in CM.CASES]:
        rel = Path('results') / 'template' / f'{cid}.revision_result.json'
        if (base / rel).read_text(encoding='utf-8') != (HERE / rel).read_text(encoding='utf-8'):
            problems.append(f'{rel} differs from the frozen template result')
    try:
        files = B2.build(stage1_responses, allow_scripted)
    except ValueError as exc:
        problems.append(f'stage 1 responses: {exc}')
        return
    problems += [f'differs from what the stage 1 responses give: {p}'
                 for p in CM.stale_files({base / n: t for n, t in files.items()})]
    saved = sorted(p.name for p in (base / 'results' / 'qwen').glob('*.json'))
    if saved != BR.expected_qwen_files():
        problems.append('results/qwen does not hold exactly the 9 expected Qwen result files')


def load_outputs(base):
    states = {s.case_id: s for s in CM.states()}
    out = []
    for cid, state in states.items():
        t = CM.load_json(base / 'results' / 'template' / f'{cid}.revision_result.json')
        out.append({'output_id': f'{cid}:template', 'method': 'template', 'case_id': cid,
                    'sample': '', 'status': CM.classify_output(t['result']), 'result': t['result'], 'state': state})
    for name in BR.expected_qwen_files():
        q = CM.load_json(base / 'results' / 'qwen' / name)
        out.append({'output_id': q['run_id'], 'method': 'qwen', 'case_id': q['case_id'], 'sample': q['repeat'],
                    'status': q['status'], 'result': q['result'], 'state': states[q['case_id']]})
    return out


def second_reviews(base, responses, allow_scripted, problems):
    """{target_id: [Critic report or None for a missing reply]}, each report rebuilt by critic.review from a
    reply that passed the response checks and is bound to its Critic request by digest."""
    summary, system, requests = CM.RB.load_batch(base / 'batch_stage2')
    if summary['system_sha256'] != CM.sha256_text(L.PROMPT_PATH.read_text(encoding='utf-8')):
        problems.append('batch_stage2 does not use the frozen Critic prompt')
    try:
        chosen = CM.checked_attempts(responses, requests, system, allow_scripted)
    except ValueError as exc:
        problems.append(f'stage 2 responses: {exc}')
        return {}
    reports = defaultdict(list)
    for request in requests:
        attempt, _ = chosen[request['run_id']]
        path = base / 'stage2_requests' / f"{request['target_id'].replace(':', '_')}.critic_request.json"
        critic_request = CM.load_json(path)
        if CM.K.digest(critic_request) != request['critic_request_sha256']:
            problems.append(f"{request['run_id']}: its Critic request file does not match the batch")
            continue
        if attempt is None or attempt['reply'] is None:
            reports[request['target_id']].append(None)
            continue
        try:
            reports[request['target_id']].append(CM.replayed_report(critic_request, attempt))
        except ValueError as exc:
            problems.append(str(exc))
    return reports


def check_targets(base, outputs, problems):
    """Each second-review request must be the original argument, or the re-criticism request of its saved
    revision result, so every second review is bound to the output it is counted for."""
    for o in outputs:
        state, cid = o['state'], o['case_id']
        expected = {f'{cid}:original': state.critic_request}
        if o['status'] == 'revised':
            expected[o['output_id'] if o['method'] == 'qwen' else f'{cid}:template'] = \
                E.recriticism_request(state.request, o['result'])
        for tid, critic_request in expected.items():
            path = base / 'stage2_requests' / f"{tid.replace(':', '_')}.critic_request.json"
            if not path.exists() or CM.K.digest(CM.load_json(path)) != CM.K.digest(critic_request):
                problems.append(f'{tid}: the second-review request is not the one this output gives')


def keys(report):
    return {(c['object_id'], c['node_id'], c['category']) for c in report['criticisms']}


def is_iso_date(text):
    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def is_iso_timestamp(text):
    try:
        datetime.fromisoformat(text)
        return '-' in text and ('T' in text or ' ' in text)
    except ValueError:
        return False


def read_review(review_dir, key_path, outputs, problems):
    """{output_id: judgment row} when the key, the items and the form are all valid; problems are appended."""
    review_dir, judgments = Path(review_dir), {}
    try:
        key = CM.load_json(key_path)['items']
    except (OSError, ValueError, KeyError) as exc:
        problems.append(f'the review key cannot be read: {exc}')
        return judgments
    ids = [k['blind_item_id'] for k in key]
    if len(ids) != len(set(ids)):
        problems.append('the review key repeats a blind item ID')
    revised = {o['output_id']: o for o in outputs if o['status'] == 'revised'}
    if sorted(k['output_id'] for k in key) != sorted(revised):
        problems.append('the review key does not list exactly the revised outputs')
    manifest = {}
    if (review_dir / 'REVIEW_MANIFEST.csv').exists():
        manifest = {r['blind_item_id']: r for r in CM.read_csv(review_dir / 'REVIEW_MANIFEST.csv')[1]}
    for k in key:
        o = revised.get(k['output_id'])
        if o is not None and CM.K.digest(o['result']) != k.get('result_sha256'):
            problems.append(f"{k['blind_item_id']}: the key is bound to a different revision result")
        item = review_dir / 'items' / f"{k['blind_item_id']}.md"
        if not item.exists() or CM.sha256_text(item.read_text(encoding='utf-8')) != k.get('item_sha256'):
            problems.append(f"{k['blind_item_id']}: the review item is missing or was changed")
        elif manifest.get(k['blind_item_id'], {}).get('sha256') != k.get('item_sha256'):
            problems.append(f"{k['blind_item_id']}: REVIEW_MANIFEST.csv does not match the item")
    form = review_dir / 'REVIEW_FORM.csv'
    if not form.exists():
        problems.append('REVIEW_FORM.csv is missing')
        return judgments
    header, rows = CM.read_csv(form)
    if tuple(header) != BR.FORM_COLUMNS:
        problems.append('REVIEW_FORM.csv: the columns must be exactly ' + ', '.join(BR.FORM_COLUMNS))
        return judgments
    seen = defaultdict(int)
    for r in rows:
        seen[r['blind_item_id']] += 1
    problems += [f'REVIEW_FORM.csv: {b} appears {n} times' for b, n in sorted(seen.items()) if n > 1]
    problems += [f'REVIEW_FORM.csv: {b} is not a review item' for b in sorted(set(seen) - set(ids))]
    problems += [f'REVIEW_FORM.csv: no judgment for {b}' for b in sorted(set(ids) - set(seen))]
    frozen = {r['review_frozen_timestamp'].strip() for r in rows}
    if len(frozen) != 1 or not is_iso_timestamp(next(iter(frozen), '')):
        problems.append('REVIEW_FORM.csv: every row needs the same ISO review_frozen_timestamp')
    for r in rows:
        b = r['blind_item_id']
        for column, allowed in BR.ANSWERS.items():
            if r[column].strip() not in allowed:
                problems.append(f'REVIEW_FORM.csv {b}: {column} must be one of {", ".join(allowed)}')
        for column in ('reviewer_id', 'prior_exposure_declaration'):
            if not r[column].strip():
                problems.append(f'REVIEW_FORM.csv {b}: {column} is empty')
        if not is_iso_date(r['review_date'].strip()):
            problems.append(f'REVIEW_FORM.csv {b}: review_date must be a date like 2026-11-24')
        if r['new_problem_introduced'].strip() == 'yes' and not r['new_problem_description'].strip():
            problems.append(f'REVIEW_FORM.csv {b}: a new problem needs a description')
    by_id = {k['blind_item_id']: k['output_id'] for k in key}
    for r in rows:
        if r['blind_item_id'] in by_id and seen[r['blind_item_id']] == 1:
            judgments[by_id[r['blind_item_id']]] = {k: v.strip() for k, v in r.items()}
    return judgments


def per_output(outputs, stage2, review):
    rows = []
    for o in outputs:
        state, result = o['state'], o['result']
        label = state.label['expected_location']
        acceptable = set(state.label['acceptable_model_categories'])
        row = {c: '' for c in OUTPUT_COLUMNS}
        row.update(output_id=o['output_id'], method=o['method'], case_id=o['case_id'], sample=o['sample'],
                   status=o['status'])
        if result is not None:
            row['stop_reason'] = result['stop_reason'] or ''
            row['validators_failed'] = ';'.join(v['name'] for v in result['validators'] if v['issues'])
            row['refused_edit_reasons'] = ';'.join(r for x in result['rejected_edits'] for r in x['reasons'])
            if result['outcome'] == 'revised':
                row['new_statement'] = next(d['after']['statement'] for d in result['diff'])
        if stage2 is not None and o['status'] == 'revised':
            target = o['output_id'] if o['method'] == 'qwen' else f"{o['case_id']}:template"
            original = keys(state.report) | {k for r in stage2.get(f"{o['case_id']}:original", []) if r for k in keys(r)}
            all_reviews = stage2.get(target, [])
            reviews = [r for r in all_reviews if r is not None]
            flagged = [any(c['object_id'] == label['object_id'] and c['node_id'] == label['node_id']
                           and c['category'] in acceptable for c in r['criticisms']) for r in reviews]
            reflag = {(label['object_id'], label['node_id'], c) for c in acceptable}
            new = [sorted(keys(r) - original - reflag) for r in reviews]
            row.update(second_reviews=len(reviews), second_reviews_missing=len(all_reviews) - len(reviews),
                       second_reviews_target_flagged=sum(flagged),
                       second_reviews_with_new_objection=sum(bool(n) for n in new),
                       new_objections=';'.join(sorted({f'{a} {b} {c}' for n in new for a, b, c in n})))
        judgment = review.get(o['output_id'])
        if judgment is not None:
            row['blind_item_id'] = judgment['blind_item_id']
            for c in BR.ANSWERS:
                row[c] = judgment[c]
            row['correct_repair'] = int(judgment['defect_fixed'] == 'yes'
                                        and judgment['revised_claim_supported_by_evidence'] == 'yes'
                                        and judgment['new_problem_introduced'] == 'no'
                                        and judgment['scope_preserved'] == 'yes')
        elif o['status'] != 'revised':
            row['correct_repair'] = 0
        rows.append(row)
    return rows


def summary_row(method, metric, rows, value, weight=lambda r: 1, note=''):
    num, den = sum(value(r) for r in rows), sum(weight(r) for r in rows)
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        if r['sample'] != '':
            by[r['sample']][0] += value(r)
            by[r['sample']][1] += weight(r)
    rates = [a / b for _, (a, b) in sorted(by.items()) if b]
    return {'method': method, 'metric': metric, 'numerator': num, 'denominator': den,
            'rate': round(num / den, 4) if den else '', 'samples': len(rates),
            'mean_over_samples': round(statistics.mean(rates), 4) if rates else '',
            'sd_over_samples': round(statistics.stdev(rates), 4) if len(rates) >= 2 else '',
            'n_cases': len({r['case_id'] for r in rows}),
            'n_groups': len({GROUPS[r['case_id']] for r in rows}),
            'note': note or ('deterministic: one output per case' if method == 'template' else '')}


def summarize(rows):
    out = []
    for method in ('template', 'qwen'):
        m = [r for r in rows if r['method'] == method]
        revised = [r for r in m if r['status'] == 'revised']
        out += [summary_row(method, 'revised', m, lambda r: int(r['status'] == 'revised')),
                summary_row(method, 'abstained', m, lambda r: int(r['status'] == 'abstained')),
                summary_row(method, 'invalid', m, lambda r: int(r['status'] in INVALID)),
                summary_row(method, 'missing_or_no_reply', m, lambda r: int(r['status'] in ('missing', 'no_reply'))),
                summary_row(method, 'correct_repair', m, lambda r: int(r['correct_repair'] == 1),
                            note='all outputs; a non-revised output is not a repair'),
                summary_row(method, 'correct_repair_of_revised', revised, lambda r: int(r['correct_repair'] == 1))]
        for column, answer in (('defect_fixed', 'yes'), ('revised_claim_supported_by_evidence', 'yes'),
                               ('new_problem_introduced', 'yes'), ('scope_preserved', 'yes')):
            out.append(summary_row(method, f'{column}={answer}', revised, lambda r, c=column, a=answer: int(r[c] == a),
                                   note='revised outputs, human review'))
        reviewed = [r for r in revised if r['second_reviews'] != '']
        if reviewed:
            out.append(summary_row(method, 'second_critic_target_still_flagged', reviewed,
                                   lambda r: r['second_reviews_target_flagged'], weight=lambda r: r['second_reviews'],
                                   note='secondary; per second review'))
            out.append(summary_row(method, 'second_critic_new_objection', reviewed,
                                   lambda r: r['second_reviews_with_new_objection'], weight=lambda r: r['second_reviews'],
                                   note='secondary; per second review'))
    return out


def tables(rows, summary):
    index = {(r['method'], r['metric']): r for r in summary}

    def cell(method, metric):
        r = index.get((method, metric))
        if r is None or r['denominator'] == 0:
            return 'n/a'
        text = f"{r['numerator']}/{r['denominator']}"
        if r['mean_over_samples'] != '' and r['sd_over_samples'] != '':
            text += f" (mean {float(r['mean_over_samples']):.2f}, SD {float(r['sd_over_samples']):.2f})"
        return text
    metrics = ('revised', 'abstained', 'invalid', 'missing_or_no_reply', 'correct_repair', 'correct_repair_of_revised',
               'defect_fixed=yes', 'revised_claim_supported_by_evidence=yes', 'new_problem_introduced=yes',
               'scope_preserved=yes', 'second_critic_target_still_flagged', 'second_critic_new_objection')
    lines = ['# RQ4 tables', '', 'Generated by `experiment/score.py`. A controlled evaluation of planted-defect repair: '
             '3 planted unsupported-guarantee defects from 2 source executions (0 independent cases). Not a general '
             'measure of Revision Agent effectiveness.', '', '| Metric | Template | Qwen |', '|---|---|---|']
    lines += [f"| {m.replace('_', ' ')} | {cell('template', m)} | {cell('qwen', m)} |" for m in metrics]
    lines += ['', '## Per output', '', '| Output | Status | Fixed | Supported | New problem | Scope | Correct |',
              '|---|---|---|---|---|---|---|']
    lines += [f"| {r['output_id']} | {r['status']} | {r['defect_fixed']} | {r['revised_claim_supported_by_evidence']} | "
              f"{r['new_problem_introduced']} | {r['scope_preserved']} | {r['correct_repair']} |" for r in rows]
    return '\n'.join(lines) + '\n'


def csv_text(columns, rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def file_sha256(paths):
    return {str(Path(p)): CM.sha256_text(Path(p).read_text(encoding='utf-8')) for p in paths}


def provenance(base, args, stage1, stage2_lines):
    """What the comparison was computed from: frozen inputs, prompts, model, run files, review files."""
    def revisions(lines):
        return sorted({str(l.get('model_revision')) for l in lines if l.get('backend') == 'openai_compatible'})
    return {
        'experiment': CM.EXPERIMENT_VERSION, 'model': CM.FROZEN['model'], 'settings': CM.FROZEN,
        'stage1_model_revisions': revisions(stage1), 'stage2_model_revisions': revisions(stage2_lines),
        'revision_prompt_sha256': CM.sha256_text(CM.PROMPT_PATH.read_text(encoding='utf-8')),
        'critic_prompt_sha256': CM.sha256_text(L.PROMPT_PATH.read_text(encoding='utf-8')),
        'stage1_batch': CM.load_json(HERE / 'batch_stage1' / 'BATCH.json')['requests_sha256'],
        'stage2_batch': CM.load_json(base / 'batch_stage2' / 'BATCH.json')['requests_sha256'],
        'files_sha256': file_sha256([*args.stage1_responses, *args.stage2_responses, CM.APPROVALS_PATH,
                                     Path(args.review_dir) / 'REVIEW_FORM.csv', args.key]),
    }


def main(argv=None, allow_scripted=False):
    """allow_scripted is for tests only: the command line never accepts scripted replies as results."""
    p = argparse.ArgumentParser(prog='score.py')
    p.add_argument('--base', default=str(HERE), help='experiment folder holding results/ and the batches')
    p.add_argument('--stage1-responses', nargs='+', required=True)
    p.add_argument('--stage2-responses', nargs='+', required=True)
    p.add_argument('--review-dir', default=str(BR.REVIEW))
    p.add_argument('--key', default=str(HERE / 'sealed' / 'REVIEW_KEY.json'))
    p.add_argument('--out-dir', required=True)
    p.add_argument('--pre-review', action='store_true', help='write only per-output facts, no human judgments')
    p.add_argument('--replace-outputs', action='store_true', help='allow changing existing output files')
    args = p.parse_args(argv)
    base, out = Path(args.base), Path(args.out_dir)
    stage1 = [l for path in args.stage1_responses for l in CM.RB.read_jsonl(path)]
    stage2_lines = [l for path in args.stage2_responses for l in CM.RB.read_jsonl(path)]
    problems = []
    check_frozen_stage1(problems)
    check_stage2_files(base, stage1, allow_scripted, problems)
    outputs = [] if problems else load_outputs(base)
    stage2 = {}
    if not problems:
        check_targets(base, outputs, problems)
        stage2 = second_reviews(base, stage2_lines, allow_scripted, problems)
    review = {}
    if not problems and not args.pre_review:
        review = read_review(args.review_dir, args.key, outputs, problems)
    if problems:
        print('nothing written; problems:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1
    if args.pre_review:
        targets = {out / 'RQ4_PRE_REVIEW_FACTS.csv': csv_text(OUTPUT_COLUMNS, per_output(outputs, stage2, {}))}
    else:
        rows = per_output(outputs, stage2, review)
        summary = summarize(rows)
        targets = {out / 'RQ4_PER_OUTPUT.csv': csv_text(OUTPUT_COLUMNS, rows),
                   out / 'RQ4_SUMMARY.csv': csv_text(SUMMARY_COLUMNS, summary),
                   out / 'RQ4_TABLES.md': tables(rows, summary),
                   out / 'RQ4_PROVENANCE.json': json.dumps(provenance(base, args, stage1, stage2_lines), indent=1) + '\n'}
    try:
        CM.write_files(targets, replace=args.replace_outputs)
    except CM.ProtectedFileError as exc:
        print(f'{exc} (use --replace-outputs to change them)', file=sys.stderr)
        return 1
    print(f'{len(outputs)} outputs: ' + ('pre-review facts written' if args.pre_review else 'scored'), file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
