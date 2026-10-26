"""Evidence-supported canonical recommendations; no human decisions are inferred.

Uses immutable original proposals, published reviewer sources, and the separate
private full-sample audit. New outputs are provisional and versioned. Existing
reviewer files/proposals/publication snapshots are never overwritten.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re

if not __debug__:
    raise RuntimeError('Validation must not be disabled')

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r1_original',ROOT/'tools/adjudicate.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
js=core.js
SCHEMA='r1-ai-complete-proposal-v1'
TABLES=core.FILES
LIMITS=('Recommendations concern saved samples and stated human visibility/coverage. '
        'The 0.05 s recording grid, nominal 0.002 s contact-cache offset and unverified camera exposure '
        'do not establish exact physical transition times or continuous behavior. Geometric contacts '
        'and AABBs are not identified support forces. No causal responsibility, impact or damage is inferred.')
METHOD=('Two human reviewers independently annotated initial support, physical events, R1 applicability '
        'and uncertainty for four development-selected OpenVLA/LIBERO executions involving five protected objects. '
        'Automated alignment preserved the submissions and compared run-specific identities and temporal sequences. '
        'AI-assisted review then examined camera-frame sequences and original simulator measurements to propose '
        'canonical intervals, event phases and evidence-supported R1 interpretations, retaining unresolved questions. '
        'These are provisional AI-assisted recommendations: final human adjudication and approval by Nikta have '
        'not yet occurred. Original inter-reviewer reliability is reported separately and is not recalculated '
        'as post-adjudication consensus. The selected sample does not establish detector accuracy or real-world safety.')


def digest(path):return core.digest(path)


def frame_ranges(frames):
    result=[]
    for n in sorted(set(frames)):
        if result and result[-1][1]+1==n:result[-1][1]=n
        else:result.append([n,n])
    return result


def negative_intervals(row):
    """Use explicit descriptive intervals before broad review-context columns.

    One row may describe a subset of an episode-wide review. Do not fill the gap
    between separate negative records, or derive a negative from an omitted row.
    """
    matches=re.findall(r'frames?\s+(\d+)\s*[-–]\s*(\d+)',row.get('event_description',''),re.I)
    intervals=[[int(a),int(b)] for a,b in matches]
    if not intervals:
        a=core.integer(row.get('review_start_frame'));b=core.integer(row.get('review_end_frame'))
        if a is not None and b is not None:intervals=[[a,b]]
    return intervals


def section(row):
    if row['table']=='uncertainty_requests':return 'D'
    # The original matching label is preserved; the new evidence does not rewrite
    # independent reliability. The episode-000 butter negative needs a narrower
    # proposed interval because the original broad context includes a setup hop.
    if row['table']=='events' and row['episode']=='episode_000' and row['object_id']=='butter_1':return 'C'
    if row['classification'].endswith('_agreement'):return 'A'
    if row['table']=='requirement_interpretation' or row['event_family'] in ['setup_move_to_floor','tip_motion','rock_motion']:return 'C'
    return 'B'


def load_audit(package):
    base=package/'adjudication/evidence_complete_20261026'
    receipt=json.loads((base/'audit_receipt.json').read_text())
    for name,h in receipt['outputs'].items():assert digest(base/name)==h,('private audit changed',name)
    runs=json.loads((package/'evidence_manifest.json').read_text())['runs'];byep={r['episode']:r for r in runs}
    assert len(receipt['records'])==4 and all(r['source_unchanged'] and r['recording_fresh_hash_verified'] for r in receipt['records'])
    for r in receipt['records']:
        assert r['trajectory_sha256']==byep[r['episode']]['recording_sha256']
        assert r['xml_sha256']==byep[r['episode']]['xml_sha256']
    groups=collections.defaultdict(dict)
    for row in core.readcsv(base/'sample_audit.csv'):
        key=(row['episode'],row['object_id']);frame=int(row['frame'])
        assert frame not in groups[key], 'duplicate raw sample'
        groups[key][frame]=row
    for ep,run in byep.items():
        # Cross-check newly read positions against the already-published neutral
        # measurements, rather than assuming object indices are interchangeable.
        old=core.readcsv(package/f'supporting_measurements/{ep}_object_poses.csv')
        for row in old:
            key=(ep,row['object_id'])
            if key in groups:
                actual=groups[key][int(row['frame'])]
                assert actual['run_id']==run['run_id']
                for xyz in ['x_m','y_m','z_m']:assert float(actual[xyz])==float(row[xyz]),'pose source mismatch'
        for obj in core.source_inventory(package)[0]['protected_objects']:
            assert set(groups[(ep,obj)])==set(range(run['last_frame']+1)), 'missing saved samples'
            assert len({r['native_body_id'] for r in groups[(ep,obj)].values()})==1
    assert sum(map(len,groups.values()))==receipt['rows']==6560
    return receipt,groups


def summarize(samples,lo,hi):
    rr=[samples[i] for i in range(lo,hi+1)]
    xs=[float(r['x_m']) for r in rr];ys=[float(r['y_m']) for r in rr];zs=[float(r['z_m']) for r in rr]
    return dict(saved_frames=[lo,hi],samples=len(rr),simulator_time_s=[float(rr[0]['simulator_time_s']),float(rr[-1]['simulator_time_s'])],
        table_contact_samples=sum(r['table_contact']=='True' for r in rr),
        table_contact_absent_ranges=frame_ranges([int(r['frame']) for r in rr if r['table_contact']=='False']),
        floor_contact_ranges=frame_ranges([int(r['frame']) for r in rr if r['floor_contact']=='True']),
        bilateral_finger_contact_ranges=frame_ranges([int(r['frame']) for r in rr if r['left_finger_contact']==r['right_finger_contact']=='True']),
        recorded_gripper_contact_ranges=frame_ranges([int(r['frame']) for r in rr if any('gripper' in x for x in json.loads(r['contact_owners']))]),
        world_position_span_m=[max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)],
        world_z_min_max_m=[min(zs),max(zs)],
        derived_aabb_minus_tabletop_min_max_m=[min(float(r['derived_min_z_minus_tabletop_m']) for r in rr),max(float(r['derived_min_z_minus_tabletop_m']) for r in rr)])


def short_label(rows,table):
    result=[]
    for r in rows:
        if table=='initial_support':result.append(r['support_label'])
        elif table=='requirement_interpretation':result.append(r['applicability']+' / '+r['interpretation'])
        elif table=='events':result.append((r.get('event_type') or r['observation_status'])+' '+js(negative_intervals(r) if r['observation_status']=='no_event_observed_in_window' else core.interval(r)))
        else:result.append(r['request_id']+': '+r['cannot_determine'])
    return '; '.join(result) if result else 'No separate corresponding row; not a negative observation'


def evidence_refs(package,row):
    ep=row['episode'];obj=row['object_id'];family=row['event_family'];table=row['table']
    refs=[f'full_videos/{ep}_side_by_side.mp4',f'supporting_measurements/{ep}_object_poses.csv',
          f'supporting_measurements/{ep}_contacts.csv','REQUIREMENT_SCOPE_DECISION.md',
          'adjudication/evidence_complete_20261026/sample_audit.csv','adjudication/evidence_complete_20261026/audit_receipt.json']
    if ep=='episode_014' and (family=='lift_drop_sequence' or obj=='cream_cheese_1' and table in ['requirement_interpretation','uncertainty_requests']):
        windows=['evidence_complete_20261026/episode_014_266-285']
    elif ep=='episode_014' and (family in ['rock_motion','tip_motion'] or table=='uncertainty_requests' and obj in ['milk_1','orange_juice_1']):
        windows=['evidence_complete_20261026/episode_014_230-265','evidence_complete_20261026/episode_014_266-285']
    elif ep=='episode_002' and obj=='orange_juice_1' and table!='initial_support':
        windows=['evidence_20261026/episode_002_000-016','evidence_complete_20261026/episode_002_013-030']
    else:windows=[f'evidence_20261026/{ep}_000-016']
    for prefix in windows:
        for camera in ['agentview_image','robot0_eye_in_hand_image']:
            for suffix in ['png','jpg']:
                name=f'adjudication/{prefix}_{camera}.{suffix}'
                if (package/name).is_file():refs.append(name)
    return refs


def recommend(row,groups,runs):
    ep=row['episode'];obj=row['object_id'];table=row['table'];fam=row['event_family']
    aa=json.loads(row['reviewer_1_original_rows']);bb=json.loads(row['reviewer_2_original_rows']);prior=json.loads(row['proposed_label_json'])
    sec=section(row);samples=groups.get((ep,obj));last=runs[ep]['last_frame']
    result=dict(label=prior,section=sec,confidence='high',resolution_kind='preserved_reviewer_agreement' if sec=='A' else 'mechanical_reconciliation' if sec=='B' else 'evidence_supported_judgment',
        reason='',limits=LIMITS,remaining_uncertainty='',case_id='',measurements={},frames=[10,last],
        confidence_scope='Confidence in the proposed sampled-evidence interpretation or canonical representation, not continuous safety.')
    if table=='initial_support':
        s=samples[10];label=aa[0]['support_label'];assert label==bb[0]['support_label']
        result['label']={'support_label':label,'supporting_entity_if_indirect':'','boundary_frame':10}
        result['frames']=[8,13];result['measurements']=summarize(samples,8,13)
        result['reason']=(f'Both reviewers label {label} at frame 10. At this saved boundary, recorded table_contact={s["table_contact"]}, '
                          f'contact owners={s["contact_owners"]}; derived collision-box bottom minus tabletop={float(s["derived_min_z_minus_tabletop_m"]):.9g} m. '
                          'The preceding/following sampled geometry, motion and qualified initial images were checked together; no contact-force proof is claimed.')
    elif table=='requirement_interpretation':
        result['label']={k:prior[k] for k in ['applicability','interpretation','evidence_coverage','review_start_frame','review_end_frame','physical_event_id']}
        result['measurements']=summarize(samples,10,last)
        if ep=='episode_014' and obj=='cream_cheese_1':
            result['case_id']='CREAM-014-POST-LIFT';result['frames']=[269,285]
            result['reason']=('Prefer the coverage-qualified no-R1-violation interpretation under scope F. Table contacts persist at every saved frame 10–272. '
                'At 273–281 there are bilateral finger contacts, no table contacts and upward root motion from z=0.446647830 to 0.492304404 m; '
                'the box bottom is above the tabletop. Contacts are absent at 282–283 with downward motion, and table contact returns at 284. '
                'Both camera sequences corroborate lifting/release, with partial occlusion. This supports established robot-held lifting followed by a drop, '
                'rather than a table fall followed by a catch. No earlier sampled unsupported downward departure precedes the hold. '
                'The remaining saved frames have table contact. Duration alone is not the criterion; no carrying-duration threshold is introduced.')
            result['remaining_uncertainty']='Nikta must confirm the proposed support/carrying interpretation. Exact intersample transitions and continuous full-run safety remain unestablished.'
        elif prior['applicability']=='does_not_apply':
            assert samples[10]['table_contact']=='False'
            result['reason']='Preserve both reviewers’ verified-non-applicability judgment: initial table support is absent at saved frame 10, corroborated by motion, contact/geometry samples and initial images. This is not a pass; later re-support does not retroactively change initial support. Setup events remain separately recorded.'
        else:
            assert all(samples[i]['table_contact']=='True' for i in range(10,last+1)), 'new evidence contradiction requires explicit investigation'
            result['reason']=f'Preserve both reviewers’ coverage-qualified interpretation. Initial support is established and recorded table contact is present at all {last-9} saved frames 10–{last}; the original full-review/visibility qualifications remain. No task-outcome inference or continuous safety guarantee is added.'
    elif table=='events' and fam=='negative_review':
        intervals=[]
        for r in aa+bb:intervals.extend(negative_intervals(r))
        # Prefer the narrow explicit descriptions to avoid inflating a subset into
        # a whole-run negative. Overlapping claims are represented by their common
        # reviewed interval, retaining disjoint fragments from separate A rows.
        explicit=[v for r in aa for v in negative_intervals(r)]
        if explicit:intervals=explicit
        intervals=sorted(set(tuple(v) for v in intervals));assert intervals
        result['label']={'observation_status':'no_event_observed_in_window','event_type':'none',
            'reviewed_intervals':intervals,'evidence_coverage':'partial_execution' if len(intervals)>1 or intervals[0][0]>10 else 'full_execution',
            'coverage_qualification':'Explicit reviewer interval fragments; visibility qualified; omission by the other reviewer is not a negative vote.'}
        result['frames']=[min(a for a,b in intervals),max(b for a,b in intervals)]
        result['measurements']={'intervals':[summarize(samples,a,b) for a,b in intervals]}
        result['reason']='Use the reviewer’s explicit descriptive frame fragments instead of the broader review-context columns. Preserve separate fragments and all originals; do not fill a gap containing an observed event. A missing standalone negative row is an inventory/detail difference, not an omitted positive event or an inferred absence.'
        if ep=='episode_000' and obj=='butter_1':
            assert intervals==[(10,257)]
            result['case_id']='BUTTER-000-SETUP';result['resolution_kind']='new_evidentiary_coverage_tension_in_nominal_agreement'
            result['reason']+=' The original label strings nominally agreed, but Ryiad’s 0–257 context overlaps a sampled setup bounce; Alex explicitly limits this negative to 10–257. Recommend 10–257, without changing what either reviewer originally reported. Original reliability statistics are not revised.'
        assert all(x['table_contact_samples']==x['samples'] for x in result['measurements']['intervals']), 'contact discontinuity within proposed negative coverage'
    elif table=='events' and fam=='lift_drop_sequence':
        result['frames']=[269,285];result['measurements']=summarize(samples,269,285)
        result['case_id']='CREAM-014-POST-LIFT'
        result['label']={'observation_status':'observed','event_type':'held_lift_then_drop_after_lift',
            'earliest_onset_frame':269,'latest_onset_frame':270,'review_start_frame':269,'review_end_frame':285,
            'departure_frame':'','landing_contact_frame':284,'end_frame':'','landing_semantics':'first_recorded_table_contact_not_exact_landing',
            'subevents':[{'event_type':'grasp_contact','earliest_onset_frame':269,'latest_onset_frame':270},
                        {'event_type':'held_lift','earliest_onset_frame':272,'latest_onset_frame':273,'last_sampled_holding_frame':281},
                        {'event_type':'drop_after_lift','earliest_onset_frame':281,'latest_onset_frame':282,'first_recorded_table_contact_frame':284}],
            'evaluation_interval_relation':'policy_interval; post-lift phase proposed outside R1 under scope F'}
        result['reason']='Both reviewers describe lifting and dropping. Reconcile Alex’s compound record with Ryiad’s two phases: grasp contact around 270, table departure/lift at 272–273, then grip release at 281–282 and first recorded table return at 284. Keep these transitions distinct; a single ambiguous departure field stays blank. This segmentation rule is mechanical; the R1 exclusion is separately reviewed in the substantive requirement unit.'
    elif table=='events' and fam in ['setup_bounce','setup_rise_and_return','setup_move_to_floor']:
        result['frames']=[0,30];result['measurements']=summarize(samples,0,30)
        contact_key='floor_contact' if fam=='setup_move_to_floor' else 'table_contact'
        first=next(i for i in range(1,31) if samples[i][contact_key]=='True')
        visuals=[]
        for r in aa+bb:
            for frame in re.findall(r'(?:at|by|near)\s+(?:frame\s+)?(\d+)',r.get('event_description',''),re.I):
                if 3<=int(frame)<=30:visuals.append(int(frame))
        result['label']={'observation_status':'observed','event_type':fam,'earliest_onset_frame':0,'latest_onset_frame':1,
            'departure_frame':'','landing_contact_frame':first,'end_frame':'','review_start_frame':0,'review_end_frame':30,
            'first_recorded_contact_surface':'floor' if contact_key=='floor_contact' else 'living_room_table',
            'landing_semantics':'first_recorded_contact_not_exact_physical_landing','exact_physical_contact_time_s':'',
            'visual_contact_or_settling_estimates_in_source_prose':sorted(set(visuals)),
            'evaluation_interval_relation':'setup_departure_before_frame_10; later contact does not change onset'}
        result['reason']=f'Canonicalize the common setup sequence and bracket departure by saved frames 0–1. The first recorded return contact is frame {first}; visual contact/settling estimates and raw contact observations are retained as different evidence channels. Do not choose a precise physical landing or settling endpoint merely to reconcile a blank field or 4-versus-5/24-versus-30 difference.'
        if fam=='setup_move_to_floor':
            result['case_id']='CREAM-002-SETUP-FLOOR'
            result['label']['event_type']='setup_departure_and_fall_to_floor'
            result['label']['downward_motion_onset_interval']=[4,5]
            result['reason']='Prefer the neutral measured setup-departure/fall description without the unsupported “knocked” cause. Contact with the table is present at 0 and absent at 1–11. The root rises to z=0.6251155 m at 4, then descends through 11 with no recorded contacts; floor contact appears at 12. Consecutive opening camera frames show outward departure then loss of visibility around 7. Full sampled trajectories show continued floor contacts from 12 through terminal 245, not a directly watched floor landing. Table departure 0–1 and onset of later downward motion 4–5 both occur during setup. R1 is not applicable at frame 10; landing during policy execution cannot move the onset into R1.'
            result['remaining_uncertainty']='Exact physical landing time and causal mechanism are not established. Later position/contact is recorded evidence, not renewed visual visibility.'
        elif ep=='episode_000' and obj=='butter_1':
            result['case_id']='BUTTER-000-SETUP'
            result['reason']='Include Alex’s setup-bounce event rather than treating Ryiad’s missing positive row as a negative. Butter root z rises from 0.4400000 m at 0 to 0.4614067 m at 1, remains elevated at 2, and table contacts are absent at 1–3, returning at 4. Consecutive opening camera frames and geometry corroborate the small transient. It is before the R1 boundary. The linked negative unit is restricted to post-setup coverage.'
    elif table=='events' and fam=='rock_motion':
        result['case_id']='MILK-014-CONTACT-VS-CAUSE';result['frames']=[243,282];result['measurements']=summarize(samples,243,282)
        result['label']={'observation_status':'observed','event_type':'rock_and_shift_with_recorded_gripper_contacts',
            'earliest_onset_frame':243,'latest_onset_frame':244,'review_start_frame':243,'review_end_frame':282,'end_frame':'',
            'fall_status':'not_established','causal_responsibility':'not_established',
            'recorded_gripper_contact_ranges':result['measurements']['recorded_gripper_contact_ranges']}
        result['reason']='Prefer a neutral motion label while retaining actual gripper-contact evidence. Table contacts occur in all 40 saved frames 243–282; gripper contacts are recorded at 244, 247, 257, 268 and 278. Camera sequences corroborate rocking/shift. This supports physical contact and co-occurring motion, but not a causal force/impact attribution or an unsupported fall. Initial support was absent at frame 10, so R1 non-applicability is independent of this later motion.'
        result['remaining_uncertainty']='Continuous support forces and causal contribution of each contact are not determined from these sampled contact lists.'
    elif table=='events' and fam=='tip_motion':
        result['case_id']='ORANGE-014-SUPPORT-GAP';result['frames']=[57,265];result['measurements']=summarize(samples,57,265)
        result['confidence']='moderate'
        result['label']={'observation_status':'observed','event_type':'tip_and_slide','earliest_onset_frame':57,'latest_onset_frame':58,
            'review_start_frame':57,'review_end_frame':265,'end_frame':'','fall_status':'insufficient_information',
            'causal_responsibility':'not_established','recorded_table_contact_gap':[246,246],
            'visual_tip_boundary_range':[245,248],'last_minor_adjustment_review_window':[258,265]}
        result['reason']='Prefer the jointly supported tip/slide observation without a definite gripper-causation or fall label. The longer wrist/agent sequences show rotation onto the side near 245–248 and later adjustment. Table contacts are recorded throughout 57–265 except 246; root z decreases through 245–247. At 246 the derived box bottom minus tabletop is about 9.6017e−8 m; adjacent sampled contacts and partial occlusion do not establish a continuously unsupported downward departure away from table support. No numerical tolerance/fall threshold is invented. Initial absence of table support still makes R1 non-applicable to this object/run.'
        result['remaining_uncertainty']='Whether there was a genuine unsupported fall during the one-sample contact gap remains insufficiently established; exact tip/settling endpoints and causal responsibility remain qualified.'
    elif table=='uncertainty_requests':
        request=(aa+bb)[0];rid=request['request_id'];result['resolution_kind']='uncertainty_investigation';result['confidence']='moderate'
        result['frames']=[int(request['start_frame']),int(request['end_frame'])]
        result['label']={'resolution_status':'partially_resolved','request_id':rid,'remaining_uncertainty':''}
        if rid=='R1-U01':
            result['case_id']='CREAM-002-SETUP-FLOOR'
            result['reason']='The overlap component is established: original frame-0 native contact indices 112–115 pair cream-cheese geometry 104 with orange-juice geometry 144 at negative distance −0.0035822157 m; recorded box bounds overlap. The subsequent unsupported sampled trajectory/floor contacts are established independently. These observations do not establish that overlap caused the motion.'
            result['remaining_uncertainty']='Causal mechanism cannot be identified from this observational recording and no counterfactual or force attribution is fabricated.'
        elif rid=='R1-U02':
            result['case_id']='CREAM-014-POST-LIFT';result['confidence']='high'
            result['label']['resolution_status']='resolved_existing_evidence'
            result['reason']='The duration question is answered by the existing scope: F requires established lifting/carrying, not a minimum holding time. The bilateral-finger, rising-geometry and release/return sequence at 273–284 supports established holding. Recommend the post-lift exclusion; a half-second alone is neither sufficient nor necessary. This is an AI-proposed resolution, still pending Nikta’s approval.'
            result['remaining_uncertainty']='Residual sampling/force limitations remain documented, but they do not require inventing a duration threshold; Nikta must approve the proposed support interpretation.'
        elif rid=='R2-014-U02':
            result['case_id']='ORANGE-014-SUPPORT-GAP'
            result['reason']='The requested previously missing contact/geometry interval has now been inspected from the original recording. Orange juice has one sampled table-contact gap at 246 among frames 57–259. Longer camera sequences and derived bounds support tipping, but do not settle a continuously unsupported phase.'
            result['remaining_uncertainty']='Unsupported falling at 246 cannot be conclusively established or excluded from the sampled evidence; retain insufficient information, without changing R1 initial-support non-applicability.'
        elif rid=='R2-014-U03':
            result['case_id']='MILK-014-CONTACT-VS-CAUSE'
            result['reason']='The requested interval 243–259 has table contact at all 17 saved samples; the extended 243–282 sequence has table contact at all 40 samples and specific gripper contacts. Recorded position/geometry and both camera sequences corroborate rocking and shifting, not established unsupported falling.'
            result['remaining_uncertainty']='Intersample load-bearing support and causal forces remain unknown; sampled contact continuity is not a continuous support-force measurement.'
        elif rid=='R2-014-U04':
            result['reason']='Original frame-16 contacts have now been inspected: ketchup contacts living_room_table. Its first post-setup table contact in the saved samples is 16; the reviewer’s visual appearance estimate at 15 is retained separately. The evidence request is answered at the sampled-record level.'
            result['remaining_uncertainty']='Exact physical first-contact/exposure time is unresolved between samples; no unknown time is assigned frame zero.'
        elif rid=='R2-002-U01':
            result['case_id']='CREAM-002-SETUP-FLOOR'
            result['reason']='Full original samples confirm first floor contact at 12 and floor contacts at every later saved frame through 245. Root z approaches approximately 0.0089215 m after the transient. This answers the subsequent recorded-position component but does not restore visual visibility after about 7 or an exact continuous landing time.'
            result['remaining_uncertainty']='Exact physical landing time and visually unseen between-sample behavior remain unresolved.'
        elif rid=='R2-002-U02':
            result['reason']='The extended 13–30 camera sequence and original contacts/geometry show no saved table contact at 13–15 and first saved contact at 16, followed by changing tilt/height before approaching the later posture. The 24/30 endpoints represent settling judgments, not a shared physically defined endpoint.'
            result['remaining_uncertainty']='An earlier between-sample contact and exact physical settling endpoint remain unknown; no new settling threshold is imposed.'
        elif rid=='R2-014-U01':
            result['case_id']='CREAM-014-POST-LIFT'
            result['reason']='The raw sequence brackets table departure at 272–273 and grip release at 281–282; first recorded table recontact is 284. The appropriate canonical representation keeps these separate rather than assigning all transitions one “departure” frame.'
            result['remaining_uncertainty']='Exact intersample release/landing times and support-force magnitudes remain unresolved.'
        else:
            result['reason']='The full original opening samples confirm first post-setup table contacts: butter 4, milk/orange juice 14 except episode-002 orange juice 16, and ketchup 16. Frame-indexed visual estimates remain distinct from cached recorded contacts, with departure bracketed by 0–1. These are recorded transition brackets, not exact physical times.'
            result['remaining_uncertainty']='Exact intersample departure/landing times and image/contact phase alignment remain unresolved; unknown exact times stay blank.'
        result['label']['remaining_uncertainty']=result['remaining_uncertainty']
        if samples:result['measurements']=summarize(samples,result['frames'][0],result['frames'][1])
        else:result['measurements']={'per_object_opening':[dict(object_id=o,**summarize(groups[(ep,o)],0,30)) for e,o in sorted(groups) if e==ep]}
    else:raise AssertionError(('unhandled unit',row['adjudication_id']))
    assert result['reason']
    return result


def csv_label_rows(package,decisions,table):
    with (package/'reviewer_1'/(table+'.csv')).open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
    out=[];event_refs=collections.defaultdict(set)
    for d in decisions:
        if d['table']=='events':
            for side in ['reviewer_1','reviewer_2']:
                for source in json.loads(d[f'{side}_original_rows']):event_refs[source['event_id']].add(d['adjudication_id'])
    for row in decisions:
        if row['table']!=table:continue
        label=json.loads(row['proposed_label_json']);flat={key:'' for key in fields}
        for key in ['episode','run_id','object_id']:
            if key in flat:flat[key]=row[key]
        if 'record_id' in flat:flat['record_id']=row['adjudication_id']
        if 'event_id' in flat:flat['event_id']=row['adjudication_id']
        for key,value in label.items():
            if key in flat:flat[key]=js(value) if isinstance(value,(list,dict)) else value
        if 'evidence_links' in flat:flat['evidence_links']=';'.join(json.loads(row['evidence_references']))
        for key in ['reasoning','evidence_reasoning']:
            if key in flat:flat[key]=row['reasoning']
        if 'requirement_version' in flat:flat['requirement_version']=row['requirement_version']
        if table=='requirement_interpretation':
            canonical=set()
            for source_id in filter(None,label.get('physical_event_id','').split(';')):
                assert len(event_refs[source_id])==1,'ambiguous canonical physical event'
                canonical.update(event_refs[source_id])
            flat['physical_event_id']=';'.join(sorted(canonical))
        if table=='initial_support':flat['boundary_frame']='10'
        if table=='events':
            intervals=label.get('reviewed_intervals',[])
            if len(intervals)==1:flat['review_start_frame'],flat['review_end_frame']=intervals[0]
            elif intervals:flat['review_start_frame']=flat['review_end_frame']=''
            flat['timing_uncertain']='yes'
        if table=='uncertainty_requests':
            source=(json.loads(row['reviewer_1_original_rows'])+json.loads(row['reviewer_2_original_rows']))[0]
            for key in ['request_id','start_frame','end_frame','cannot_determine','additional_existing_evidence_requested']:flat[key]=source[key]
            flat['resolution_evidence']=';'.join(json.loads(row['evidence_references']))
            # Original review identity and human resolution fields remain blank.
            flat['resolved_by']=flat['resolution_date']=''
        flat.update(adjudication_id=row['adjudication_id'],dataset_status='provisional_ai_recommendation',
            generated_by='AI-assisted evidence investigation',human_approval_status='pending',adjudicator_identity='',approval_date='',
            ai_review_section=row['ai_review_section'],confidence=row['confidence'],confidence_scope=row['confidence_scope'],
            canonical_label_json=row['proposed_label_json'],reviewed_intervals_json=js(label.get('reviewed_intervals',[])),
            subevents_json=js(label.get('subevents',[])),remaining_uncertainty=row['remaining_uncertainty'],
            reviewer_1_source=row['reviewer_1_source'],reviewer_2_source=row['reviewer_2_source'],
            reviewer_1_sha256=row['reviewer_1_sha256'],reviewer_2_sha256=row['reviewer_2_sha256'])
        out.append(flat)
    return out


def build(package,proposal,out,private_out,local_review):
    package=Path(package).resolve();proposal=Path(proposal).resolve();out=Path(out).resolve();private_out=Path(private_out).resolve()
    assert not out.exists() and not private_out.exists(),'new version directories required; do not overwrite existing work'
    source_manifest,original=core.verify(package,proposal)
    receipt,groups=load_audit(package);runs={r['episode']:r for r in source_manifest['runs']}
    out.mkdir(parents=True);decisions=[]
    for old in original:
        finding=recommend(old,groups,runs);refs=evidence_refs(package,old)
        row=dict(old,prior_proposed_label_json=old['proposed_label_json'],proposed_label_json=js(finding['label']),
            ai_review_section=finding['section'],resolution_kind=finding['resolution_kind'],confidence=finding['confidence'],
            confidence_scope=finding['confidence_scope'],case_id=finding['case_id'],
            reasoning=finding['reason'],remaining_uncertainty=finding['remaining_uncertainty'],
            evidence_measurements_json=js(finding['measurements']),evidence_frame_interval_json=js(finding['frames']),
            evidence_references=js(refs),evidence_time_interval_s_json=js([finding['frames'][0]/20,finding['frames'][1]/20]),
            applicable_requirement_condition='R1 scope B/C/D/F/G/H; initial saved frame 10; first policy endpoint 11',
            evidence_limitations=finding['limits'],ai_recommendation_status='complete_provisional_recommendation',
            alex_original_label=short_label(json.loads(old['reviewer_1_original_rows']),old['table']),
            ryiad_original_label=short_label(json.loads(old['reviewer_2_original_rows']),old['table']),
            human_approval_required='yes',human_approval_status='pending',adjudicator_identity='',approval_date='')
        decisions.append(row)
    core.writecsv(out/'complete_adjudication_decisions.csv',decisions)
    for table in TABLES:core.writecsv(out/f'adjudicated_{table}.csv',csv_label_rows(package,decisions,table))
    ledger=[dict(adjudication_id=r['adjudication_id'],proposal_sha256=hashlib.sha256(js(r).encode()).hexdigest(),
                 disposition='pending',adjudicator_identity='',approval_date='',label_json=r['proposed_label_json'],
                 reason='',evidence_references=';'.join(json.loads(r['evidence_references'])),
                 review_section=r['ai_review_section'],case_id=r['case_id'],recommended_reason=r['reasoning']) for r in decisions]
    core.writecsv(out/'remaining_human_approval.csv',ledger)
    stats=proposal/'agreement_statistics.json';(out/'original_agreement_statistics.json').write_bytes(stats.read_bytes())
    count=collections.Counter(r['ai_review_section'] for r in decisions)
    summary=dict(schema_version=SCHEMA,source_rows_preserved=160,alignment_units=90,
        original_difference_units=38,mechanical_difference_units_reconciled=sum(r['ai_review_section']=='B' and not r['classification'].endswith('_agreement') for r in decisions),
        original_substantive_difference_units_investigated=sum(r['ai_review_section']=='C' and not r['classification'].endswith('_agreement') for r in decisions),
        additional_nominal_agreement_coverage_tensions=sum(r['ai_review_section']=='C' and r['classification'].endswith('_agreement') for r in decisions),
        sections=dict(count),substantive_review_units=count['C'],substantive_case_cards=len({r['case_id'] for r in decisions if r['ai_review_section']=='C'}),
        high_confidence_recommendations=sum(r['confidence']=='high' for r in decisions),confidence_is_not_probability=True,
        confidence_scope='Strength of the bounded recommendation/canonical representation, not certainty of continuous safety.',
        original_uncertainty_requests=11,proposed_uncertainty_resolutions=dict(collections.Counter(json.loads(r['proposed_label_json'])['resolution_status'] for r in decisions if r['table']=='uncertainty_requests')),
        unresolved_uncertainty_requests=sum(json.loads(r['proposed_label_json'])['resolution_status']!='resolved_existing_evidence' for r in decisions if r['table']=='uncertainty_requests'),
        uncertain_physical_event_classifications=sum(json.loads(r['proposed_label_json']).get('fall_status')=='insufficient_information' for r in decisions),
        decisions_pending_human_approval=90,decisions_human_approved=0,dataset_frozen=False,
        original_agreement_statistics_sha256=digest(stats),original_statistics_unchanged=True,
        new_recorded_samples_inspected=receipt['rows'],recordings_fresh_hash_verified=4,duplicate_event_rows_found=0,
        camera_inspection='Prior verified opening/boundary sheets reused; new consecutive sampled camera sequences inspected in both views. Full continuous videos not independently watched; no between-sample observations invented.',
        episode_014_cream_cheese='Propose applies / no_violation_observed_within_reviewed_coverage under scope F; retain held-lift and drop phases; Nikta confirmation pending.')
    core.writejson(out/'adjudication_summary.json',summary)
    (out/'methodology.md').write_text(METHOD+'\n')
    public_manifest=dict(schema_version=SCHEMA,status='ai_assisted_provisional_not_human_approved_not_frozen',
        source_original_proposal_sha256=digest(proposal/'proposal_checksums.json'),source_decisions_sha256=digest(proposal/'adjudication_decisions.csv'),
        source_file_sha256=source_manifest['source_file_sha256'],requirement_version=source_manifest['requirement_version'],runs=source_manifest['runs'],
        producer_sha256=digest(__file__),collector_sha256=digest(Path(__file__).with_name('collect_complete_evidence.py')),
        private_audit_receipt_sha256=digest(package/'adjudication/evidence_complete_20261026/audit_receipt.json'),
        scientific_evidence_access='Raw audit tables and contact sheets remain local-only; report findings and logical references are publishable. No private absolute paths or raw payloads are embedded.',
        decision_counts=dict(pending=90,approved=0),adjudicator_identity=None,approval_date=None,finalized_labels_sha256=None,
        original_agreement_statistics_sha256=digest(stats))
    core.writejson(out/'dataset_manifest.json',public_manifest)
    write_report(out,decisions,summary)
    (out/'README.md').write_text('''# Complete AI-assisted R1 proposal — pending human approval

Read adjudication_evidence_report.md and adjudication_summary.json. All four adjudicated_*.csv filenames denote **provisional AI-generated recommendations**, never approved human ground truth. Their dataset_status and human_approval_status columns make this explicit. All 90 alignment units are represented, with complete original reviewer rows retained in complete_adjudication_decisions.csv.

The unchanged original independent-review statistics are in original_agreement_statistics.json. The new evidence-qualified coverage issue does not rewrite those statistics. Disjoint negative-observation fragments stay disjoint; the compound lift/drop retains explicit subevents. Blank exact physical timings remain unknown.

The adjacent ignored local HTML review interface groups A agreements, B mechanical reconciliations, C substantive cases and D unresolved requests; its E section exports a signed decision ledger only after an actual human enters decisions, identity, date and reasons. It does not approve anything by opening the file. A/B can be reviewed as batches; C/D are shown individually. Contact sheets are loaded from local evidence directories and must not be pushed.

After actual review, validate the downloaded ledger against the new private proposal. Do not apply new decision bindings to the old proposed_20261026 package. The private bridge is a new proposal compatible with the existing approval-gated finalizer; no real finalization is performed during preparation.

```sh
python3 human_review_package/adjudication/ai_tools/complete_adjudication.py verify --package human_review_package --out human_review_package/adjudication/ai_assisted_20261026
python3 human_review_package/adjudication/ai_tools/complete_adjudication.py check-approvals --package human_review_package --out human_review_package/adjudication/ai_assisted_20261026 --private-proposal human_review_package/adjudication/ai_private_20261026 --ledger nikta_reviewed_approvals.csv
```

Only after explicit approval, the unchanged existing finalizer can consume that verified new private proposal and signed ledger, preserving unresolved decisions. It emits group-level canonical events with subevents/intervals preserved in final_label_json. This AI-assisted preparation does not execute finalization, amend reviewers, approve labels, commit or push anything.
''')
    checks={p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()};core.writejson(out/'checksums.json',checks)
    # New private bridge; leave the original proposal and published snapshot intact.
    private_out.mkdir(parents=True)
    core.writecsv(private_out/'adjudication_decisions.csv',decisions)
    private_manifest=json.loads(json.dumps(source_manifest));private_manifest['decision_counts']=dict(approved=0,pending=90,unresolved=summary['unresolved_uncertainty_requests'])
    private_manifest['ai_proposal_schema']=SCHEMA;private_manifest['ai_producer_sha256']=digest(__file__)
    for row in decisions:
        for ref in json.loads(row['evidence_references']):private_manifest['evidence_file_sha256'][ref]=digest(package/ref)
    core.writejson(private_out/'dataset_manifest.json',private_manifest)
    core.writejson(private_out/'proposal_checksums.json',{p.name:digest(p) for p in sorted(private_out.iterdir()) if p.is_file()})
    core.verify(package,private_out)
    if local_review:
        local_review=Path(local_review).resolve();local_review.mkdir(parents=True,exist_ok=False)
        write_html(local_review/'review.html',decisions,summary)
    verify(package,out)
    return summary


def write_report(out,rows,summary):
    lines=['# Complete AI-assisted R1 adjudication proposal','',
        '**All 90 decisions are pending human approval. No dataset is frozen.**','',
        f'Original 160 submitted rows are represented in 90 units. {summary["mechanical_difference_units_reconciled"]} of the 38 original difference units are mechanically reconciled; '
        f'{summary["original_substantive_difference_units_investigated"]} require substantive evidence judgments. '
        'One nominally agreeing butter negative has an additional coverage tension. Five substantive case cards cover six units. '
        'The eleven uncertainty questions receive specific answers: one proposed resolved interpretation and ten with unresolved components. '
        'High confidence describes the bounded recommendation, not continuous physical certainty.','',
        '## A — Reviewer agreements','',
        'Forty units retain categorical agreement without discovered evidentiary contradiction. Original full-review/visibility limits remain; no continuous negative is inferred. '
        'All original source rows and reasons are in complete_adjudication_decisions.csv. These can be reviewed as a batch, rather than re-investigating each recording.','',
        '| Type | Units | Evidence check |','|---|---:|---|',
        '| Initial support | 20 | Frame-10 poses, contact owners, collision-box bounds, prior qualified initial-camera review |',
        '| Requirement interpretation | 19 | Initial support and full saved contact/pose sequences; no task-outcome-to-safety inference |',
        '| Negative coverage | 1 | Explicit post-setup fragment and sampled table contacts; visibility qualified |','',
        '## B — Mechanical reconciliations','',
        'Thirty-three original difference units are reconciled by deterministic rules. Seventeen negative-coverage/inventory differences use explicit descriptive fragments instead of broad episode context, fifteen setup timing differences distinguish first recorded contact from unknown exact landing/settling, and one lift/drop unit receives explicit grasp/lift/release phases. '
        'No duplicate event row was found. Missing negative rows are not treated as negative votes. Separate no-event fragments are never joined across a positive event.','',
        '| Unit | Run / object | Canonical recommendation | Rule |','|---|---|---|---|']
    for row in rows:
        if row['ai_review_section']=='B':
            label=json.loads(row['proposed_label_json']);desc=label.get('event_type','')
            if label.get('reviewed_intervals'):desc+=' '+js(label['reviewed_intervals'])
            lines.append(f'| {row["adjudication_id"]} | {row["episode"]} / {row["object_id"]} | {desc} | {row["reasoning"]} |')
    lines+=['','## C — Substantive adjudication recommendations','',
        'These are AI-proposed decisions for Nikta to approve/correct. Original reviewer labels remain unchanged. References use saved frame indices; simulator time is frame/20 s on this recording grid. '
        'Private contact-sheet/audit references are logical local-only identifiers, not publicly available payloads.','']
    for case in sorted({r['case_id'] for r in rows if r['ai_review_section']=='C'}):
        rr=[r for r in rows if r['ai_review_section']=='C' and r['case_id']==case]
        lines+=['### '+case,'']
        for row in rr:
            lo,hi=json.loads(row['evidence_frame_interval_json'])
            lines += [f'**{row["adjudication_id"]}: {row["episode"]} / {row["object_id"]}**',
                '', '**Alex:** '+row['alex_original_label'], '', '**Ryiad:** '+row['ryiad_original_label'],
                '', '**Recommended:** `'+row['proposed_label_json']+'`', '', row['reasoning'],
                '', f'**Evidence:** [camera video](../../full_videos/{row["episode"]}_side_by_side.mp4#t={lo/20:.2f},{hi/20:.2f}), frames {lo}–{hi}; simulator time {lo/20:.2f}–{hi/20:.2f} s. '
                f'Original HDF5 fields: frames/<frame>/raw_observation/<object>_pos/value and <object>_quat/value; simulator/contacts@json, geom_xpos/value, geom_xmat/value; per-run XML/native geometry mapping.',
                '', '**Measured audit summary:** `'+row['evidence_measurements_json']+'`',
                '', '**Confidence:** '+row['confidence']+'. **Human approval:** pending. **Limits:** '+row['remaining_uncertainty'],
                '', '**Exact evidence references:** `'+row['evidence_references']+'`','']
    lines+=['## D — Unresolved uncertainties','',
        'All eleven requests are retained. “Resolved” below is only the proposed answer to the question; it is not a human resolution signature. Ten requests retain unresolved scientific components. '
        'The orange-juice event classification is additionally marked insufficient information, linked to its uncertainty request.','',
        '| Request / unit | Proposed outcome | Evidence-supported answer | Remaining limit |','|---|---|---|---|']
    for row in rows:
        if row['table']=='uncertainty_requests':
            label=json.loads(row['proposed_label_json'])
            lines.append(f'| {label["request_id"]} / {row["adjudication_id"]} | {label["resolution_status"]} | {row["reasoning"]} | {row["remaining_uncertainty"]} |')
    lines+=['','## E — Human approval','',
        'Use the local offline review.html file for batch A/B and focused C/D decisions. It displays both source labels, canonical labels, reasons, saved measurements and the relevant local contact sheets. '
        'Every selection starts pending. Nikta may approve a proposed label, retain an explicitly unresolved outcome, reject, or correct its JSON. '
        'The download requires actual identity/date and a reason for each selected decision; it does not run finalization. All records still pending are preserved as pending. '
        'The downloaded ledger is bound to the new complete decision rows by SHA-256 and checked with check-approvals. '
        'No original annotations or prior proposals are overwritten.','',
        '## Evidence scope and limitations','',LIMITS,'',
        'All 6,560 object/frame samples (1,312 saved frames × five protected objects) were inspected by reproducible table checks. All four original HDF5 hashes were freshly matched to the independent-review manifest; XML hashes and source fingerprints were checked. '
        'metrics.csv rows and resources.csv schema/checksums were audited as execution metadata; they are not support or safety evidence. '
        'Prior verified opening/boundary contact sheets were reused. Newly extracted consecutive sampled sequences 002/13–30 and 014/57–65,230–265,266–285 were inspected in both views. '
        'This does not claim watching the entire full videos or seeing between saved frames.','',
        '## Original reliability, unchanged','',
        'Initial support 20/20, κ=1.0; applicability 20/20, κ=1.0; interpretation 19/20, κ≈0.894; strict paired detail 41/66 (62.12%). '
        'The original 38 difference units and all original source rows remain unchanged. The new evidence-qualified coverage tension is reported separately, not used to revise independent reliability. '
        'No post-AI consensus statistic is presented as independent inter-rater reliability.','',
        '## Research methodology','',METHOD,'']
    (out/'adjudication_evidence_report.md').write_text('\n'.join(lines))


def write_html(path,rows,summary):
    """Local, self-contained interaction; no network, persistence or auto-approval."""
    payload=js(dict(rows=rows,summary=summary)).replace('<','\\u003c')
    template=r'''<!doctype html><html lang="en"><meta charset="utf-8"><title>R1 AI-assisted proposal — human approval pending</title>
<style>body{font:16px system-ui;max-width:1150px;margin:30px auto;padding:0 15px;color:#17212b}header{position:sticky;top:0;background:#fff;padding:12px;border-bottom:2px solid #bbb}article{border:1px solid #bbc;padding:16px;margin:14px 0;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f7;padding:12px}img{max-width:100%;height:auto}textarea{width:96%;min-height:65px}input,select,button{font:inherit;margin:5px;padding:6px}.pending{color:#8a4100}.note{background:#fff5d9;padding:14px}</style>
<header><b>Proposed AI-assisted R1 adjudication — all 90 human decisions pending</b><div id="summary"></div><nav><a href="#A">A Agreements</a> · <a href="#B">B Mechanical</a> · <a href="#C">C Substantive</a> · <a href="#D">D Uncertainties</a> · <a href="#E">E Approval</a></nav></header>
<p class="note">This file neither approves nor freezes data. Review recommendations, then explicitly select decisions. Original reviewer answers stay unchanged. A/B may be reviewed as groups; C/D remain individual. Approving a qualified or uncertain label approves preservation of that uncertainty, not a definite safety claim. If you choose unresolved/rejected, edit the JSON to an explicit uncertain outcome where needed. Contact sheets are private local sampled images, not continuous observations. Nothing is sent to a server.</p>
<main id="content"></main><section id="E"><h2>E — Human approval</h2><p>Export records actual selections, leaving unreviewed units pending. Enter your real identity and date. Do not sign an AI recommendation you have not reviewed. This creates an approval ledger only; the command-line validator rejects pending decisions before finalization.</p><label>Adjudicator <input id="identity" placeholder="Nikta — actual human adjudicator"></label><label>Approval date <input id="date" type="date"></label><button id="download">Download reviewed decision ledger</button><p id="error"></p></section>
<script type="application/json" id="data">PAYLOAD</script><script>
const data=JSON.parse(document.getElementById('data').textContent),rows=data.rows,states=new Map();
document.getElementById('summary').textContent=`${rows.length} units; ${data.summary.mechanical_difference_units_reconciled} mechanical differences; ${data.summary.substantive_case_cards} substantive case cards; 11 uncertainty requests.`;
const titles={A:'Reviewer agreements — no discovered contradiction',B:'Mechanical reconciliations',C:'Substantive recommendations — focus here',D:'Unresolved questions and proposed answers'};
function node(tag,text,parent){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(parent)parent.appendChild(n);return n;}
for(const key of ['A','B','C','D']){const section=node('section',undefined,document.getElementById('content'));section.id=key;node('h2',key+' — '+titles[key],section);
 const rr=rows.filter(r=>r.ai_review_section===key);node('p',rr.length+' units. All are currently pending; high confidence is not a human signature.',section);
 if(['A','B'].includes(key)){const bulkReason=node('input',undefined,section);bulkReason.placeholder='Your reason after reviewing this group';const batch=node('button','Select proposals in this group',section);batch.onclick=()=>{if(!bulkReason.value.trim()){alert('Enter your review reason first.');return;}for(const r of rr){const s=states.get(r.adjudication_id);s.select.value='approved';s.reason.value=bulkReason.value;} };}
 for(const r of rr){const article=node('article',undefined,section);article.id=r.adjudication_id;node('h3',`${r.episode} / ${r.object_id||'run-wide'} — ${r.case_id||r.table}`,article);
 node('p',`${r.adjudication_id}; ${r.confidence} confidence; original comparison: ${r.classification}`,article);
 const detail=node('details',undefined,article);if(['C','D'].includes(key))detail.open=true;node('summary','Evidence and recommendation',detail);
 node('p','Alex: '+r.alex_original_label,detail);node('p','Ryiad: '+r.ryiad_original_label,detail);node('pre',r.proposed_label_json,detail);node('p',r.reasoning,detail);node('p','Remaining limits: '+(r.remaining_uncertainty||r.evidence_limitations),detail);
 node('pre','Measured audit: '+r.evidence_measurements_json,detail);node('p','R1: '+r.applicable_requirement_condition,detail);
 const refs=JSON.parse(r.evidence_references);for(const ref of refs){if(ref.endsWith('.png')||ref.endsWith('.jpg')){if(['C','D'].includes(key)){const img=node('img',undefined,detail);img.loading='lazy';img.alt=ref;img.src='../'+ref.replace(/^adjudication\//,'');}}else if(ref.endsWith('.mp4')){const link=node('a','Open existing run video',detail);link.href='../../'+ref;node('br','',detail);}}
 const raw=node('details',undefined,detail);node('summary','Original annotations and precise references',raw);node('pre',r.reviewer_1_original_rows+'\n'+r.reviewer_2_original_rows+'\n'+r.evidence_references,raw);
 const select=node('select',undefined,article);for(const [value,label] of [['pending','Pending'],['approved','Approve selected/corrected label'],['unresolved','Retain explicit uncertainty'],['rejected','Reject — uncertainty/correction required']]){const o=node('option',label,select);o.value=value;}
 const reason=node('textarea',undefined,article);reason.placeholder='Your explanation (required for a selected human decision)';const edit=node('details',undefined,article);node('summary','Correct the proposed JSON label',edit);const label=node('textarea',undefined,edit);label.value=r.proposed_label_json;states.set(r.adjudication_id,{select,reason,label});
 }}
function csv(v){return '"'+String(v??'').replaceAll('"','""')+'"';}
document.getElementById('download').onclick=()=>{const identity=document.getElementById('identity').value.trim(),date=document.getElementById('date').value;const error=document.getElementById('error');error.textContent='';
 if(!identity.toLowerCase().includes('nikta')||!date){error.textContent='Actual Nikta identity and approval date are required.';return;}
 const fields=['adjudication_id','proposal_sha256','disposition','adjudicator_identity','approval_date','label_json','reason','evidence_references'];const out=[fields.map(csv).join(',')];
 for(const r of rows){const s=states.get(r.adjudication_id),status=s.select.value;try{JSON.parse(s.label.value);}catch(e){error.textContent='Invalid correction JSON: '+r.adjudication_id;return;}
 if(status!=='pending'&&!s.reason.value.trim()){error.textContent='A reason is required for '+r.adjudication_id;return;}
 const values=[r.adjudication_id,r.approval_binding_sha256,status,status==='pending'?'':identity,status==='pending'?'':date,s.label.value,status==='pending'?'':s.reason.value,JSON.parse(r.evidence_references).join(';')];out.push(values.map(csv).join(','));}
 const blob=new Blob([out.join('\n')+'\n'],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='nikta_reviewed_approvals.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
};</script></html>'''
    # Bind downloaded choices to the exact private-finalizer rows. The binding is
    # not part of those rows, avoiding a self-referential hash.
    uirows=[]
    for row in rows:uirows.append(dict(row,approval_binding_sha256=hashlib.sha256(js(row).encode()).hexdigest()))
    payload=js(dict(rows=uirows,summary=summary)).replace('<','\\u003c')
    path.write_text(template.replace('PAYLOAD',payload))


def verify(package,out):
    package=Path(package).resolve();out=Path(out)
    checks=json.loads((out/'checksums.json').read_text())
    assert set(checks)=={p.name for p in out.iterdir() if p.is_file() and p.name!='checksums.json'}
    for name,h in checks.items():assert digest(out/name)==h,('output changed',name)
    manifest=json.loads((out/'dataset_manifest.json').read_text())
    assert manifest['status']=='ai_assisted_provisional_not_human_approved_not_frozen'
    assert manifest['decision_counts']==dict(pending=90,approved=0) and manifest['adjudicator_identity'] is None
    assert manifest['producer_sha256']==digest(__file__)
    for ref,h in manifest['source_file_sha256'].items():assert digest(package/ref)==h,'original submission changed'
    rows=core.readcsv(out/'complete_adjudication_decisions.csv');assert len(rows)==90 and len({r['adjudication_id'] for r in rows})==90
    for row in rows:
        assert row['human_approval_status']=='pending' and row['human_approval_required']=='yes' and not row['adjudicator_identity'] and not row['approval_date']
        assert row['reasoning'] and row['evidence_measurements_json'] and row['evidence_references']
        for ref in json.loads(row['evidence_references']):assert (package/ref).is_file(),('missing evidence reference',ref)
    for side in ['reviewer_1','reviewer_2']:
        for table in TABLES:
            originals=core.readcsv(package/side/(table+'.csv'))
            represented=[source for r in rows if r['table']==table for source in json.loads(r[f'{side}_original_rows'])]
            assert collections.Counter(map(js,originals))==collections.Counter(map(js,represented)), 'source annotation lost/changed'
    exported=[]
    for table in TABLES:
        rr=core.readcsv(out/f'adjudicated_{table}.csv');exported+=rr
        assert len(rr)==len([r for r in rows if r['table']==table])
        assert all(r['dataset_status']=='provisional_ai_recommendation' and r['human_approval_status']=='pending' for r in rr)
    assert {r['adjudication_id'] for r in exported}=={r['adjudication_id'] for r in rows}
    event_ids={r['event_id'] for r in exported if 'event_id' in r}
    for r in exported:
        if 'physical_event_id' in r:
            assert set(filter(None,r['physical_event_id'].split(';')))<=event_ids,'broken canonical event reference'
    private_receipt=package/'adjudication/evidence_complete_20261026/audit_receipt.json'
    assert digest(private_receipt)==manifest['private_audit_receipt_sha256'],'private evidence receipt changed'
    for name,h in json.loads(private_receipt.read_text())['outputs'].items():
        assert digest(private_receipt.parent/name)==h,('private audit artifact changed',name)
    assert digest(out/'original_agreement_statistics.json')==manifest['original_agreement_statistics_sha256']
    ledger=core.readcsv(out/'remaining_human_approval.csv');byid={r['adjudication_id']:r for r in rows}
    assert len(ledger)==90
    for row in ledger:
        assert row['disposition']=='pending' and not row['adjudicator_identity'] and not row['approval_date']
        assert row['proposal_sha256']==hashlib.sha256(js(byid[row['adjudication_id']]).encode()).hexdigest()
    for path in out.iterdir():
        if path.is_file():
            text=path.read_text();assert not re.search(r'/(?:Users|disk|local/home|eecs|private)/',text),'private absolute path in public-safe output'
    return json.loads((out/'adjudication_summary.json').read_text())


def check_approvals(package,out,private,ledger):
    verify(package,out);manifest,rows=core.verify(Path(package).resolve(),Path(private))
    expected={r['adjudication_id']:r for r in rows};actual=core.readcsv(ledger)
    assert len(actual)==90 and len({r['adjudication_id'] for r in actual})==90 and {r['adjudication_id'] for r in actual}==set(expected)
    byrun=core.source_inventory(Path(package).resolve())[2]
    for r in actual:
        row=expected[r['adjudication_id']]
        assert r['proposal_sha256']==hashlib.sha256(js(row).encode()).hexdigest(),'approval bound to different proposal'
        assert r['disposition'] in ['approved','unresolved','rejected'],'human decisions still pending'
        assert 'nikta' in r['adjudicator_identity'].casefold() and r['reason'].strip(),'actual adjudicator and reason required'
        datetime.date.fromisoformat(r['approval_date']);label=json.loads(r['label_json']);core.validate_label(row['table'],label,byrun[row['run_id']])
        refs=[v.strip() for v in r['evidence_references'].split(';') if v.strip()]
        assert set(refs)&set(json.loads(row['evidence_references'])),'decision-specific evidence required'
        for ref in refs:
            p=(Path(package)/ref).resolve();assert p.is_relative_to(Path(package).resolve()) and p.is_file()
            assert ref in manifest['evidence_file_sha256'] and digest(p)==manifest['evidence_file_sha256'][ref]
        for key in ['run_id','object_id','episode']:
            if key in label:assert label[key]==row[key],'cross-run correction'
        if r['disposition'] in ['unresolved','rejected']:
            assert any(label.get(key) in ['uncertain','insufficient_information'] for key in ['support_label','observation_status','interpretation']) or label.get('resolution_status','').startswith(('unresolved','partially_resolved')),'unresolved/rejected needs explicit uncertainty label'
    return 'Human ledger validates structurally; this command does not approve labels or freeze a dataset.'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    for name in ['build','verify','check-approvals']:
        q=sub.add_parser(name);q.add_argument('--package',type=Path,default=ROOT.parent);q.add_argument('--out',type=Path,required=True)
        if name=='build':
            q.add_argument('--proposal',type=Path,required=True);q.add_argument('--private-out',type=Path,required=True);q.add_argument('--local-review',type=Path)
        if name=='check-approvals':q.add_argument('--private-proposal',type=Path,required=True);q.add_argument('--ledger',type=Path,required=True)
    a=p.parse_args()
    value=build(a.package,a.proposal,a.out,a.private_out,a.local_review) if a.cmd=='build' else verify(a.package,a.out) if a.cmd=='verify' else check_approvals(a.package,a.out,a.private_proposal,a.ledger)
    print(json.dumps(value,indent=2))
