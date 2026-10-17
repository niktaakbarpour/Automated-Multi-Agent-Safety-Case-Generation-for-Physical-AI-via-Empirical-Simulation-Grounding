"""Provisional development detector. No requirement approvals or safety verdicts."""
import json, math
from pathlib import Path

REQUIRED = {'status','objects','table_geom_ids','floor_geom_ids','gripper_left_ids','gripper_right_ids','contact_face_band_m','descent_m','lift_clearance_m','minimum_descent_intervals','sample_period_s','time_arithmetic_allowance_s','geometry_phase_lag_s','interval_start_frame','post_lift_scope','source_root','task_id','sensitivity_profiles','requirement_approved','detector_validated','unknown_is_pass','floor_required','catch_erases_event','initial_indirect_support'}
def load_config(path):
    c=json.loads(Path(path).read_text()); validate_config(c); return c

def validate_config(c):
    missing=REQUIRED-set(c)
    if missing: raise ValueError('Missing explicit configuration: '+','.join(sorted(missing)))
    if c['status']!='PROPOSED_UNAPPROVED': raise ValueError('Development configuration must remain unapproved')
    for k in ['contact_face_band_m','descent_m','lift_clearance_m','sample_period_s','time_arithmetic_allowance_s']:
        if not isinstance(c[k],(float,int)) or not math.isfinite(c[k]) or c[k]<=0: raise ValueError('Invalid parameter '+k)
    if any(c[k] is not False for k in ['requirement_approved','detector_validated','unknown_is_pass','floor_required','catch_erases_event']):raise ValueError('Provisional scope invariant violated')
    if c['interval_start_frame']!=10 or c['geometry_phase_lag_s']!=0.002:raise ValueError('Unsupported phase/interval configuration for these recordings')
    if c['minimum_descent_intervals']<1: raise ValueError('Invalid descent persistence')
    if c['post_lift_scope']!='unresolved_not_automatic_table_fall': raise ValueError('Post-lift scope requires separate review')

def time_guard(previous,current,c):
    if not math.isfinite(current['time']):raise ValueError('Nonfinite simulator time')
    if previous is not None and (current['frame']!=previous['frame']+1 or abs(current['time']-previous['time']-c['sample_period_s'])>c['time_arithmetic_allowance_s']):
        raise ValueError('Missing interval or timing mismatch')

def initial_applicability(s):
    if not s.get('valid',False): return 'unknown_missing_measurement'
    if s['direct_support']: return 'direct_table_support_candidate'
    if s['indirect_candidate']: return 'unknown_indirect_support'
    if s['other_contacts']: return 'unknown_other_contact_support'
    return 'initial_table_support_not_established'


def contact_free(s):
    """Observed endpoint qualification only, never continuous contact absence."""
    return s.get('valid',False) and not s['direct_support'] and not s['other_contacts'] and not s['indirect_candidate'] and not s['gripper_contacts']

def reference(s):
    return {k:s[k] for k in ['frame','time','geometry_nominal_time','run_id','hdf5_frame'] if k in s}

def analyze(samples,c):
    """Two intervals require three valid contact-free endpoints, each descending.

    Departure history is distinct from the contact-free confirmation window.
    Event types may strengthen, but origin/contact/gripper uncertainties persist.
    """
    validate_config(c)
    events=[];gaps=[];transitions=[];unconfirmed=[]
    active=None;previous=None;last_support=None;departure=None;lift=False;interaction=False
    interaction_frames=[];lift_frames=[];chain=[]
    initial=next((s for s in samples if s['frame']==c['interval_start_frame']),{'valid':False})

    def classification(e):
        h=e['origin_history']
        if h['lift_candidate']:return 'post_lift_drop_candidate'
        if h['unresolved_contact_history']:return 'ambiguous_contact_departure_descent_candidate'
        if h['last_table_support_frame'] is None:return 'unsupported_descent_unknown_origin'
        if e['strong_departure_evidence']:return 'direct_table_departure_descent_candidate'
        return 'table_support_loss_descent_ambiguous_candidate'

    def update(e,s):
        e['observed_event_span']['end']=reference(s)
        evidence=[]
        for field in ['whole_collision_below_tabletop','outside_table_support_projection']:
            if s.get(field,False):
                item={'kind':field,'reference':reference(s)};e['strong_departure_evidence'].append(item);evidence.append(item)
        kind=classification(e)
        if kind!=e['type']:
            e['classification_history'].append({'type':kind,'reference':reference(s),'supporting_evidence':evidence,'reason':'Later collision geometry strengthens departure evidence; original ambiguity flags retained'})
            e['type']=kind

    def close(reason,s=None,censored=False):
        nonlocal active
        if active is None:return
        e=events[active]
        e['ending']={'reason':reason,'type':reason,'censored':censored,'reference':reference(s) if s is not None else None,
                     'last_observed_reference':e['observed_event_span']['end']}
        if s is not None and s.get('valid',False):e['ending']['contacts']=s['other_contacts']
        active=None

    def flush_chain(reason):
        nonlocal chain
        if chain and active is None:
            unconfirmed.append({'contact_free_descent_intervals':chain.copy(),'count':len(chain),'required':c['minimum_descent_intervals'],
                'stopped_reason':reason,'phase':'setup' if chain[-1]['end']['frame']<c['interval_start_frame'] else 'policy',
                'departure_bracket':departure.copy() if departure else None,
                'origin_history':{'lift_candidate':lift,'unresolved_contact_history':interaction},
                'status':'insufficient_persistence_not_an_event_candidate'})
        chain=[]

    def reset():
        nonlocal previous,last_support,departure,lift,interaction,interaction_frames,lift_frames,chain
        previous=None;last_support=None;departure=None;lift=False;interaction=False;interaction_frames=[];lift_frames=[];chain=[]

    for original in samples:
        s=original
        if s.get('valid',False):
            try:
                if not all(math.isfinite(s[k]) for k in ['time','center_z','bottom_z','table_top_z']):raise ValueError('Nonfinite observation')
            except (KeyError,TypeError,ValueError) as exc:s=dict(s,valid=False,error=str(exc))
        if s['frame']==c['interval_start_frame']:initial=s
        if not s.get('valid',False):
            flush_chain('recording_gap');close('recording_gap',s,censored=True)
            gaps.append({'frame':s['frame'],'reason':s.get('error','missing measurement')});reset();continue
        try:time_guard(previous,s,c)
        except ValueError as exc:
            flush_chain('timing_or_frame_gap');close('timing_or_frame_gap',None,censored=True)
            gaps.append({'frame':s['frame'],'reason':str(exc)});reset()
        if s['frame']==c['interval_start_frame']:
            flush_chain('policy_interval_boundary');close('policy_interval_boundary',None,censored=True);reset()
        if previous is not None and previous['direct_support']!=s['direct_support']:
            t={'type':'table_support_candidate_gained' if s['direct_support'] else 'table_support_candidate_departed',
               'frames':[previous['frame'],s['frame']],'times':[previous['time'],s['time']],
               'phase':'setup' if s['frame']<c['interval_start_frame'] else 'policy'};transitions.append(t)
            if previous['direct_support']:departure=t['frames'].copy()
        interval_ok=previous is not None and contact_free(previous) and contact_free(s) and previous['center_z']-s['center_z']>=c['descent_m']
        if interval_ok:
            interval={'start':reference(previous),'end':reference(s),'descent_m':previous['center_z']-s['center_z'],'both_endpoints_contact_free':True}
            chain.append(interval)
            if active is not None:events[active]['observed_contact_free_descent_intervals'].append(interval)
        else:flush_chain('contact_or_non_descending_endpoint')

        # Record and retain interactions before assessing active evidence or event creation.
        if not s['direct_support'] and s['other_contacts']:
            interaction=True;interaction_frames.append(reference(s))
        if not s['direct_support'] and s['bilateral_gripper'] and s['bottom_z']-s['table_top_z']>c['lift_clearance_m'] and last_support is not None:
            lift=True;lift_frames.append(reference(s))
        if active is None and len(chain)>=c['minimum_descent_intervals']:
            window=chain[-c['minimum_descent_intervals']:]
            start=window[0]['start'];span_start=start
            if departure is not None:
                # Departure end is known from a consecutive supported/non-supported pair.
                span_start={'frame':departure[1],'time':last_support['time']+c['sample_period_s']}
            e={'type':None,'initial_classification':None,'classification_history':[],
               'departure_bracket':departure.copy() if departure else None,
               'observed_event_span':{'start':span_start,'end':reference(s)},
               'descent_frames':[start['frame'],s['frame']],
               'confirmation_window':window.copy(),'observed_contact_free_descent_intervals':window.copy(),
               'confirmation_frame':s['frame'],'confirmation_time':s['time'],
               'phase':'setup' if s['frame']<c['interval_start_frame'] else 'policy',
               'initial_applicability':initial_applicability(initial),'ending':None,
               'origin_history':{'last_table_support_frame':last_support['frame'] if last_support else None,'lift_candidate':lift,
                                 'lift_evidence':lift_frames.copy(),'unresolved_contact_history':interaction,'unresolved_contact_frames':interaction_frames.copy()},
               'strong_departure_evidence':[],
               'uncertainty':['Contact-free only at sampled endpoints; no continuous absence of contact established','20 Hz coverage can miss support, catches, short events and substep transitions','Recorded contacts lack normals/forces; support and lift remain candidates','No robot intention or contact causation inferred'],
               'requirement_verdict':'not_assessed_pending_requirement_scope_and_detector_review'}
            # Accumulate geometry evidence already observed during this confirmation window.
            for x in samples:
                if start['frame']<=x['frame']<=s['frame'] and x.get('valid',False):
                    for field in ['whole_collision_below_tabletop','outside_table_support_projection']:
                        if x.get(field,False):e['strong_departure_evidence'].append({'kind':field,'reference':reference(x)})
            e['type']=classification(e);e['initial_classification']=e['type']
            e['classification_history'].append({'type':e['type'],'reference':reference(s),'supporting_evidence':e['strong_departure_evidence'].copy(),'reason':'Persistence confirmation at contact-free endpoints'})
            events.append(e);active=len(events)-1
        elif active is not None:update(events[active],s)

        if s['direct_support']:
            close('table_recontact',s);last_support=s;departure=None;lift=False;interaction=False;interaction_frames=[];lift_frames=[]
        elif s['other_contacts']:
            close('gripper_contact_catch_candidate' if s['gripper_contacts'] else 'non_table_contact_transition',s)
        previous=s
    flush_chain('recording_termination');close('recording_termination',None,censored=True)
    return {'initial_applicability':initial_applicability(initial),'events':events,'support_transitions':transitions,'gaps':gaps,
            'unconfirmed_descent_sequences':unconfirmed,
            'requirement_verdict':'not_assessed_pending_approval','human_label':None,
            'measurement_statement':'Provisional 20 Hz endpoint evidence; absence of a candidate is not continuous safety.'}
