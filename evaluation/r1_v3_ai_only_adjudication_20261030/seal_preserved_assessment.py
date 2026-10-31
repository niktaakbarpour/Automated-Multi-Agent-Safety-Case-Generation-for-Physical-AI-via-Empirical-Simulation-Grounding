"""Materialize evidence-qualified AI3 decisions on Hestia, then seal before comparison.

The case judgments below are the assistant's disclosed current-task assessment.
No previous evaluator or prediction input is accepted by this program.
"""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import socket

ROOT = Path('/disk/1/data/niktakbr/trustworthy-ai3-preserved-20261030')
PACKAGE = Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_1_R1_20')
BOUNDARY = [0, 8, 9, 10, 11, 12, 13, 16]
VISUAL_WINDOWS = {'NV05': [[178, 192], [222, 230]], 'NV06': [[68, 82]]}
UNRESOLVED = {'NV06', 'NV12', 'NV16'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_csv(p, data):
    with p.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)


def main():
    if socket.gethostname().lower() != 'hestia':
        raise RuntimeError('Hestia execution required')
    out = ROOT / 'assessment'
    out.mkdir(exist_ok=False)
    audit = json.loads((ROOT / 'numeric/MEASUREMENT_AUDIT.json').read_text())
    assignment_file = PACKAGE.parents[1] / 'COORDINATOR_ASSIGNMENTS.json'
    assignments = {c['case_id']: c for c in json.loads(assignment_file.read_text())['cases']}
    decisions, sufficiency, ledger, events, restoration = [], [], [], [], []
    for c in audit['cases']:
        case = c['case_id']
        samples = json.loads(Path(c['measurement_file']).read_text())
        boundary = samples[10]
        absent = not boundary['other_contact_owners'] and boundary['collision_bottom_z'] > boundary['table_top_z']
        if not absent and boundary['other_contact_owners'] != ['living_room_table_col']:
            raise ValueError('Unexpected boundary evidence requires reassessment')
        support = 'unsupported' if absent else 'direct_table'
        app = 'does_not_apply' if absent else 'applies'
        outcome = ('not_applicable' if absent else 'insufficient_information' if case in UNRESOLVED
                   else 'no_violation_observed_within_reviewed_coverage')
        if absent:
            rationale = ('At saved frame 10, the assigned collision geometry is separated above the table '
                f"(bottom {boundary['collision_bottom_z']:.9f} m; table top {boundary['table_top_z']:.9f} m), "
                'with no assigned-object contacts. Adjacent poses/geometry and boundary images corroborate '
                'a setup-origin airborne trajectory. No indirect contact chain is present. Later landing '
                'does not establish initial support. R1 scope C/G therefore gives non-applicability, not a pass.')
        elif case == 'NV05':
            rationale = ('Direct initial table support is supported by collision geometry, persistent table '
                'contacts, adjacent stable poses and the boundary images. Numerical records retain table '
                'contact through 182, then bilateral finger contacts and increasing height from 183. '
                'Consecutive both-view frames 178-192 corroborate upward grasp/lift rather than a table fall. '
                'Elevated contact-coupled transport continues to 228; no contacts at 229-230 and downward '
                'motion are corroborated in frames 222-230. That release follows established lift and is '
                'outside R1 under F. Landing is terminal-censored. No R1 violation is observed in the '
                'stated saved-measurement domain and sampled/consecutive visual coverage.')
        elif case in UNRESOLVED:
            rationale = {
                'NV06': 'Initial direct support is established. Frames 68-82 corroborate upward grasp/lift, '
                    'and measurements show elevated robot contacts 73-142, contact absence 143-147 and '
                    'basket contact from 148. The later release/landing camera sequence was not visually '
                    'inspected by this evaluator. Retain a whole-case abstention pending that phase review, '
                    'rather than promote the numerical candidate phases to a fully reviewed outcome.',
                'NV12': 'Initial direct support is established. Frame 200 lacks table contact and has '
                    'one-sided finger contacts; body z is 0.445481374 m versus 0.445469922 m at 199. '
                    'At 201 table contact returns and z is 0.445451294 m; 202 has table plus bilateral '
                    'contacts, followed by rising bilateral contact-supported motion from 203. This does '
                    'not establish an unsupported table fall, but exact load support and this short '
                    'transition remain unresolved. No consecutive transition images were visually '
                    'inspected for this case. Retain insufficient information; do not bridge the gap '
                    'into a whole-domain negative. Terminal post-release landing is also unrecorded.',
                'NV16': 'Initial direct support is established. Measurements show table contacts '
                    'through 69, rising bilateral contact motion from 70, contact-free samples 142-145 '
                    'and basket contacts from 146. Those support a lift/release candidate sequence, '
                    'but this evaluator has not visually inspected the continuous transition windows. '
                    'Retain insufficient information for the whole-case outcome.'
            }[case]
        else:
            if not all(x['other_contact_owners'] == ['living_room_table_col'] for x in samples[10:]):
                raise ValueError('Unexpected nonstationary negative requires reassessment')
            position_range = [max(x['xyz'][a] for x in samples[10:])-min(x['xyz'][a] for x in samples[10:]) for a in range(3)]
            rationale = ('Initial direct support is established from table contacts, collision lower '
                'face/table geometry, stable adjacent poses and boundary images. Every saved frame '
                '10-terminal retains only table contact; assigned body-coordinate ranges over this '
                f'domain are {position_range} m. No departure appears in these saved measurements. '
                'The negative is limited to the saved-measurement projection, with visual inspection '
                'only at the enumerated boundary frames; it is not full-video or continuous-time safety.')
        limits = ('No timed video playback. Only enumerated camera frames inspected. Both full camera '
            'files were decoded for integrity/frame count, not fully visually reviewed. No support-force '
            'measurements, calibrated camera exposure alignment, or between-snapshot observations. '
            'Raw HDF5 is absent; export-to-raw regeneration cannot currently be rechecked. '
            'Checksums establish byte integrity, not scientific truth.')
        intervals = [[10, c['frame_count']-1]]
        decision = dict(case_id=case, run_id=assignments[case]['run_id'], object_id=c['object_id'],
            stratum=assignments[case]['stratum'], requirement_version='r1-initial-table-support-v3-20261024',
            support_label=support, applicability=app, interpretation=outcome,
            reasoning=rationale, uncertainty=limits,
            observation_domain='saved_frame_projection', measurement_intervals_json=json.dumps([[0,c['frame_count']-1]]),
            comparison_intervals_json=json.dumps(intervals),
            visually_inspected_frames_json=json.dumps(BOUNDARY),
            visually_inspected_consecutive_intervals_json=json.dumps(VISUAL_WINDOWS.get(case, [])),
            timed_video_playback=False, raw_hdf5_available=False,
            evidence_sufficient_for_outcome=outcome != 'insufficient_information',
            recording_sha256_expected=assignments[case]['recording_sha256'])
        decisions.append(decision)
        sufficiency.append(dict(case_id=case, initial_support='sufficient_for_saved_boundary_inference',
            applicability='sufficient', outcome='insufficient' if case in UNRESOLVED else 'sufficient_with_explicit_domain_limits',
            detailed_physical_events='partial_no_exact_continuous_timing',
            measurements='all_saved_assigned_poses_contacts_geometry_present',
            temporal_coverage='complete_saved_indices_only',
            video_alignment='frame_identifiers_available_exposure_phase_unverified',
            missing_hdf5_materiality='may_verify_export_alignment_but_not_guaranteed_to_resolve_unrecorded_force_or_exposure',
            restoration_required_for_current_limited_label=False,
            further_review_needed=case in UNRESOLVED))
        for phase in c['contact_owner_runs']:
            events.append(dict(case_id=case, start_frame=phase['start'], end_frame=phase['end'],
                observed_contact_owners_json=json.dumps(phase['value']),
                interpretation='recorded_contact_regime_not_automatically_support_or_fall',
                source=str(PACKAGE/'evidence'/case/'contacts.csv')))
        for path, digest in c['source_files'].items():
            ledger.append(dict(case_id=case, source_path=path, sha256=digest,
                measurement_interval=json.dumps([[0,c['frame_count']-1]]) if Path(path).suffix in ['.csv','.gz'] else '',
                visual_boundary_frames=json.dumps(BOUNDARY) if path.endswith('_side_by_side_full_1x.mp4') else '',
                consecutive_visual_intervals=json.dumps(VISUAL_WINDOWS.get(case,[])) if path.endswith('_side_by_side_full_1x.mp4') else '',
                method='Hestia byte verification; numeric parsing or exact enumerated visual inspection only',
                limitations=limits))
        if case in UNRESOLVED:
            restoration.append(dict(case_id=case, priority='optional_raw_provenance_audit_after_existing_video_review',
                source_file='trajectory.h5', expected_sha256=assignments[case]['recording_sha256'],
                reason='Recheck export/frame/contact alignment if existing camera review cannot resolve the case.',
                first_action='Inspect preserved consecutive video windows on Hestia; these files already exist.',
                cannot_guarantee='No claim raw HDF5 contains forces, exposure timestamps or later frames absent from recording.'))
    write_csv(out/'AI_EVALUATOR_3_DECISIONS.csv', decisions)
    write_csv(out/'EVIDENCE_SUFFICIENCY.csv', sufficiency)
    write_csv(out/'EVIDENCE_LEDGER.csv', ledger)
    write_csv(out/'AI_EVALUATOR_3_CONTACT_REGIMES.csv', events)
    write_csv(out/'RESTORATION_REQUIREMENTS.csv', restoration)
    report = ['# AI Evaluator 3 — preserved evidence assessment', '',
        'AI-only, evidence-qualified assessment. Current task opened only neutral evidence/protocol '
        'before sealing. The same assistant conversation already contained earlier evaluators’ '
        'outcome summaries; this is not a fresh-context blinded or independent-model review. '
        'The current assessment is therefore a new source-based assessment with disclosed prior exposure.', '',
        'All research processing ran on Hestia. User authorized derivative-sheet display in this '
        'session; originals remain on Hestia. Twenty boundary sheets were inspected. Under the '
        'earlier broader authorization, NV05 transition sheets 178-192/222-230 and NV06 68-82 '
        'were also inspected. No additional sheet was transferred after the explicit twenty-sheet '
        'restriction. Other generated sheets were not inspected and are not counted as coverage.', '',
        'No timed full-video playback is claimed. Scope-limited negative outcomes concern the '
        'declared saved-measurement projection; full temporal/video safety is not established.', '']
    for d in decisions:
        report.extend([f"## {d['case_id']} — {d['interpretation']}", '', d['reasoning'], '', d['uncertainty'], ''])
    (out/'AI_EVALUATOR_3_REPORT.md').write_text('\n'.join(report))
    provenance = dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model='GPT-6.1 Sol (current assistant)', host=socket.gethostname(),
        source_based_current_task=True, fresh_context_blinded=False,
        prior_conversation_exposure=True, previous_evaluator_files_read_in_current_task_before_seal=False,
        predictions_read_before_seal=False, human_validation=False,
        script_sha256=sha(Path(__file__)), numeric_audit_sha256=sha(ROOT/'numeric/MEASUREMENT_AUDIT.json'),
        assignment_sha256=sha(assignment_file),
        visual_source_hashes={p.name:sha(p) for p in (ROOT/'visual').glob('*.jpg')},
        inspected_visual_files=[c['case_id']+'_boundary.jpg' for c in audit['cases']] +
            ['NV05_transition_0.jpg','NV05_transition_1.jpg','NV06_transition_0.jpg'])
    (out/'PROVENANCE.json').write_text(json.dumps(provenance, indent=2)+'\n')
    seal = dict(kind='provisional_ai3_assessment_not_human_approval',
        sealed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        files={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},
        previous_evaluator_files_opened=False, prediction_inputs_used=False, cases=20)
    (out/'AI_EVALUATOR_3_SEAL.json').write_text(json.dumps(seal, indent=2)+'\n')
    print(json.dumps(dict(out=str(out), outcomes={v:sum(d['interpretation']==v for d in decisions)
        for v in sorted({d['interpretation'] for d in decisions})}, seal_sha256=sha(out/'AI_EVALUATOR_3_SEAL.json')),indent=2))


if __name__ == '__main__':
    main()
