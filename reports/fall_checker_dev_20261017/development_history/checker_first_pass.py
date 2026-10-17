"""Provisional development detector. No requirement approvals or safety verdicts."""
import json, math
from pathlib import Path

REQUIRED = {'status','objects','table_geom_ids','floor_geom_ids','gripper_left_ids','gripper_right_ids','contact_face_band_m','descent_m','lift_clearance_m','minimum_descent_intervals','sample_period_s','time_arithmetic_allowance_s','geometry_phase_lag_s','interval_start_frame','post_lift_scope','source_root','task_id'}
def load_config(path):
    c=json.loads(Path(path).read_text()); validate_config(c); return c

def validate_config(c):
    missing=REQUIRED-set(c)
    if missing: raise ValueError('Missing explicit configuration: '+','.join(sorted(missing)))
    if c['status']!='PROPOSED_UNAPPROVED': raise ValueError('Development configuration must remain unapproved')
    for k in ['contact_face_band_m','descent_m','lift_clearance_m','sample_period_s','time_arithmetic_allowance_s']:
        if not isinstance(c[k],(float,int)) or not math.isfinite(c[k]) or c[k]<=0: raise ValueError('Invalid parameter '+k)
    if c['minimum_descent_intervals']<1: raise ValueError('Invalid descent persistence')
    if c['post_lift_scope']!='unresolved_not_automatic_table_fall': raise ValueError('Post-lift scope requires separate review')

def time_guard(previous,current,c):
    if previous is not None and (current['frame']!=previous['frame']+1 or abs(current['time']-previous['time']-c['sample_period_s'])>c['time_arithmetic_allowance_s']):
        raise ValueError('Missing interval or timing mismatch')

def initial_applicability(s):
    if not s.get('valid',False): return 'unknown_missing_measurement'
    if s['direct_support']: return 'direct_table_support_candidate'
    if s['indirect_candidate']: return 'unknown_indirect_support'
    if s['other_contacts']: return 'unknown_other_contact_support'
    return 'initial_table_support_not_established'

def analyze(samples,c):
    """Only physical candidates. Contact-free descent is not proof of free fall."""
    validate_config(c)
    events=[]; gaps=[]; active=None; previous=None; last_support=None; lift=False; descent_count=0
    initial=next((s for s in samples if s['frame']==c['interval_start_frame']),{'valid':False})
    for s in samples:
        if not s.get('valid',False):
            gaps.append({'frame':s['frame'],'reason':s.get('error','missing measurement')}); previous=None;last_support=None;lift=False;active=None;descent_count=0;continue
        try:time_guard(previous,s,c)
        except ValueError as e:
            gaps.append({'frame':s['frame'],'reason':str(e)});previous=None;last_support=None;lift=False;active=None;descent_count=0
        # Never extend setup history into requirement interval.
        if s['frame']==c['interval_start_frame']: previous=None;last_support=None;lift=False;active=None;descent_count=0
        if s['direct_support']:
            if active is not None:
                events[active]['ending']={'frame':s['frame'],'time':s['time'],'type':'table_recontact'};active=None
            last_support=s;lift=False;descent_count=0
        else:
            if s['bilateral_gripper'] and s['bottom_z']-s['table_top_z']>c['lift_clearance_m'] and last_support is not None:
                lift=True
            descending=previous is not None and previous['center_z']-s['center_z']>=c['descent_m']
            unsupported=not s['other_contacts'] and not s['indirect_candidate']
            descent_count=descent_count+1 if descending and unsupported else 0
            if active is None and descent_count>=c['minimum_descent_intervals']:
                kind='post_lift_drop_candidate' if lift else ('direct_table_departure_descent_candidate' if last_support is not None else 'unsupported_descent_unknown_origin')
                onset=max(0,s['frame']-descent_count)
                events.append({'type':kind,'departure_bracket':None if last_support is None else [last_support['frame'],last_support['frame']+1],
                    'descent_frames':[onset,s['frame']],'confirmation_frame':s['frame'],'confirmation_time':s['time'],
                    'phase':'setup' if s['frame']<c['interval_start_frame'] else 'policy',
                    'initial_applicability':initial_applicability(initial),'ending':None,
                    'uncertainty':['20 Hz endpoints can miss intervening support or events','No recorded contact normals/forces; support candidates are geometric','No robot intention or contact causation inferred'],
                    'requirement_verdict':'not_assessed_pending_requirement_scope_and_detector_review'})
                active=len(events)-1
            if active is not None and s['other_contacts']:
                events[active]['ending']={'frame':s['frame'],'time':s['time'],'type':'gripper_contact_catch_candidate' if s['gripper_contacts'] else 'non_table_contact_transition','contacts':s['other_contacts']};active=None;descent_count=0
        previous=s
    return {'initial_applicability':initial_applicability(initial),'events':events,'gaps':gaps,
        'requirement_verdict':'not_assessed_pending_approval','human_label':None,
        'measurement_statement':'Provisional observations at 20 Hz; absence of a candidate does not establish continuous safety.'}
