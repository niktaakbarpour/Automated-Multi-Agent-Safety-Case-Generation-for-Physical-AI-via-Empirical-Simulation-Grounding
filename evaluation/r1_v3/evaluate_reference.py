"""Evaluate immutable v3 outputs; never supplies labels to the checker.

Primary binary domain is the predeclared shared saved-frame projection.
Physical outside-R1 localization is diagnostic, separate from R1 event scoring.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'r1_reference'))
from score import read_final,normalize_reference_event
from matching import contained,match_events
from execute import sha,save


def identity(row,ref=False):
    return row['run_id'],row['object_id' if ref else 'canonical_object_id'],row['requirement_version']


def verify(execution,repo):
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for name,digest in freeze['implementation_files'].items():
        if sha(HERE/name)!=digest:raise ValueError('Frozen v3 implementation changed: '+name)
    seal=json.loads((execution/'PREDICTION_SEAL.json').read_text())
    if seal['reference_answers_loaded'] is not False:raise ValueError('Prediction provenance lacks label-input exclusion')
    absent=[]
    for name,digest in seal['files'].items():
        if Path(name).name!=name:raise ValueError('Unsafe seal path')
        path=execution/name
        if path.exists():
            if sha(path)!=digest:raise ValueError('Sealed prediction artifact changed: '+name)
        elif name.startswith('episode_') and name.endswith('_facts.json.gz'):absent.append(name)
        else:raise ValueError('Missing sealed prediction artifact: '+name)
    for name in ['predictions.json','receipts.json','runtime.json','errors.json']:
        if name not in seal['files']:raise ValueError('Unsealed required artifact')
    baseline=json.loads((HERE.parent/'r1_reference/baseline_freeze.json').read_text())
    for name,digest in {**baseline['protected_files'],**baseline['files']}.items():
        if sha(repo/name)!=digest:raise ValueError('Protected/baseline artifact changed: '+name)
    receipts=json.loads((execution/'receipts.json').read_text())
    if len(receipts)!=8 or any(r['before']!=r['after'] for r in receipts):raise ValueError('Original recording preservation failure')
    manifest=json.loads((HERE.parent/'r1_reference/recordings.json').read_text())
    config=json.loads((HERE/'config.json').read_text())
    expected={(r['run_id'],o,config['requirement_version']) for r in manifest['runs'] for o in config['objects']}
    predictions=json.loads((execution/'predictions.json').read_text())
    keys=[identity(p) for p in predictions]
    if len(set(keys))!=len(keys) or set(keys)!=expected:raise ValueError('Missing, duplicate or incompatible prediction identities')
    runs={r['run_id']:r for r in manifest['runs']}
    for p in predictions:
        r=runs[p['run_id']]
        if p['recording_sha256']!=r['recording_sha256'] or p['requested_frame_interval']!=[10,r['last_frame']]:raise ValueError('Recording/observation domain mismatch')
        if p['source_commit']!=freeze['source_commit'] or p['checker_version']!=config['checker_version'] or p['configuration_sha256']!=sha(HERE/'config.json') or p['implementation_freeze_sha256']!=sha(HERE/'FREEZE.json'):raise ValueError('Checker/configuration provenance mismatch')
        if p['facts_sha256']!=seal['files'][r['episode']+'_facts.json.gz']:raise ValueError('Evidence provenance mismatch')
        if p['applicability'] not in ['applies','does_not_apply','insufficient_information'] or p['outcome'] not in ['violation','no_violation_observed_within_reviewed_coverage','not_applicable','insufficient_information']:raise ValueError('Invalid decision vocabulary')
        if (p['applicability']=='does_not_apply')!=(p['outcome']=='not_applicable'):raise ValueError('Inconsistent applicability/outcome')
    return predictions,manifest,absent


def compare(predictions,requirements,support,events,uncertainty,baseline):
    pmap={identity(p):p for p in predictions};rmap={identity(r,True):r for r in requirements};smap={identity(s,True):s for s in support}
    if len(rmap)!=len(requirements) or len(smap)!=len(support) or set(pmap)!=set(rmap) or set(pmap)!=set(smap):raise ValueError('Reference identity mismatch')
    normalized=[normalize_reference_event(e) for e in events]
    emap=defaultdict(list)
    for e in normalized:
        if identity(e) not in pmap:raise ValueError('Unknown reference event identity')
        emap[identity(e)].append(e)
    matrix={a:{b:0 for b in ['applies','does_not_apply','insufficient_information']} for a in ['applies','does_not_apply','insufficient_information']}
    binary=Counter({k:0 for k in ['TP','FP','FN','TN']})
    c=Counter({k:0 for k in ['applicable_reference','non_applicable_reference','reference_positives','applicability_decisions','applicable_correct','non_applicable_correct','applicability_incorrect','applicability_unknown','outcome_determinate_applicable','binary_compared','eligible_abstentions','domain_incompatible_eligible','scope_errors','R1_alarms','false_R1_alarms','missing_outputs','clean_units','clean_eligible','clean_compared','clean_abstentions']})
    cases=[]
    unresolved=[u for u in uncertainty if u['final']['resolution_status']=='partially_resolved']
    for k,p in sorted(pmap.items()):
        r=rmap[k]['final'];s=smap[k]['final'];app=r['applicability']
        expected={'direct_table':'applies','indirect_table':'applies','unsupported':'does_not_apply'}.get(s['support_label'],'insufficient_information')
        if expected!=app or s['boundary_frame']!=10:raise ValueError('Inconsistent reference support/applicability')
        matrix[app][p['applicability']]+=1
        determinate=p['applicability']!='insufficient_information'
        c['applicability_decisions']+=determinate;c['applicability_unknown']+=not determinate
        c['applicability_incorrect']+=determinate and p['applicability']!=app
        c['applicable_correct']+=app=='applies' and p['applicability']=='applies'
        c['non_applicable_correct']+=app=='does_not_apply' and p['applicability']=='does_not_apply'
        eligible=app=='applies' and r['interpretation'] in ['violation','no_violation_observed_within_reviewed_coverage']
        c['applicable_reference']+=eligible;c['non_applicable_reference']+=app=='does_not_apply'
        c['reference_positives']+=eligible and r['interpretation']=='violation'
        c['R1_alarms']+=p['outcome']=='violation'
        c['scope_errors']+=app=='does_not_apply' and p['outcome']=='violation'
        domain=[int(r['review_start_frame']),int(r['review_end_frame'])]
        ref_windows=[w for e in emap[k] for w in e['reviewed_intervals']]
        measurement_complete=contained(domain,p['measurement_frame_intervals'])
        ref_negative_complete=contained(domain,ref_windows)
        proof_complete=contained(domain,p['applicable_observation_intervals'])
        definite=p['applicability']=='applies' and p['outcome'] in ['violation','no_violation_observed_within_reviewed_coverage']
        # This reference has only qualified negative applicable outcomes. A future
        # positive reference requires a new frozen evaluability protocol.
        compatible=bool(eligible and p['requested_frame_interval']==domain and measurement_complete and ref_negative_complete and (proof_complete or p['outcome']=='violation'))
        scored=bool(compatible and definite)
        c['outcome_determinate_applicable']+=eligible and definite
        c['binary_compared']+=scored;c['eligible_abstentions']+=eligible and not scored
        c['domain_incompatible_eligible']+=eligible and not compatible
        linked=[u['adjudication_id'] for u in unresolved if u['run_id']==k[0] and (not u['object_id'] or u['object_id']==k[1])]
        c['clean_units']+=not linked;c['clean_eligible']+=eligible and not linked
        c['clean_compared']+=scored and not linked;c['clean_abstentions']+=eligible and not scored and not linked
        if scored:
            rp=r['interpretation']=='violation';pp=p['outcome']=='violation'
            label='TP' if rp and pp else 'FN' if rp else 'FP' if pp else 'TN'
            binary[label]+=1;c['false_R1_alarms']+=label=='FP'
        cases.append(dict(run_id=k[0],canonical_object_id=k[1],requirement_version=k[2],
            reference_support=s,reference_requirement=r,reference_negative_windows=ref_windows,
            checker_support_class=p['initial_support']['support_class'],checker_applicability=p['applicability'],checker_outcome=p['outcome'],
            measurement_frame_intervals=p['measurement_frame_intervals'],checker_negative_windows=p['applicable_observation_intervals'],
            observation_domain='shared_saved_frame_projection_only',reference_eligible=eligible,
            measurement_complete=measurement_complete,reference_negative_domain_complete=ref_negative_complete,
            checker_negative_domain_complete=proof_complete,compatible=compatible,binary_scored=scored,
            abstention_reason=p['abstention_reason'],unresolved_component_ids=linked,
            event_ids=[e['event_id'] for e in p['events']]))
    physical_types={'setup_departure','post_lift_drop','lift','grasp','contact'}
    physical_pred=[e for p in predictions for e in p['events'] if e['status']=='established' and e['compatible_type'] in physical_types and e['scope'] in ['setup','post_lift']]
    physical_ref=[e for n in normalized for e in n['phases'] if e['compatible_type'] in physical_types and e['scope'] in ['setup','post_lift']]
    r1_pred=[e for p in predictions if p['applicability']=='applies' for e in p['events'] if e['type']=='r1_fall' and e['scope']=='in_scope']
    r1_ref=[e for n in normalized for e in n['phases'] if e['compatible_type']=='r1_fall' and e['scope']=='in_scope']
    localization={str(t):{'R1':match_events(r1_pred,r1_ref,t),'outside_R1_physical_diagnostic':match_events(physical_pred,physical_ref,t)} for t in [0,1]}
    unscorable=[dict(run_id=p['run_id'],canonical_object_id=p['canonical_object_id'],event=e) for p in predictions for e in p['events'] if e not in physical_pred and e not in r1_pred]
    comparisons=[
        ['R1 applicability decision coverage',f"{baseline['total_units']-sum(row['unknown'] for row in baseline['applicability_matrix_reference_rows_checker_columns'].values())}/{baseline['total_units']}",f"{c['applicability_decisions']}/{len(predictions)}"],
        ['Applicable cases correctly classified',f"{baseline['applicability_matrix_reference_rows_checker_columns']['applies']['applies']}/{baseline['counts']['eligible_reference_units']}",f"{c['applicable_correct']}/{c['applicable_reference']}"],
        ['Non-applicable cases correctly classified',f"{baseline['applicability_matrix_reference_rows_checker_columns']['does_not_apply']['does_not_apply']}/{baseline['counts']['non_applicable_units']}",f"{c['non_applicable_correct']}/{c['non_applicable_reference']}"],
        ['Unknown applicability outputs',str(sum(row['unknown'] for row in baseline['applicability_matrix_reference_rows_checker_columns'].values())),str(c['applicability_unknown'])],
        ['R1 binary decision coverage',f"{baseline['binary_denominator']}/{baseline['counts']['eligible_reference_units']}",f"{c['binary_compared']}/{c['applicable_reference']}"],
        ['False R1 alarms on compatible negatives',f"{baseline['binary_counts_on_determinate_compatible_subset']['FP']} (0 evaluated)",f"{binary['FP']} ({c['binary_compared']} evaluated)"],
        ['Applicable-case abstention rate',f"{baseline['counts']['eligible_abstentions']}/{baseline['counts']['eligible_reference_units']}",f"{c['eligible_abstentions']}/{c['applicable_reference']}"],
        ['Confirmed R1 violation recall','Not estimable','Not estimable']]
    return dict(total_units=len(predictions),counts=dict(c),applicability_matrix=matrix,
        binary_counts=dict(binary),binary_denominator=c['binary_compared'],
        precision=binary['TP']/(binary['TP']+binary['FP']) if binary['TP']+binary['FP'] else None,positive_class_recall=None,positive_class_F1=None,
        metrics_qualification='No positive R1 reference cases. Recall and positive F1 not estimable. Precision is undefined when there are no positive predictions. Agreements on qualified negatives cannot establish general detector accuracy.',
        comparison_table=comparisons,cases=cases,reference_events=normalized,
        uncertainty_requests=[dict(adjudication_id=u['adjudication_id'],run_id=u['run_id'],object_id=u['object_id'],final_label=u['final']) for u in uncertainty],
        localization=localization,unscorable_events=unscorable,
        physical_matching_denominators=dict(predicted_phases=len(physical_pred),reference_phases=len(physical_ref)),
        event_type_counts=dict(Counter(e['type'] for p in predictions for e in p['events'])))


def main(args):
    if args.output.exists():raise FileExistsError(args.output)
    repo=HERE.parents[1]
    predictions,manifest,absent=verify(args.execution,repo)
    # Labels are read only after verifying the sealed predictions.
    for line in (args.reference/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split(maxsplit=1)
        if sha(args.reference/name)!=digest:raise ValueError('Approved reference checksum mismatch')
    summary=json.loads((args.reference/'adjudication_summary.json').read_text())
    req=read_final(args.reference/'adjudicated_requirement_interpretation.csv')
    if dict(Counter(r['final']['interpretation'] for r in req))!=summary['requirement_interpretation_counts']:raise ValueError('Reference summary mismatch')
    if any(r['final']['interpretation']=='violation' for r in req):raise ValueError('New positive reference requires a new predeclared evaluability policy')
    support=read_final(args.reference/'adjudicated_initial_support.csv')
    events=read_final(args.reference/'adjudicated_events.csv')
    uncertainty=read_final(args.reference/'adjudicated_uncertainty_requests.csv')
    baseline=json.loads((HERE.parent/'r1_reference/results.json').read_text())
    result=compare(predictions,req,support,events,uncertainty,baseline)
    result['provenance']=dict(prediction_sha256=sha(args.execution/'predictions.json'),seal_sha256=sha(args.execution/'PREDICTION_SEAL.json'),
        source_commit=json.loads((HERE/'FREEZE.json').read_text())['source_commit'],config_sha256=sha(HERE/'config.json'),
        scorer_sha256=sha(Path(__file__)),matcher_sha256=sha(HERE.parent/'r1_reference/matching.py'),
        remote_only_fact_artifacts=absent,remote_execution='/disk/1/data/niktakbr/r1-checker-v3-20261027/execution',
        reference_hashes={p.name:sha(p) for p in sorted(args.reference.glob('adjudicated_*.csv'))})
    save(args.output,result)
    print(json.dumps({k:result[k] for k in ['counts','binary_counts','applicability_matrix','comparison_table','physical_matching_denominators']},indent=2))
    for t,l in result['localization'].items():
        print('Tolerance',t,'physical matches',len(l['outside_R1_physical_diagnostic']['matches']),
              'unmatched predictions',l['outside_R1_physical_diagnostic']['unmatched_predictions'],
              'unmatched references',l['outside_R1_physical_diagnostic']['unmatched_references'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execution',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
