"""Score sealed R1 adapter-v1 outputs against immutable approved final labels.

Requires no third-party packages. Never reads proposed/historical answer cells.
This version refuses determinate predictions: adapter-v1 has no policy that
establishes them. A future adapter needs a new frozen protocol and scorer.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
from matching import contained,match_events
from run_frozen import HERE,dump,sha

OBJECTS={'cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1'}

def key(x,ref=False):
    return (x['run_id'],x['object_id'] if ref else x['canonical_object_id'],x['requirement_version'])

def read_final(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        if row['human_approval_status']!='approved':
            raise ValueError('Reference row not approved')
        row['final']=json.loads(row['final_label_json'])
    return rows

def validate_predictions(predictions,manifest,protocol):
    expected={(r['run_id'],o,protocol['requirement_version']) for r in manifest['runs'] for o in OBJECTS}
    actual=[key(p) for p in predictions]
    if len(actual)!=len(set(actual)) or set(actual)!=expected:
        raise ValueError('Unknown/missing/duplicate run, object or requirement version')
    terminals={r['run_id']:r['last_frame'] for r in manifest['runs']}
    freeze=json.loads((HERE/'baseline_freeze.json').read_text())
    base='reports/fall_checker_dev_v2_20261017/'
    for p in predictions:
        if p['checker_sha256']!=freeze['files'][base+'src/checker.py'] or p['checker_config_sha256']!=freeze['files'][base+'config.json'] or p['checker_commit']!=freeze['checker_last_commit']:
            raise ValueError('Frozen checker provenance mismatch')
        if p['adapter_version']!=protocol['adapter_version']:
            raise ValueError('Incompatible adapter version')
        if p['applicability']!='unknown' or p['outcome']!='insufficient_information':
            raise ValueError('Adapter-v1 cannot establish determinate claims; new adapter/protocol required')
        if not p['abstention_reason'] or p['requested_frame_interval']!=[10,terminals[p['run_id']]]:
            raise ValueError('Missing reason or incompatible requested domain')
        if p['compatible_reference_domain_established'] or p['reviewed_frame_intervals']:
            raise ValueError('Adapter-v1 cannot establish human-compatible reviewed coverage')
        if p['evaluation_config_sha256']!=sha(HERE/'protocol.json') or p['adapter_sha256']!=sha(HERE/'run_frozen.py'):
            raise ValueError('Adapter/protocol drift after prediction seal')
        for lo,hi in p['measurement_frame_intervals']:
            if not 10<=lo<=hi<=terminals[p['run_id']]:
                raise ValueError('Invalid measurement coverage')
        for event in p['events']:
            if event['status']!='provisional_physical_candidate' or event['scope']!='unresolved':
                raise ValueError('Unsupported event promotion')
    return expected

def normalize_reference_event(row):
    """Preserve every final field, fragments, uncertainty and compound linkage.

    Output spans are *observed sample bounds*, not exact physical endpoints.
    Unknown end_frame is never replaced by review_end_frame as a physical end.
    """
    label=row['final'];eid=row['adjudication_id']
    common={'run_id':row['run_id'],'canonical_object_id':row['object_id'],
            'requirement_version':row['requirement_version'],'reference_group_id':eid}
    out=dict(common,event_id=eid,final_label=label,phases=[],reviewed_intervals=label.get('reviewed_intervals',[]))
    kind=label['event_type']
    if kind=='none':
        out['scoring_status']='explicit_reviewed_negative_fragments'
        return out
    scope='setup' if label.get('evaluation_interval_relation','').startswith('setup_departure') else 'post_lift' if kind=='held_lift_then_drop_after_lift' else 'unresolved'
    out['scoring_status']='physical_observation_outside_R1' if scope!='unresolved' else 'physical_observation_without_established_fall'
    def phase(suffix,type_name,phase_name,onset,last=None):
        if not all(isinstance(v,int) for v in onset):
            raise ValueError('Missing established sample onset bracket')
        out['phases'].append(dict(common,event_id=f'{eid}:{suffix}',compatible_type=type_name,
            phase=phase_name,scope=scope,status='established',onset_bracket=onset,
            interval=[onset[0],last if last is not None else onset[1]],
            offset_established_exact=False,physical_end_frame=None,
            endpoint_semantics='annotated sampled bounds; no exact physical endpoint inferred'))
    if scope=='setup':
        phase('departure','setup_departure','departure',[label['earliest_onset_frame'],label['latest_onset_frame']],label.get('landing_contact_frame'))
        if isinstance(label.get('landing_contact_frame'),int):
            contact=label['landing_contact_frame']
            phase('recorded_contact','contact','contact',[contact,contact],contact)
            out['phases'][-1]['offset_established_exact']=True
            out['phases'][-1]['endpoint_semantics']='first recorded contact sample; not exact physical landing'
    elif kind=='held_lift_then_drop_after_lift':
        type_map={'grasp_contact':('grasp','grasp'),'held_lift':('lift','lift'),'drop_after_lift':('post_lift_drop','release')}
        for i,s in enumerate(label['subevents']):
            typ,ph=type_map[s['event_type']]
            phase(f'subevent-{i}',typ,ph,[s['earliest_onset_frame'],s['latest_onset_frame']],s.get('last_sampled_holding_frame',s.get('first_recorded_table_contact_frame')))
        c=label['landing_contact_frame'];phase('recorded_contact','contact','contact',[c,c],c)
        out['phases'][-1]['offset_established_exact']=True
        out['phases'][-1]['endpoint_semantics']='first recorded table contact sample; not exact physical landing'
    return out

def compare(predictions,support,requirements,events,uncertainties):
    pmap={key(p):p for p in predictions}
    smap={key(r,True):r for r in support}
    rmap={key(r,True):r for r in requirements}
    if len(smap)!=len(support) or len(rmap)!=len(requirements) or set(smap)!=set(pmap) or set(rmap)!=set(pmap):
        raise ValueError('Reference identity mismatch')
    emap=defaultdict(list)
    normalized=[normalize_reference_event(e) for e in events]
    for e,n in zip(events,normalized):
        if key(e,True) not in pmap:
            raise ValueError('Unrecognized reference event identity')
        emap[key(e,True)].append(n)
    unresolved=[u for u in uncertainties if u['final']['resolution_status'] not in ['resolved_existing_evidence']]
    for u in uncertainties:
        if u['run_id'] not in {k[0] for k in pmap} or (u['object_id'] and u['object_id'] not in OBJECTS):
            raise ValueError('Unrecognized uncertainty identity')
    applicability={a:{b:0 for b in ['applies','does_not_apply','unknown']} for a in ['applies','does_not_apply','unknown']}
    cases=[];counts=Counter({k:0 for k in ['eligible_reference_units','reference_positives','non_applicable_units','compatible_domains','sampled_complete_units','scope_errors','applicability_determinate_errors','clean_units','clean_eligible_units','binary_compared_units','clean_binary_compared_units','eligible_abstentions']});reasons=Counter();binary=Counter({k:0 for k in ['TP','FP','FN','TN']})
    for k in sorted(pmap):
        p=pmap[k];s=smap[k]['final'];r=rmap[k]['final']
        sa={'direct_table':'applies','indirect_table':'applies','unsupported':'does_not_apply','insufficient_information':'unknown'}.get(s['support_label'])
        if sa is None or sa!=r['applicability'] or s['boundary_frame']!=10:
            raise ValueError('Reference support/applicability inconsistency')
        applicable=r['applicability'];applicability[applicable][p['applicability']]+=1
        windows=[w for e in emap[k] for w in e['reviewed_intervals']]
        reference_domain=[int(r['review_start_frame']),int(r['review_end_frame'])]
        linked=[u['adjudication_id'] for u in unresolved if u['run_id']==k[0] and (not u['object_id'] or u['object_id']==k[1])]
        eligible=applicable=='applies' and r['interpretation'] in ['violation','no_violation_observed_within_reviewed_coverage']
        sampled_complete=contained(reference_domain,p['measurement_frame_intervals'])
        compatible=p['compatible_reference_domain_established'] and contained(reference_domain,p['reviewed_frame_intervals'])
        determinate=p['applicability']=='applies' and p['outcome'] in ['violation','no_violation_observed_within_reviewed_coverage']
        counts['eligible_reference_units']+=eligible
        counts['reference_positives']+=eligible and r['interpretation']=='violation'
        counts['non_applicable_units']+=applicable=='does_not_apply'
        counts['compatible_domains']+=bool(compatible)
        counts['sampled_complete_units']+=sampled_complete
        counts['scope_errors']+=applicable=='does_not_apply' and p['outcome']=='violation'
        counts['applicability_determinate_errors']+=p['applicability']!='unknown' and p['applicability']!=applicable
        counts['clean_units']+=not linked
        counts['clean_eligible_units']+=not linked and eligible
        scored=eligible and compatible and determinate
        if scored:
            ref_pos=r['interpretation']=='violation';pred_pos=p['outcome']=='violation'
            binary['TP' if ref_pos and pred_pos else 'FN' if ref_pos else 'FP' if pred_pos else 'TN']+=1
            counts['binary_compared_units']+=1
            counts['clean_binary_compared_units']+=not linked
        elif eligible:
            counts['eligible_abstentions']+=1
            reasons[p['abstention_reason']]+=1
        cases.append({'run_id':k[0],'canonical_object_id':k[1],'requirement_version':k[2],
            'reference_support':s,'reference_requirement':r,
            'reference_reviewed_negative_windows':windows,
            'reference_observation_domain':reference_domain,
            'checker_applicability':p['applicability'],'checker_outcome':p['outcome'],
            'checker_candidate_initial_assessment':p['evidence']['initial_candidate_assessment'],
            'measurement_frame_intervals':p['measurement_frame_intervals'],
            'sampled_domain_complete':sampled_complete,'compatible_claim_domain':bool(compatible),
            'reference_eligible':eligible,'binary_compared':bool(scored),
            'abstention_reason':p['abstention_reason'],'unresolved_component_ids':linked,
            'candidate_event_ids':[e['event_id'] for e in p['events']]})
    # Only established R1 predictions/reference events enter event TP/FP/FN.
    # Adapter-v1 emits no established events: all 29 provisional candidates are
    # listed explicitly as unscorable; out-of-scope physical events stay separate.
    established_predictions=[]
    established_reference_r1=[]
    for n in normalized:
        for phase in n['phases']:
            if phase['compatible_type']=='r1_fall' and phase['scope']=='in_scope':
                established_reference_r1.append(phase)
    event_results={str(t):match_events(established_predictions,established_reference_r1,t) for t in [0,1]}
    candidates=[dict(run_id=p['run_id'],canonical_object_id=p['canonical_object_id'],event_id=e['event_id'],type=e['type'],phase=e['phase'],interval=e['interval'],reason='Provisional classification and unresolved scope; not a definitive R1 alarm') for p in predictions for e in p['events']]
    total=len(cases);eligible=counts['eligible_reference_units'];compared=counts['binary_compared_units']
    result={
        'total_units':total,'applicability_matrix_reference_rows_checker_columns':applicability,
        'counts':dict(counts),'binary_counts_on_determinate_compatible_subset':dict(binary),
        'binary_denominator':compared,
        'precision':None,'positive_class_recall':None,'positive_class_F1':None,
        'metric_explanation':'No determinate compatible predictions; precision undefined. Zero reference R1 positives: positive-class recall and F1 not estimable, including end-to-end recall.',
        'reference_eligibility_coverage':{'numerator':eligible,'denominator':total},
        'checker_decision_coverage':{'numerator':compared,'denominator':eligible},
        'abstention_rate':{'numerator':counts['eligible_abstentions'],'denominator':eligible},
        'eligible_abstention_reasons':dict(reasons),
        'all_unresolved_component_free_sensitivity':{'policy':'Exclude units with any linked partially unresolved request; blank object means run-wide. This conservative secondary restriction does not alter primary claim eligibility.',
            'units':counts['clean_units'],'eligible_units':counts['clean_eligible_units'],'binary_compared_units':counts['clean_binary_compared_units'],
            'abstentions':counts['clean_eligible_units']-counts['clean_binary_compared_units'],
            'unit_keys':[[c['run_id'],c['canonical_object_id']] for c in cases if not c['unresolved_component_ids']]},
        'event_localization':{'strict_and_one_frame':event_results,'established_R1_reference_events':len(established_reference_r1),
            'established_R1_prediction_events':len(established_predictions),'unscorable_candidates':candidates,
            'candidate_type_counts':dict(Counter(c['type'] for c in candidates)),
            'candidate_phase_counts':dict(Counter(c['phase'] for c in candidates)),
            'interpretation':'0 eligible R1 pairs at both tolerances; localization performance is not estimable. No physical-event candidate is counted as an R1 false positive. No event TNs.'},
        'reference_events':normalized,'cases':cases}
    return result

def score(args):
    if args.output.exists():raise FileExistsError(args.output)
    # Verify predictions and all copied execution artifacts *before* opening labels.
    seal=json.loads((args.execution/'PREDICTION_SEAL.json').read_text())
    if seal['reference_answers_loaded'] is not False:raise ValueError('Leakage control not asserted')
    missing=[]
    for name,expected in seal['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Unsafe seal path')
        p=args.execution/name
        if p.exists():
            if sha(p)!=expected:raise ValueError('Sealed artifact changed: '+name)
        else:
            if not (name.startswith('raw/episode_') and (name.endswith('_geometry_contacts.json.gz') or name.endswith('_observations.json.gz'))):
                raise ValueError('Required sealed artifact missing: '+name)
            missing.append(name)
    if 'predictions.json' not in seal['files'] or not (args.execution/'predictions.json').is_file():raise ValueError('Missing sealed predictions')
    protocol=json.loads((HERE/'protocol.json').read_text())
    manifest=json.loads((HERE/'recordings.json').read_text())
    predictions=json.loads((args.execution/'predictions.json').read_text())
    validate_predictions(predictions,manifest,protocol)
    freeze=json.loads((HERE/'baseline_freeze.json').read_text())
    repo=HERE.parents[1]
    for name,expected in freeze['protected_files'].items():
        if sha(repo/name)!=expected:raise ValueError('Protected reference/reviewer file changed: '+name)
    # Internal immutable reference checksums are independently checked.
    for line in (args.reference/'SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split(maxsplit=1)
        if sha(args.reference/name)!=expected:raise ValueError('Reference checksum mismatch: '+name)
    # Summary loaded first, before denominators are computed.
    summary=json.loads((args.reference/'adjudication_summary.json').read_text())
    support=read_final(args.reference/'adjudicated_initial_support.csv')
    reqs=read_final(args.reference/'adjudicated_requirement_interpretation.csv')
    events=read_final(args.reference/'adjudicated_events.csv')
    uncertainty=read_final(args.reference/'adjudicated_uncertainty_requests.csv')
    result=compare(predictions,support,reqs,events,uncertainty)
    actual=dict(Counter(r['final']['interpretation'] for r in reqs))
    if actual!=summary['requirement_interpretation_counts']:raise ValueError('Summary/final labels disagree')
    result['provenance']={'prediction_sha256':sha(args.execution/'predictions.json'),
        'prediction_seal_sha256':sha(args.execution/'PREDICTION_SEAL.json'),
        'reference_directory':str(args.reference),'reference_final_csv_sha256':{p.name:sha(p) for p in sorted(args.reference.glob('adjudicated_*.csv'))},
        'not_copied_from_remote':missing,'remote_execution_root':'/disk/1/data/niktakbr/r1-reference-evaluation-20261027/predictions',
        'scorer_sha256':sha(Path(__file__)),'matcher_sha256':sha(HERE/'matching.py')}
    dump(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['cases','reference_events','event_localization']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execution',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    score(p.parse_args())
