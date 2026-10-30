"""Prepare/validate AI-assisted acceptance records without reading V3 predictions.

This is deliberately separate from the independent-human workflow. It cannot freeze
or score a reference. User-reported acceptance is recorded, never impersonated.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSIGNMENTS = REPO / 'evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json'
BASE = '87a8221d0c62eb62077a066f0a333de2aac4a7e5'
TABLES = ['initial_support', 'events', 'requirement_interpretation', 'uncertainty_requests']
METHOD = 'AI-assisted human verification with human adjudication'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def write_csv(path, fields, rows):
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source(n, root=HERE):
    return root / f'human_evaluator_{n}/source_ai'


def case_map():
    return {c['case_id']: c for c in load(ASSIGNMENTS)['cases']}


def data(root=HERE):
    return {n: {t: read_csv(source(n, root) / 'annotations' / (t + '.csv'))[1]
                for t in TABLES} for n in (1, 2)}


def by_case(rows, case):
    # Blank-case uncertainty requests are explicitly global, not dropped.
    return [r for r in rows if r.get('run_id') in (case, '')]


def one(rows, case):
    matches = [r for r in rows if r['run_id'] == case]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one case row: {case}')
    return matches[0]


IDENTITY = {'record_id', 'request_id', 'event_id', 'physical_event_id',
            'reviewer_copy', 'reviewer_identity', 'review_date',
            'prior_exposure_disclosure', 'scope_agreement_reference'}
DETAIL = {'reasoning', 'evidence_reasoning', 'event_description', 'visibility',
          'confidence_uncertainty', 'unresolved_questions', 'unresolved_scope_questions',
          'cannot_determine', 'additional_existing_evidence_requested'}
COVERAGE = {'review_start_frame', 'review_end_frame', 'excerpt_start_frame',
            'excerpt_end_frame', 'evidence_coverage', 'supporting_frame_references',
            'evidence_links', 'camera_measurement_references'}


def classification(case, table, field, equal):
    if equal:
        return 'exact_agreement', 'not_required'
    if table == 'requirement_interpretation' and field == 'interpretation' and case == 'NV12':
        return 'outcome_disagreement', 'resolved_by_reported_third_human_selection_only'
    if field in IDENTITY:
        return 'source_identifier_or_provenance_difference', 'retain_both'
    if field in COVERAGE:
        return 'evidence_coverage_difference', 'additional_confirmation_required'
    if field in DETAIL:
        # Similar-looking prose is not automatically declared scientifically equivalent.
        return 'descriptive_detail_or_uncertainty_difference', 'retained_not_semantically_adjudicated'
    return 'potential_substantive_or_structural_difference', 'unresolved'


def compare(root=HERE):
    """All fields, all rows. Event rows are NOT aligned by arbitrary row number.

    Each cell retains its ordered source values and source row IDs. This exposes
    one-to-many/split/merged events without inventing equivalence between them.
    """
    dd = data(root)
    result = []
    for case in sorted(case_map()):
        for table in TABLES:
            aa, bb = (by_case(dd[n][table], case) for n in (1, 2))
            fields = sorted(set().union(*(set(r) for r in aa + bb)))
            for field in fields:
                a = [r.get(field) for r in aa]
                b = [r.get(field) for r in bb]
                category, status = classification(case, table, field, a == b)
                result.append(dict(case_id=case, table=table, field=field,
                    evaluator_1_values=a, evaluator_2_values=b,
                    evaluator_1_row_ids=[r.get('event_id') or r.get('request_id') or r.get('record_id') for r in aa],
                    evaluator_2_row_ids=[r.get('event_id') or r.get('request_id') or r.get('record_id') for r in bb],
                    exact_equal=a == b, category=category, disposition=status))
        ca = load(source(1, root) / 'COVERAGE.json')[case]
        cb = next(c for c in load(source(2, root) / 'COVERAGE.json')['cases'] if c['case_id'] == case)
        # Preserve whole nested objects, including every exact frame index and method.
        result.append(dict(case_id=case, table='COVERAGE.json', field='complete_case_object',
            evaluator_1_values=ca, evaluator_2_values=cb, exact_equal=ca == cb,
            category='evidence_coverage_difference', disposition='additional_confirmation_required'))
    return result


def reference(root=HERE):
    dd = data(root)
    rows = []
    for case, assignment in sorted(case_map().items()):
        a, b = (one(dd[n]['requirement_interpretation'], case) for n in (1, 2))
        sa, sb = (one(dd[n]['initial_support'], case) for n in (1, 2))
        if a['applicability'] != b['applicability'] or sa['support_label'] != sb['support_label']:
            raise ValueError('Unexpected support/applicability disagreement requires human selection')
        if a['interpretation'] != b['interpretation'] and case != 'NV12':
            raise ValueError('Unexpected outcome disagreement requires human selection')
        rows.append(dict(case_id=case, run_id=assignment['run_id'], object_id=assignment['object_id'],
            stratum=assignment['stratum'], requirement_version=a['requirement_version'],
            support_label=sa['support_label'], applicability=a['applicability'],
            interpretation=b['interpretation'],
            selection_method='reported_third_human_selects_evaluator_2_outcome' if case == 'NV12' else 'matching_accepted_outcome_labels',
            reference_status='proposed_not_formally_approved', human_approval_status='pending',
            adjudicator_identity='', approval_date='',
            human_inspected_intervals_json='null', approved_comparison_domain='',
            source_reviewers_json=json.dumps({f'human_evaluator_{n}': {
                'authorship': 'AI', 'acceptance': 'user_reported',
                'requirement_interpretation': one(dd[n]['requirement_interpretation'], case),
                'initial_support': one(dd[n]['initial_support'], case),
                'events': by_case(dd[n]['events'], case),
                'uncertainty_requests': by_case(dd[n]['uncertainty_requests'], case),
            } for n in (1, 2)}, sort_keys=True),
            selected_nv12_ai_rationale=b['reasoning'] if case == 'NV12' else '',
            evidence_references=json.dumps({'evaluator_1': a['evidence_links'], 'evaluator_2': b['evidence_links']}),
            remaining_uncertainty='All source uncertainties retained verbatim in source_reviewers_json; physical phase alignment and actual human coverage remain unconfirmed.'))
    return rows


def event_alignment_candidates(root=HERE):
    """Navigation groups only; neither equivalence nor final timing is inferred."""
    dd = data(root)
    groups = {
        'setup_phases': {'setup_small_separation_and_return', 'setup_upward_separation',
                         'setup_airborne_descent', 'setup_unsupported_descent',
                         'table_recontact', 'table_landing_after_setup'},
        'lift': {'grasp_and_upward_lift', 'robot_lift_from_table'},
        'transport': {'robot_supported_transport'},
        'release_and_drop': {'release_and_post_lift_descent', 'gripper_release', 'post_carry_unsupported_drop'},
        'basket_contact_settling': {'basket_contact_and_settling', 'basket_landing', 'no_further_unsupported_departure_observed'},
        'table_grasp_adjustment': {'brief_support_transition_uncertain', 'grasp_adjustment_at_table'},
        'supported_motion': {'supported_displacement_and_intermittent_robot_contact', 'supported_tipping_translation_with_incidental_robot_contact'},
        'negative_windows': {'initial_supported_interval', 'no_unsupported_departure_observed', 'no_unsupported_table_departure_observed'},
    }
    result = []
    for case in sorted(case_map()):
        for group, types in groups.items():
            rows = {str(n): [r for r in dd[n]['events'] if r['run_id'] == case and r['event_type'] in types] for n in (1, 2)}
            if any(rows.values()):
                result.append(dict(case_id=case, candidate_phase_group=group, source_rows=rows,
                    approved_equivalence=False, disposition='retain_both_pending_human_phase_and_boundary_confirmation'))
    assigned_types = set().union(*groups.values())
    if any(r['event_type'] not in assigned_types for n in (1, 2) for r in dd[n]['events']):
        raise ValueError('An event type was omitted from navigation groups')
    return result


def prepare(root=HERE):
    """Only create new derived files; never rewrite original sources or approvals."""
    if (root / 'provenance.json').exists():
        raise FileExistsError('Already prepared; use validate, not a rebuild over human records')
    dd = data(root)
    for n in (1, 2):
        folder = root / f'human_evaluator_{n}'
        manifest = load(folder / 'SOURCE_MANIFEST.json')
        copied = {str(p.relative_to(source(n, root))): sha(p)
                  for p in sorted(source(n, root).rglob('*')) if p.is_file()}
        save(folder / 'acceptance.json', dict(method=METHOD, role=f'Human Evaluator {n}',
            report_received_date='2026-10-30', human_review_date=None, human_identity=None,
            authenticated_confirmation=None, source='explicit_user_report_in_task',
            reported_acceptance='all_proposed_decisions_and_annotations',
            accepted_case_ids=sorted(case_map()), ai_authorship_preserved=True,
            human_original_authorship_claimed=False, independent_annotation_claimed=False,
            human_inspected_evidence_coverage=None, ai_coverage_not_attributed_to_human=True,
            original_remote_source=manifest['source_root'], copied_file_sha256=copied,
            authoritative_physical_snapshot='annotations/physical_stage_v2' if n == 1 else 'annotations/physical_stage'))
        fields = ['case_id', 'object_id', 'reported_acceptance', 'human_identity',
                  'human_review_date', 'human_inspected_intervals_json', 'authorship', 'formal_approval']
        write_csv(folder / 'accepted_cases.csv', fields, [dict(case_id=c, object_id=v['object_id'],
            reported_acceptance='accept_all_source_proposals_per_user_report', human_identity='',
            human_review_date='', human_inspected_intervals_json='null', authorship='AI',
            formal_approval='pending') for c, v in sorted(case_map().items())])
    rr = reference(root)
    write_csv(root / 'adjudicated_reference.csv', list(rr[0]), rr)
    discrepancies = compare(root)
    save(root / 'field_comparison.json', discrepancies)
    save(root / 'discrepancies.json', [d for d in discrepancies if not d['exact_equal']])
    save(root / 'event_alignment_candidates.json', event_alignment_candidates(root))
    nv12 = next(r for r in rr if r['case_id'] == 'NV12')
    save(root / 'human_evaluator_3_adjudication/NV12.json', dict(
        method=METHOD, case_id='NV12', report_source='explicit_user_report_in_task',
        original_disagreement={str(n): one(dd[n]['requirement_interpretation'], 'NV12')['interpretation'] for n in (1, 2)},
        reported_third_human_selection='accept_human_evaluator_2_outcome',
        selected_outcome=nv12['interpretation'],
        selected_ai_requirement_row=one(dd[2]['requirement_interpretation'], 'NV12'),
        selected_ai_physical_rows=by_case(dd[2]['events'], 'NV12'),
        both_sources_uncertainties={str(n): by_case(dd[n]['uncertainty_requests'], 'NV12') for n in (1, 2)},
        rationale_source='blinded AI Evaluator 2; no distinct human rationale supplied',
        human_identity=None, human_review_date=None, human_signature=None,
        actual_human_inspected_evidence=None, formal_approval='pending',
        scope='Selects NV12 outcome only; does not resolve all physical timing, coverage or support-force differences'))
    save(root / 'provenance.json', dict(schema='r1-ai-assisted-human-verification-v1', method=METHOD,
        base_commit=BASE, report_received_date='2026-10-30',
        human_decision_source='User reports human acceptance and third-human selection in this task',
        independent_human_annotation=False, human_identity_or_signature_supplied=False,
        human_review_dates_supplied=False, human_actual_coverage_supplied=False,
        prediction_inputs_used_for_reference_selection=False,
        prediction_file_not_read_by_this_pathway=True, formal_approval=False, frozen=False,
        superseded_exposed_evaluator_2_excluded=True,
        assignment_sha256=sha(ASSIGNMENTS),
        remote_sources={str(n): load(root / f'human_evaluator_{n}/SOURCE_MANIFEST.json')['source_root'] for n in (1, 2)},
        copied_non_media_source_files={str(n): len(load(root / f'human_evaluator_{n}/acceptance.json')['copied_file_sha256']) for n in (1, 2)},
        remote_media_policy='All 718 source files hash-inventoried; non-media source files copied byte-for-byte. Original media/evidence remain on Hestia; raw relative links retain original context.',
        approved_four_recording_reference_unchanged=True))
    # These are declarations to be completed by actual humans, not endorsements.
    template = dict(schema='r1-ai-assisted-approval-v1', method=METHOD,
        approval_decision='', authorized_approver_identity='', approval_date='', approval_statement='',
        ai_assisted_nonindependent_method_acknowledged=False,
        unresolved_evidence_limits_accepted=False,
        reviewer_confirmations={str(n): dict(identity='', actual_review_date='', confirmation_statement='',
            user_report_is_accurate=None, human_inspected_evidence_description='',
            verified_human_frame_intervals_by_case={}, ai_explanations_remain_ai_authored=False) for n in (1, 2)},
        third_reviewer=dict(identity='', actual_adjudication_date='', confirmation_statement='',
            nv12_outcome_selection_confirmed=False),
        proposed_reference_sha256=sha(root / 'adjudicated_reference.csv'),
        discrepancy_report_sha256=sha(root / 'discrepancies.json'),
        source_acceptance_sha256={str(n): sha(root / f'human_evaluator_{n}/acceptance.json') for n in (1, 2)},
        comparison_domain_by_case={}, discrepancy_resolutions=[],
        note='Do not assert independent annotation. Domains and unresolved event differences require explicit decisions before freezing/scoring.')
    save(root / 'APPROVAL_TEMPLATE.json', template)
    counts = {str(n): dict(collections.Counter(r['interpretation'] for r in dd[n]['requirement_interpretation'])) for n in (1, 2)}
    summary = dict(ai_outcome_counts=counts, proposed_outcome_counts=dict(collections.Counter(r['interpretation'] for r in rr)),
        initial_support_label_agreement=20, applicability_label_agreement=20, outcome_label_agreement=19,
        total_cases=20, independent_interannotator_reliability=None,
        human_acceptance_of_ai_proposals={'evaluator_1': '20/20 user-reported', 'evaluator_2': '20/20 user-reported'},
        ai_annotation_row_counts={str(n): {t: len(v) for t, v in dd[n].items()} for n in (1, 2)},
        compared_fields=len(discrepancies), differing_fields=sum(not d['exact_equal'] for d in discrepancies),
        by_category=dict(collections.Counter(d['category'] for d in discrepancies)),
        V3_metrics=None, scoring_status='not_run_missing_formal_approval_and_confirmed_comparison_domains')
    save(root / 'comparison_summary.json', summary)
    return summary


def validate(root=HERE):
    errors = []
    cm = case_map()
    dd = data(root)
    for n in (1, 2):
        manifest = load(root / f'human_evaluator_{n}/SOURCE_MANIFEST.json')
        acceptance = load(root / f'human_evaluator_{n}/acceptance.json')
        fingerprint = hashlib.sha256(json.dumps(manifest['manifest'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        expected_fingerprint = {
            1: '96319504c00f4410cb48cbbf44db0dfc2027496a60b69adba000663631eae705',
            2: '7f3e32f2810c7ccf55707a38ff27a0f49de6acdf2d8bbc1e1cb75b64a87a0bf0',
        }[n]
        if fingerprint != expected_fingerprint:
            errors.append('Source manifest differs from intake and final remote verification')
        for name, digest in acceptance['copied_file_sha256'].items():
            p = source(n, root) / name
            if sha(p) != digest or digest != manifest['manifest'][name]['sha256']:
                errors.append(f'Source byte mismatch {n}/{name}')
        actual = {str(p.relative_to(source(n, root))) for p in source(n, root).rglob('*') if p.is_file()}
        if actual != set(acceptance['copied_file_sha256']):
            errors.append('Copied source inventory changed')
        if 'blind' not in manifest['source_root'] and n == 2:
            errors.append('Wrong evaluator 2 source')
        for table in ['initial_support', 'requirement_interpretation']:
            rows = dd[n][table]
            if len(rows) != 20 or {r['run_id'] for r in rows} != set(cm):
                errors.append(f'Missing/duplicate {n}/{table} cases')
        event_ids = [r['event_id'] for r in dd[n]['events']]
        if len(event_ids) != len(set(event_ids)):
            errors.append('Duplicate source event identifiers')
        for table, rows in dd[n].items():
            for r in rows:
                case = r.get('run_id')
                if not case and table == 'uncertainty_requests':
                    continue
                if case not in cm or r['object_id'] != cm[case]['object_id']:
                    errors.append(f'Wrong case/object {n}/{table}')
                    continue
                for field in ['boundary_frame', 'review_start_frame', 'review_end_frame',
                              'excerpt_start_frame', 'excerpt_end_frame', 'earliest_onset_frame',
                              'latest_onset_frame', 'departure_frame', 'landing_contact_frame',
                              'start_frame', 'end_frame']:
                    value = r.get(field, '')
                    if value:
                        try:
                            if not 0 <= int(value) < cm[case]['frame_count']:
                                raise ValueError()
                        except ValueError:
                            errors.append(f'Invalid temporal bound {n}/{table}/{case}/{field}')
                for lo, hi in [('review_start_frame', 'review_end_frame'), ('earliest_onset_frame', 'latest_onset_frame')]:
                    if r.get(lo) and r.get(hi) and int(r[lo]) > int(r[hi]):
                        errors.append(f'Reversed temporal bounds {n}/{table}/{case}')
        if acceptance['human_identity'] is not None or acceptance['human_review_date'] is not None or acceptance['independent_annotation_claimed']:
            errors.append('Invented human metadata')
        if acceptance['accepted_case_ids'] != sorted(cm) or acceptance['reported_acceptance'] != 'all_proposed_decisions_and_annotations' or acceptance['source'] != 'explicit_user_report_in_task' or acceptance['human_inspected_evidence_coverage'] is not None:
            errors.append('Acceptance report or coverage changed')
        accepted = read_csv(root / f'human_evaluator_{n}/accepted_cases.csv')[1]
        if len(accepted) != 20 or {r['case_id'] for r in accepted} != set(cm):
            errors.append('Accepted-case inventory incomplete')
        for r in accepted:
            if r['object_id'] != cm[r['case_id']]['object_id'] or r['human_identity'] or r['human_review_date'] or r['human_inspected_intervals_json'] != 'null' or r['authorship'] != 'AI' or r['formal_approval'] != 'pending' or r['reported_acceptance'] != 'accept_all_source_proposals_per_user_report':
                errors.append('Human acceptance row provenance changed')
        # Every tracked annotation in the prior delivered AI mirror must match too.
        mirror = REPO / f'evaluation/r1_v3_ai_assisted_reviews_20261029/ai_evaluator_{n}'
        for p in (mirror / 'annotations').rglob('*.csv'):
            if p.read_bytes() != (source(n, root) / p.relative_to(mirror)).read_bytes():
                errors.append('Source diverges from frozen delivered annotation ' + str(p))
    if read_csv(root / 'adjudicated_reference.csv')[1] != reference(root):
        errors.append('Proposed reference differs from accepted sources/selection')
    if load(root / 'field_comparison.json') != compare(root):
        errors.append('Field comparison incomplete/changed')
    if load(root / 'discrepancies.json') != [d for d in compare(root) if not d['exact_equal']]:
        errors.append('Discrepancy inventory incomplete/changed')
    if load(root / 'event_alignment_candidates.json') != event_alignment_candidates(root):
        errors.append('Event navigation groups incomplete/changed')
    nv = load(root / 'human_evaluator_3_adjudication/NV12.json')
    if nv['selected_ai_requirement_row'] != one(dd[2]['requirement_interpretation'], 'NV12'):
        errors.append('NV12 selection/rationale changed')
    if nv['selected_ai_physical_rows'] != by_case(dd[2]['events'], 'NV12'):
        errors.append('NV12 detailed source rows changed')
    if nv['both_sources_uncertainties'] != {str(n): by_case(dd[n]['uncertainty_requests'], 'NV12') for n in (1, 2)}:
        errors.append('NV12 uncertainties missing/changed')
    if any(nv[k] is not None for k in ['human_identity', 'human_review_date', 'human_signature', 'actual_human_inspected_evidence']) or nv['formal_approval'] != 'pending':
        errors.append('Invented adjudicator approval metadata')
    provenance = load(root / 'provenance.json')
    if provenance['assignment_sha256'] != sha(ASSIGNMENTS) or any(provenance[k] is not False for k in ['independent_human_annotation', 'formal_approval', 'frozen', 'prediction_inputs_used_for_reference_selection']):
        errors.append('Provenance or assignment changed')
    expected_counts = {'not_applicable': 12, 'no_violation_observed_within_reviewed_coverage': 8}
    if dict(collections.Counter(r['interpretation'] for r in reference(root))) != expected_counts:
        errors.append('Unexpected proposed distribution')
    approval = load(root / 'APPROVAL_TEMPLATE.json')
    if approval['proposed_reference_sha256'] != sha(root / 'adjudicated_reference.csv') or approval['discrepancy_report_sha256'] != sha(root / 'discrepancies.json'):
        errors.append('Approval template not bound to current proposal')
    if approval['approval_decision'] or approval['authorized_approver_identity'] or approval['approval_date']:
        errors.append('Blank approval template was overwritten')
    summary = load(root / 'comparison_summary.json')
    if summary['V3_metrics'] is not None or summary['independent_interannotator_reliability'] is not None or summary['proposed_outcome_counts'] != expected_counts:
        errors.append('Unapproved metrics or changed summary')
    return dict(passed=not errors, errors=errors, cases=20,
        source_files_verified=sum(len(load(root / f'human_evaluator_{n}/acceptance.json')['copied_file_sha256']) for n in (1, 2)),
        remote_files_inventoried=sum(len(load(root / f'human_evaluator_{n}/SOURCE_MANIFEST.json')['manifest']) for n in (1, 2)),
        formally_approved=False, reference_frozen=False, V3_scored=False)


def check_approval(path, root=HERE):
    """Check declarations only; cannot authenticate signers, freeze, or read predictions."""
    result = validate(root)
    if not result['passed']:
        raise ValueError(result['errors'])
    approval = load(path)
    template = load(root / 'APPROVAL_TEMPLATE.json')
    for key in ['schema', 'method', 'proposed_reference_sha256', 'discrepancy_report_sha256', 'source_acceptance_sha256']:
        if approval.get(key) != template[key]:
            raise ValueError('Approval binding mismatch: ' + key)
    for n, digest in template['source_acceptance_sha256'].items():
        if sha(root / f'human_evaluator_{n}/acceptance.json') != digest:
            raise ValueError('Acceptance changed since approval template')
    if approval.get('approval_decision') != 'approve' or any(not approval.get(k, '').strip() for k in ['authorized_approver_identity', 'approval_date', 'approval_statement']):
        raise ValueError('Missing authorized human approval declaration')
    if approval.get('ai_assisted_nonindependent_method_acknowledged') is not True or approval.get('unresolved_evidence_limits_accepted') is not True:
        raise ValueError('Method/limitations not explicitly accepted')
    identities = []
    for n in ('1', '2'):
        c = approval.get('reviewer_confirmations', {}).get(n, {})
        if any(not c.get(k, '').strip() for k in ['identity', 'actual_review_date', 'confirmation_statement', 'human_inspected_evidence_description']) or c.get('user_report_is_accurate') is not True or c.get('ai_explanations_remain_ai_authored') is not True:
            raise ValueError('Missing human reviewer confirmation: ' + n)
        identities.append(c['identity'].strip())
    third = approval.get('third_reviewer', {})
    if any(not third.get(k, '').strip() for k in ['identity', 'actual_adjudication_date', 'confirmation_statement']) or third.get('nv12_outcome_selection_confirmed') is not True:
        raise ValueError('Missing third-reviewer confirmation')
    if len(set(identities + [third['identity'].strip()])) != 3:
        raise ValueError('Three distinct reported human roles require confirmed identities')
    # Do not auto-approve time/coverage/phase mismatches or silently treat prose as equivalent.
    pending = {f"{d['case_id']}:{d['table']}:{d['field']}" for d in load(root / 'discrepancies.json')
               if d['disposition'] in ['unresolved', 'additional_confirmation_required', 'retained_not_semantically_adjudicated']}
    decisions = approval.get('discrepancy_resolutions', [])
    seen = set()
    for d in decisions:
        key = d.get('discrepancy_id')
        if key in seen or key not in pending or d.get('decision') not in ['retain_both_unscorable', 'descriptive_only_confirmed', 'selected_source_1', 'selected_source_2'] or not d.get('human_reason', '').strip():
            raise ValueError('Invalid/duplicate/unexplained discrepancy resolution')
        seen.add(key)
    if seen != pending:
        raise ValueError('Unresolved physical/coverage/detail discrepancies require explicit disposition')
    domains = approval.get('comparison_domain_by_case', {})
    if set(domains) != set(case_map()):
        raise ValueError('All 20 comparison domains need explicit human decisions')
    for case, d in domains.items():
        if d.get('status') == 'unscorable' and d.get('reason', '').strip():
            continue
        if d.get('status') != 'approved_saved_frame_projection' or not d.get('reason', '').strip() or not d.get('intervals'):
            raise ValueError('Missing/invalid approved domain: ' + case)
        for pair in d['intervals']:
            if len(pair) != 2 or any(type(x) is not int for x in pair) or not 10 <= pair[0] <= pair[1] < case_map()[case]['frame_count']:
                raise ValueError('Invalid domain bounds: ' + case)
    return dict(declaration_complete=True, authenticated_by_software=False, frozen=False,
                scoring_permitted_by_this_tool=False,
                next='Verify human declarations through the coordinator; review a separate AI-assisted freeze/scoring adapter before execution. The independent-human CLI remains inapplicable.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'validate', 'check-approval'])
    parser.add_argument('--approval', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare()
    elif args.command == 'validate':
        result = validate()
    else:
        if not args.approval:
            parser.error('--approval required')
        result = check_approval(args.approval)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get('passed') is False:
        raise SystemExit(1)
