"""Deterministic R1 reasoning over qualified recorded-state evidence.

No episode identifiers, labels, reviewer text, model calls or physical thresholds.
All positive/negative claims concern sampled states, not intersample behavior.
"""
import math
import sys

TABLE = 'living_room_table'
UNKNOWN = 'insufficient_information'


def ranges(frames):
    result = []
    for f in sorted(set(frames)):
        if result and result[-1][1] + 1 == f:
            result[-1][1] = f
        else:
            result.append([f, f])
    return result


def arithmetic(values, config):
    return config['arithmetic_eps_multiplier'] * sys.float_info.epsilon * max(1., *(abs(v) for v in values))


def close_vectors(a, b, config):
    return len(a) == len(b) and bool(a) and all(math.isfinite(x) and math.isfinite(y) and abs(x-y) <= arithmetic([x,y], config) for x,y in zip(a,b))


def complete(frame, name):
    return bool(frame and frame.get('valid') and frame.get('contacts_complete') and frame.get('mapping_valid') and math.isfinite(frame.get('time',float('nan'))) and name in frame.get('objects', {}) and frame['objects'][name].get('valid'))


def adjacent(a, b, config):
    return b['frame']==a['frame']+1 and abs(b['time']-a['time']-config['sample_period_s'])<=config['time_arithmetic_allowance_s']


def path_to_table(frame, name, visiting=()):
    """Only qualified upward faces form edges, not arbitrary contact graphs."""
    if name == TABLE:
        return [TABLE]
    if name in visiting or not complete(frame, name):
        return None
    obj = frame['objects'][name]
    parents = obj['support_parents']
    if len(parents)!=1 or set(obj['contact_entities']) - set(parents) - set(obj.get('supported_children',[])):
        return None
    for parent in sorted(parents):
        path = path_to_table(frame, parent, visiting + (name,))
        if path:
            return [name] + path
    return None


def static_path(frames, name, config):
    if not frames or any(not complete(f, name) for f in frames):
        return None
    if any(not adjacent(a,b,config) for a,b in zip(frames,frames[1:])):
        return None
    paths = [path_to_table(f, name) for f in frames]
    if not paths[0] or any(p != paths[0] for p in paths):
        return None
    for entity in paths[0][:-1]:
        if any(not complete(f, entity) for f in frames):
            return None
        pose = frames[0]['objects'][entity]['pose']
        if any(not close_vectors(pose, f['objects'][entity]['pose'], config) for f in frames[1:]):
            return None
    # The reference surface itself must be invariant in the saved bundle.
    if any(not close_vectors(frames[0]['table_pose'], f['table_pose'], config) for f in frames[1:]):
        return None
    return paths[0]


def initial_support(frames, name, config):
    start = config['start_frame']
    index = {f['frame']: f for f in frames}
    stencil = [index.get(start+i) for i in config['initial_stencil_offsets']]
    evidence = {'frames': [start+i for i in config['initial_stencil_offsets']],
                'boundary_frame': start, 'observation_domain': 'saved_geometry_contact_states',
                'qualification': 'Nominal contact/geometry lag retained; no support forces inferred.'}
    if any(not complete(f, name) for f in stencil):
        return dict(applicability=UNKNOWN, support_class=UNKNOWN,
                    reason='Missing, invalid, incompletely mapped or incomplete-contact boundary/adjacent snapshot.', evidence=evidence)
    if any(not adjacent(a,b,config) for a,b in zip(stencil,stencil[1:])):
        return dict(applicability=UNKNOWN,support_class=UNKNOWN,reason='Boundary timing/coverage gap.',evidence=evidence)
    path = static_path(stencil, name, config)
    evidence['observations'] = [{
        'frame': f['frame'], 'support_parents': f['objects'][name]['support_parents'],
        'contact_native_ids': f['objects'][name]['contact_native_ids'],
        'contact_entities': f['objects'][name]['contact_entities'],
        'bounds': f['objects'][name]['bounds'], 'pose': f['objects'][name]['pose'],
        'support_contacts': f['objects'][name]['support_contacts']
    } for f in stencil]
    if path:
        evidence['support_chain'] = path
        evidence['chain_observations'] = {entity: [dict(frame=f['frame'], pose=f['objects'][entity]['pose'], support_contacts=f['objects'][entity]['support_contacts']) for f in stencil] for entity in path[:-1]}
        return dict(applicability='applies', support_class='direct_stable_table' if len(path)==2 else 'indirect_stable_table',
                    reason='Invariant adjacent sampled geometry and qualified upward support contacts establish a stable recorded support chain.', evidence=evidence)
    if all(not f['objects'][name]['contact_entities'] and f['objects'][name]['table_separated'] for f in stencil):
        return dict(applicability='does_not_apply', support_class='established_absence',
                    reason='Complete contact records show no support path and collision geometry is separated from table at boundary and both adjacent snapshots.', evidence=evidence)
    return dict(applicability=UNKNOWN, support_class=UNKNOWN,
                reason='Motion, competing/ambiguous contacts or an unestablished indirect chain prevent a stable support determination.', evidence=evidence)


def downward(a, b, name, config):
    if not complete(a,name) or not complete(b,name):
        return False
    x=a['objects'][name]; y=b['objects'][name]
    if x['contact_entities'] or y['contact_entities']:
        return False
    av=x['vertices'];bv=y['vertices']
    return len(av)==len(bv) and bool(av) and all(p[2]-q[2]>arithmetic([p[2],q[2]],config) for p,q in zip(av,bv))


def upward_held(a, b, name, config):
    if not complete(a,name) or not complete(b,name):
        return False
    x=a['objects'][name];y=b['objects'][name]
    if not all(o['bilateral_gripper'] and o['table_separated'] and set(o['contact_entities'])=={'robot'} for o in [x,y]):
        return False
    if not all(q[2]-p[2]>arithmetic([p[2],q[2]],config) for p,q in zip(x['vertices'],y['vertices'])):
        return False
    return all(y['finger_z'][side]-x['finger_z'][side]>arithmetic([y['finger_z'][side],x['finger_z'][side]],config) for side in ['left','right'])


def physical_events(frames, name, config):
    """Track contacts, lift and descent from frame 0 without a frame-10 reset."""
    events=[];last_table=None;departure=None;lift=None;active=None;previous=None;chain_complete=True
    start=config['start_frame']
    def event(typ, phase, scope, onset, interval, **evidence):
        e=dict(event_id=f'{name}:E{len(events):04d}', type=typ, compatible_type=typ,
               phase=phase, scope=scope, onset_bracket=onset, onset=onset[-1],
               interval=interval, status='established', evidence=evidence,
               physical_end_frame=None, offset_established_exact=False)
        events.append(e)
        return e
    for f in frames:
        if not complete(f,name) or (previous and not adjacent(previous,f,config)):
            previous=None;last_table=None;departure=None;lift=None;active=None;chain_complete=False
            continue
        o=f['objects'][name];fi=f['frame']
        table_path=path_to_table(f,name)
        # Record a contact departure before evaluating descent; never reset at 10.
        if previous:
            p=previous['objects'][name]
            previous_path=path_to_table(previous,name)
            if (previous_path and not table_path) or (previous['frame']<start and p['table_contact'] and not o['table_contact']):
                departure=[previous['frame'],fi]
                last_table=previous['frame']
                lift=None;active=None;chain_complete=True
            if upward_held(previous,f,name,config) and departure and not active:
                if lift is None:
                    lift=event('lift','lift','post_lift',departure,[departure[0],fi],
                               upward_pair=[previous['frame'],fi], bilateral_contact=True,
                               qualification='Bilateral exclusive robot contact plus object/both-finger upward co-motion; no carrying-duration threshold.')
                else:
                    lift['interval'][1]=fi
            if lift and p['bilateral_gripper'] and not o['bilateral_gripper']:
                lift['evidence']['release_bracket']=[previous['frame'],fi]
                lift['interval'][1]=previous['frame']
            if downward(previous,f,name,config) and departure and o['table_separated']:
                scope='setup' if departure[1]<start else 'post_lift' if lift else 'in_scope' if chain_complete and last_table is not None else 'unresolved'
                typ='setup_departure' if scope=='setup' else 'post_lift_drop' if scope=='post_lift' else 'r1_fall' if scope=='in_scope' else 'uncertain_descent'
                if active is None:
                    onset=lift['evidence'].get('release_bracket',[previous['frame'],fi]) if lift else departure
                    active=event(typ,'release' if lift else 'departure',scope,onset,[onset[0],fi],
                                 support_departure_bracket=departure.copy(), downward_motion_bracket=[previous['frame'],fi],
                                 lift_event_id=lift['event_id'] if lift else None,
                                 qualification='Consecutive contact-free sampled states and all collision vertices moving downward; no claim about unobserved substeps.')
                else:
                    active['interval'][1]=fi
            elif not o['contact_entities'] and departure:
                pass
            elif o['contact_entities'] and active:
                active['evidence']['first_recorded_contact_frame']=fi
                active['evidence']['first_recorded_contact_entities']=o['contact_entities']
                contact=event('contact','contact',active['scope'],[fi,fi],[fi,fi],group_event_id=active['event_id'],semantics='first recorded contact, not exact physical landing')
                contact['offset_established_exact']=True
                active=None
            # Any unclassified external interaction blocks a later direct-fall inference.
            if departure and o['contact_entities'] and not table_path and not lift:
                chain_complete=False
            if p['table_contact'] and o['table_contact'] and not close_vectors(p['pose'],o['pose'],config):
                if events and events[-1]['type']=='contacted_motion' and events[-1]['interval'][1]==previous['frame']:
                    events[-1]['interval'][1]=fi
                else:
                    m=event('contacted_motion','motion','unresolved',[previous['frame'],fi],[previous['frame'],fi],
                            fall_status=UNKNOWN,classification='Tipping/sliding/rocking versus support-bearing motion unresolved; table contact is not a force measurement.')
                    m['status']='observed_motion_not_established_fall'
            # Single unsupported endpoints and moving supported states retain uncertainty.
            if not o['contact_entities'] and p['contact_entities'] and not table_path and not o['bilateral_gripper']:
                event('support_transition_uncertain','transition','unresolved',[previous['frame'],fi],[previous['frame'],fi],
                      contacts_before=p['contact_entities'],contacts_after=o['contact_entities'],fall_status=UNKNOWN)
        if table_path:
            last_table=fi
            # Preserve active fall before any recovery; emitted events are never erased.
            if active is None:
                departure=None;lift=None;chain_complete=True
        previous=f
    return events


def evaluate(frames, name, run_id, config):
    frames=sorted(frames,key=lambda f:f['frame'])
    if not frames or len({f['frame'] for f in frames})!=len(frames):
        raise ValueError('Empty or duplicate frame sequence')
    initial=initial_support(frames,name,config)
    events=physical_events(frames,name,config)
    for e in events:
        e['event_id']=f'{run_id}:{e["event_id"]}'
        e.update(run_id=run_id,canonical_object_id=name,requirement_version=config['requirement_version'])
        for field in ['lift_event_id','group_event_id']:
            if e['evidence'].get(field):e['evidence'][field]=f'{run_id}:{e["evidence"][field]}'
    valid=[f['frame'] for f in frames if f['frame']>=config['start_frame'] and complete(f,name)]
    negative=[]
    for a,b in zip(frames,frames[1:]):
        if b['frame']>=config['start_frame'] and b['frame']==a['frame']+1 and static_path([a,b],name,config):
            negative.append(b['frame'])
    requested=[config['start_frame'],frames[-1]['frame']]
    proven_falls=[e for e in events if e['type']=='r1_fall' and e['scope']=='in_scope']
    if initial['applicability']=='does_not_apply':
        outcome='not_applicable';reason=None
    elif initial['applicability']!='applies':
        outcome=UNKNOWN;reason=initial['reason']
    elif proven_falls:
        outcome='violation';reason=None
    elif negative==list(range(requested[0],requested[1]+1)):
        outcome='no_violation_observed_within_reviewed_coverage';reason=None
    else:
        outcome=UNKNOWN;reason='Requested domain contains missing observations or states without invariant table-support evidence. Motion, lift/release and re-placement need separate qualified interpretation; absent fall candidates do not qualify them as negatives.'
    return dict(run_id=run_id,canonical_object_id=name,requirement_id=config['requirement_id'],
                requirement_version=config['requirement_version'],checker_version=config['checker_version'],
                initial_support=initial,applicability=initial['applicability'],outcome=outcome,
                events=events,requested_frame_interval=requested,measurement_frame_intervals=ranges(valid),
                applicable_observation_intervals=ranges(negative) if initial['applicability']=='applies' else [],
                negative_evidence_rule='invariant sampled collision transforms and qualified support path at consecutive complete endpoints',
                abstention_reason=reason,uncertainty=['Saved-state observations only; intersample behavior and exact image/contact phase unestablished.','Support classification is a recorded static-equilibrium inference, not a support-force measurement.'],
                evidence_references={'frame_path':'trajectory.h5:frames/<saved_frame>/simulator','initial_frames':initial['evidence']['frames']})
