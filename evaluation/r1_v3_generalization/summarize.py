"""Descriptive audit only. No new-run accuracy without approved human labels."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()


def summarize(root):
    seal=json.loads((root/'execution/PREDICTION_SEAL.json').read_text())
    missing=[]
    for n,h in seal['files'].items():
        p=root/'execution'/n
        if p.exists():
            if sha(p)!=h:raise ValueError('Sealed artifact mismatch: '+n)
        elif n.endswith('_facts.json.gz'):missing.append(n)
        else:raise ValueError('Missing required artifact: '+n)
    predictions=json.loads((root/'execution/predictions.json').read_text())
    inventory=json.loads((root/'inventory/inventory.json').read_text())['records']
    inputs=json.loads((root/'INPUTS.json').read_text())
    expected={(r['run_id'],o) for r in inputs['records'] for o in ['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']}
    keys=[(p['run_id'],p['canonical_object_id']) for p in predictions]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:raise ValueError('Missing/duplicate/incompatible prediction identity')
    partitions={}
    for name in ['same_task_reserved','cross_task_same_scene']:
        ps=[p for p in predictions if p['partition']==name]
        applicable=[p for p in ps if p['applicability']=='applies']
        determinate=[p for p in applicable if p['outcome'] in ['violation','no_violation_observed_within_reviewed_coverage']]
        inconsistencies=[dict(run_id=p['run_id'],object_id=p['canonical_object_id'],event_id=e['event_id']) for p in ps if p['applicability']!='applies' for e in p['events'] if e['type']=='r1_fall' and e['scope']=='in_scope']
        partitions[name]=dict(executions=len({p['run_id'] for p in ps}),object_units=len(ps),predicted_applicability=dict(collections.Counter(p['applicability'] for p in ps)),
            predicted_outcomes=dict(collections.Counter(p['outcome'] for p in ps)),predicted_applicable_units=len(applicable),
            determinate_outcomes_given_predicted_applicability=len(determinate),predicted_applicable_abstentions=len(applicable)-len(determinate),
            operational_decision_coverage=dict(numerator=len(determinate),denominator=len(applicable)),
            abstention_reasons=dict(collections.Counter(p['abstention_reason'] for p in applicable if p['outcome']=='insufficient_information')),
            raw_R1_alarm_outputs=sum(p['outcome']=='violation' for p in ps),event_type_counts=dict(collections.Counter(e['type'] for p in ps for e in p['events'])),
            lift_objects=dict(collections.Counter(p['canonical_object_id'] for p in ps for e in p['events'] if e['type']=='lift')),
            post_lift_drop_objects=dict(collections.Counter(p['canonical_object_id'] for p in ps for e in p['events'] if e['type']=='post_lift_drop')),
            event_scope_inconsistency_cases=inconsistencies,independently_reviewed_units=0,accuracy_evaluation='pending independent human reference',
            reference_applicable=None,reference_non_applicable=None,applicability_confusion=None,coverage_compatible_binary_counts=dict(TP=None,FP=None,FN=None,TN=None),
            false_alarm_rate=None,positive_recall=None,positive_class_F1=None,physical_localization_accuracy=None)
    duplicates={}
    for field in ['receipts_before','trajectory_payload_sha256','protected_geometry_stream_sha256','setup_qpos_sha256']:
        groups=collections.defaultdict(list)
        for row in inventory:
            if row['partition']=='cross_scene_preflight':continue
            h=row['receipts_before'][0]['sha256'] if field=='receipts_before' else row.get(field)
            if h:groups[h].append(row['run_id'])
        duplicates[field]=dict(records=sum(map(len,groups.values())),unique=len(groups),duplicate_groups=[v for v in groups.values() if len(v)>1])
    models=collections.defaultdict(list)
    for row in inventory:
        if row.get('metadata'):
            m=row['metadata'];signature=json.dumps({k:m[k] for k in ['checkpoint','checkpoint_revision','checkpoint_weight_sha256']},sort_keys=True)
            models[hashlib.sha256(signature.encode()).hexdigest()].append(row['run_id'])
    logs=json.loads((root/'execution/access_log.json').read_text())
    examples=[]
    selections=[('same_task_reserved',4,'cream_cheese_1'),('cross_task_same_scene',0,'cream_cheese_1'),('cross_task_same_scene',0,'butter_1')]
    for partition,ep,obj in selections:
        p=next(p for p in predictions if p['partition']==partition and f'trial{ep:03d}_' in p['run_id'] and p['canonical_object_id']==obj)
        examples.append(dict(run_id=p['run_id'],object_id=obj,applicability=p['applicability'],outcome=p['outcome'],requested_frame_interval=p['requested_frame_interval'],negative_windows=p['applicable_observation_intervals'],events=[e for e in p['events'] if e['type'] in ['lift','post_lift_drop','uncertain_descent']],abstention_reason=p['abstention_reason']))
    preflights=[r for r in inventory if r['partition']=='cross_scene_preflight']
    metadata_index={r['run_id']:r for r in inventory}
    model_config_mismatches=[r['run_id'] for r in inputs['records'] if metadata_index[r['run_id']]['metadata']['model_configuration_id']!=r['source_model_configuration_id']]
    return dict(partitions=partitions,duplicates=duplicates,metadata_checkpoint_signature_groups={k:len(v) for k,v in models.items()},
        model_weight_qualification='Attested checkpoint hashes in rehashed metadata; weight binaries not rehashed or executed.',model_configuration_id_catalog_mismatches=model_config_mismatches,
        cross_scene_preflight=dict(tasks=len(preflights),eligible=sum(r['eligible'] for r in preflights),all_blockers=dict(collections.Counter(r.get('preflight_blocker','none') for r in preflights)),examples=[{k:r.get(k) for k in ['run_id','task_id','native_geom_count','named_table_present','scope_missing_objects','preflight_blocker']} for r in preflights if r['suite']=='long' and r['benchmark_task_id']==7]),
        extraction_errors=[dict(run_id=l['run_id'],errors=l['errors']) for l in logs if l['errors']],
        all_prediction_input_receipts_identical=all(l.get('receipts_before')==l.get('receipts_after') for l in logs),
        all_inventory_receipts_identical=all(r.get('receipts_before')==r.get('receipts_after') for r in inventory),
        valid_object_samples=sum(sum(b-a+1 for a,b in p['measurement_frame_intervals']) for p in predictions),
        selected_snapshots=sum(l['frames'] for l in logs),missing_local_fact_artifacts=missing,case_studies=examples,
        prediction_sha256=sha(root/'execution/predictions.json'),seal_sha256=sha(root/'execution/PREDICTION_SEAL.json'),
        independent_generalization_accuracy='not measurable yet',new_positive_reference_count=None,
        development_results_source='evaluation/r1_v3/results.json (separately approved development cases; not new ground truth)')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=HERE);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=summarize(a.root);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['partitions'],indent=2))
