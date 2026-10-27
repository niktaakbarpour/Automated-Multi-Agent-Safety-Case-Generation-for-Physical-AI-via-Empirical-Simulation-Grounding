"""Positive-capable scoring of already sealed V3, gated on approved frozen humans."""
import argparse
import json
import sys
from collections import Counter,defaultdict
from pathlib import Path
from workflow import HERE,TABLES,sha,save,reference_rows,cases
sys.path.insert(0,str(HERE/'scoring_support'))
from matching import contained,match_events


def key(row):return row['run_id'],row.get('canonical_object_id',row.get('object_id')),row['requirement_version']


def verify_reference(reference,assignment):
    seal=json.loads((reference/'REFERENCE_SEAL.json').read_text())
    if seal.get('approved') is not True or seal.get('prediction_inputs_used') is not False or seal['assignment_sha256']!=sha(assignment):raise ValueError('Reference is not approved/frozen for this assignment')
    required={f'adjudicated_{t}.csv' for t in TABLES}|{'APPROVAL.json','SOURCE_RECEIPTS.json'}
    if set(seal['files'])!=required:raise ValueError('Incomplete reference seal')
    for n,h in seal['files'].items():
        if sha(reference/n)!=h:raise ValueError('Frozen reference changed: '+n)
    approval=json.loads((reference/'APPROVAL.json').read_text());receipts=json.loads((reference/'SOURCE_RECEIPTS.json').read_text())
    if approval.get('approval_decision')!='approve' or approval.get('independent_submissions_confirmed') is not True or not all(approval.get(k,'').strip() for k in ['adjudicator_identity','approval_date','approval_statement']):raise ValueError('Missing explicit independent human approval')
    if approval['assignment_sha256']!=sha(assignment) or approval['adjudication_hashes']!={n:seal['files'][n] for n in required if n.startswith('adjudicated_')}:raise ValueError('Approval/hash mismatch')
    if set(receipts)!={'reviewer_1','reviewer_2'} or any(not r['complete'] for r in receipts.values()):raise ValueError('Missing two complete independent source receipts')
    if approval['submission_hashes']!={k:r['submission_sha256'] for k,r in receipts.items()}:raise ValueError('Original independent source hashes not bound')
    if set(receipts['reviewer_1']['reviewer_identities'])&set(receipts['reviewer_2']['reviewer_identities']):raise ValueError('Independent reviewer identities overlap')
    expected={c['run_id']:c['recording_sha256'] for c in cases(assignment).values()}
    if seal['recordings']!=expected:raise ValueError('Reference recording identity mismatch')
    data=reference_rows(reference,assignment)
    if any(r['adjudicator_identity']!=approval['adjudicator_identity'] for rr in data.values() for r in rr):raise ValueError('Approval identity mismatch')
    return data,seal


def normalized_events(rows,allowed):
    phases=[];unscorable=[];negative=defaultdict(list)
    for row in rows:
        label=row['final'];identity=dict(run_id=row['run_id'],canonical_object_id=row['object_id'],requirement_version=row['requirement_version'])
        if label['observation_status']=='no_event_observed_in_window':
            negative[key(identity)].extend(label.get('reviewed_intervals',[]))
        components=label.get('subevents',[label])
        for i,component in enumerate(components):
            mapping=component.get('evaluation_mapping')
            if not mapping or component.get('observation_status',label['observation_status'])!='observed' or component.get('fall_status')=='insufficient_information':
                if label['observation_status']!='no_event_observed_in_window':unscorable.append(dict(adjudication_id=row['adjudication_id'],component=i,reason='No explicit approved determinate phase mapping',final_label=component))
                continue
            typ=mapping.get('compatible_type');scope=mapping.get('scope');phase=mapping.get('phase')
            onset=mapping.get('onset_bracket');interval=mapping.get('interval')
            if typ not in allowed or scope not in ['in_scope','setup','post_lift'] or not phase or not onset or not interval:
                unscorable.append(dict(adjudication_id=row['adjudication_id'],component=i,reason='Incomplete/unknown approved phase mapping',final_label=component));continue
            if len(onset)!=2 or len(interval)!=2 or any(type(n) is not int for pair in [onset,interval] for n in pair):
                unscorable.append(dict(adjudication_id=row['adjudication_id'],component=i,reason='Unknown approved localization bounds; no exact times invented',final_label=component));continue
            if onset[0]>onset[1] or interval[0]>interval[1]:raise ValueError('Malformed approved event bounds')
            phases.append(dict(identity,event_id=row['adjudication_id']+f':phase:{i}',reference_group_id=row['adjudication_id'],compatible_type=typ,phase=phase,scope=scope,status='established',onset_bracket=onset,interval=interval,offset_established_exact=mapping.get('offset_established_exact',False),final_component=component))
    return phases,negative,unscorable


def compare(predictions,data,selection,protocol):
    pm={key(p):p for p in predictions};rm={key(r):r for r in data['requirement_interpretation']};sm={key(r):r for r in data['initial_support']}
    expected={(c['run_id'],c['object_id'],protocol['requirement_version']) for c in selection.values()}
    if set(rm)!=expected or set(sm)!=expected or len(rm)!=len(data['requirement_interpretation']) or len(sm)!=len(data['initial_support']):raise ValueError('Incomplete/duplicate reference identity set')
    if not expected<=set(pm) or len(pm)!=len(predictions):raise ValueError('Missing/duplicate sealed prediction identities')
    matrix={a:{b:0 for b in ['applies','does_not_apply','insufficient_information']} for a in ['applies','does_not_apply','insufficient_information']}
    counts=Counter({n:0 for n in ['total_units','reference_applicable','reference_non_applicable','reference_unknown','eligible_reference','reference_positive_eligible','compared','abstentions','scope_errors','applicability_incorrect','uncovered_domains','operational_positive_hits','reference_unknown_with_determinate_prediction']})
    binary=Counter({n:0 for n in ['TP','FP','FN','TN']});case_results=[]
    for k in sorted(expected):
        p=pm[k];r=rm[k]['final'];support=sm[k]['final'];app=r['applicability']
        expected_app={'direct_table':'applies','indirect':'applies','unsupported':'does_not_apply','uncertain':'insufficient_information'}[support['support_label']]
        if app!=expected_app:raise ValueError('Adjudicated initial support/R1 applicability inconsistent')
        matrix[app][p['applicability']]+=1;counts['total_units']+=1
        counts['reference_applicable']+=app=='applies';counts['reference_non_applicable']+=app=='does_not_apply';counts['reference_unknown']+=app=='insufficient_information'
        counts['applicability_incorrect']+=app!='insufficient_information' and p['applicability']!='insufficient_information' and p['applicability']!=app
        counts['reference_unknown_with_determinate_prediction']+=app=='insufficient_information' and p['applicability']!='insufficient_information'
        counts['scope_errors']+=app=='does_not_apply' and p['outcome']=='violation'
        eligible=app=='applies' and r['interpretation'] in ['violation','no_violation_observed_within_reviewed_coverage']
        intervals=r.get('reviewed_intervals',[])
        measured=bool(intervals) and all(contained(pair,p['measurement_frame_intervals']) for pair in intervals)
        definite=p['applicability']=='applies' and p['outcome'] in ['violation','no_violation_observed_within_reviewed_coverage']
        proof=True
        if p['outcome']=='no_violation_observed_within_reviewed_coverage':proof=all(contained(pair,p['applicable_observation_intervals']) for pair in intervals)
        if p['outcome']=='violation':proof=any(e['type']=='r1_fall' and e['scope']=='in_scope' and contained(e['interval'],intervals) for e in p['events'])
        compatible=measured and proof and r.get('observation_domain')=='saved_frame_projection'
        scored=eligible and definite and compatible
        counts['eligible_reference']+=eligible;counts['reference_positive_eligible']+=eligible and r['interpretation']=='violation'
        counts['compared']+=scored;counts['abstentions']+=eligible and not scored;counts['uncovered_domains']+=eligible and not compatible
        if scored:
            rp=r['interpretation']=='violation';pp=p['outcome']=='violation';binary['TP' if rp and pp else 'FN' if rp else 'FP' if pp else 'TN']+=1
            counts['operational_positive_hits','reference_unknown_with_determinate_prediction']+=rp and pp
        exclusion=None if scored else 'reference_not_applicable' if app=='does_not_apply' else 'reference_uncertain' if not eligible else 'incompatible_observation_domain' if not compatible else 'checker_non_applicability_or_unknown_applicability' if p['applicability']!='applies' else 'explicit_checker_abstention'
        case_results.append(dict(comparison_exclusion_reason=exclusion,run_id=k[0],object_id=k[1],reference=r,initial_support=support,predicted_applicability=p['applicability'],predicted_outcome=p['outcome'],reference_eligible=eligible,compatible_domain=compatible,compared=bool(scored),abstention_reason=p.get('abstention_reason') if not scored else None,reviewed_intervals=intervals))
    refs,negatives,unscorable=normalized_events(data['events'],protocol['compatible_types'])
    predicted=[e for k in expected for e in pm[k]['events'] if e.get('status')=='established' and e.get('compatible_type') in protocol['compatible_types']]
    ref_r1=[e for e in refs if e['compatible_type']=='r1_fall' and e['scope']=='in_scope' and rm[key(e)]['final']['applicability']=='applies']
    pred_r1=[e for e in predicted if e['compatible_type']=='r1_fall' and e['scope']=='in_scope' and pm[key(e)]['applicability']=='applies' and rm[key(e)]['final']['applicability']=='applies']
    outside_ref=[e for e in refs if e['scope'] in ['setup','post_lift']]
    outside_pred=[e for e in predicted if e['scope'] in ['setup','post_lift']]
    unscorable_predictions=[dict(run_id=k[0],object_id=k[1],event=e) for k in expected for e in pm[k]['events'] if e.get('status')!='established' or e.get('compatible_type') not in protocol['compatible_types'] or e.get('scope')=='unresolved']
    tag_inconsistencies=[dict(run_id=k[0],object_id=k[1],event_id=e['event_id']) for k in expected if pm[k]['applicability']!='applies' for e in pm[k]['events'] if e.get('compatible_type')=='r1_fall' and e.get('scope')=='in_scope']
    localization={}
    for tol in [0,1]:
        m=match_events(pred_r1,ref_r1,tol);fp=[];unknown=[]
        for eid in m['unmatched_predictions']:
            e=next(e for e in pred_r1 if e['event_id']==eid)
            (fp if contained(e['interval'],negatives[key(e)]) else unknown).append(eid)
        localization[str(tol)]=dict(scorable_R1_reference_events=len(ref_r1),scorable_R1_prediction_events=len(pred_r1),outside_R1_reference_phases=len(outside_ref),outside_R1_prediction_phases=len(outside_pred),R1_matching=m,event_TP=len(m['matches']),event_FN=len(m['unmatched_references']),adjudicable_event_FP_ids=fp,unscorable_unmatched_prediction_ids=unknown,outside_R1_physical_diagnostic=match_events(outside_pred,outside_ref,tol))
    unresolved=set()
    for row in data['uncertainty_requests']:
        label=row['final']
        if label.get('resolution_status') not in ['resolved_existing_evidence','resolved']:
            if row['object_id']:unresolved.add(key(row))
            else:unresolved.update(k for k in expected if k[0]==row['run_id'])
    for table in TABLES:
        for row in data[table]:
            if row['final'].get('unresolved_components'):unresolved.add(key(row))
    clean=[c for c in case_results if (c['run_id'],c['object_id'],protocol['requirement_version']) not in unresolved]
    positive=counts['reference_positive_eligible'];den=binary['TP']+binary['FP'];recden=binary['TP']+binary['FN']
    return dict(counts=dict(counts),applicability_confusion=matrix,binary_counts=dict(binary),
        decision_coverage=dict(numerator=counts['compared'],denominator=counts['eligible_reference']),
        precision=binary['TP']/den if den else None,
        positive_class_recall=binary['TP']/recden if positive and recden else None,
        positive_class_F1=2*binary['TP']/(2*binary['TP']+binary['FP']+binary['FN']) if positive and (2*binary['TP']+binary['FP']+binary['FN']) else None,
        end_to_end_positive_recall=counts['operational_positive_hits','reference_unknown_with_determinate_prediction']/positive if positive else None,
        uncertainty_free_sensitivity=dict(units=len(clean),eligible=sum(c['reference_eligible'] for c in clean),compared=sum(c['compared'] for c in clean)),
        cases=case_results,localization=localization,unscorable_reference_phases=unscorable,unscorable_prediction_events=unscorable_predictions,event_scope_tag_inconsistencies=tag_inconsistencies,
        original_final_events=data['events'],original_final_uncertainties=data['uncertainty_requests'],
        limitations='Only independently approved sampled reference cases; shared saved-frame projection, not continuous-time safety. No positive recall/F1 estimate with zero positive references. Non-applicability and abstention never add TNs.')


def score(args):
    if args.out.exists():raise FileExistsError(args.out)
    # This gate intentionally precedes *all* prediction reads.
    data,refseal=verify_reference(args.reference,args.assignments)
    code_freeze=json.loads((HERE/'SCORING_FREEZE.json').read_text())
    if sha(args.assignments)!=code_freeze['files']['COORDINATOR_ASSIGNMENTS.json']:raise ValueError('Scoring assignments differ from the preregistered 20-case sample')
    for n,h in code_freeze['files'].items():
        if sha(HERE/n)!=h:raise ValueError('Scoring code/protocol changed after prereview freeze')
    protocol=json.loads((HERE/'SCORING_PROTOCOL.json').read_text())
    pseal=json.loads(args.predictions.with_name('PREDICTION_SEAL.json').read_text())
    if sha(args.predictions)!=protocol['prediction_sha256'] or pseal['files']['predictions.json']!=protocol['prediction_sha256']:raise ValueError('Not the already frozen V3 prediction file')
    predictions=json.loads(args.predictions.read_text());selected=cases(args.assignments)
    for p in predictions:
        if (p['run_id'],p['canonical_object_id']) not in {(c['run_id'],c['object_id']) for c in selected.values()}:continue
        c=next(c for c in selected.values() if (c['run_id'],c['object_id'])==(p['run_id'],p['canonical_object_id']))
        if p['recording_sha256']!=c['recording_sha256'] or p['checker_sha256']!=protocol['checker_sha256'] or p['configuration_sha256']!=protocol['configuration_sha256'] or p['requirement_version']!=protocol['requirement_version']:raise ValueError('Frozen prediction source/config/identity mismatch')
    result=compare(predictions,data,selected,protocol)
    result['provenance']=dict(reference_seal_sha256=sha(args.reference/'REFERENCE_SEAL.json'),prediction_sha256=sha(args.predictions),assignment_sha256=sha(args.assignments),scoring_protocol_sha256=sha(HERE/'SCORING_PROTOCOL.json'),scorer_sha256=sha(Path(__file__)))
    save(args.out,result);print(json.dumps(result['counts'],indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--assignments',type=Path,default=HERE/'COORDINATOR_ASSIGNMENTS.json');p.add_argument('--predictions',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    score(p.parse_args())
