"""Concise, outcome-free proposal input; complete provenance is stored separately."""
import json
from pathlib import Path
from requirement_proposals import prepare, digest, read


def prepare_v2(project, geometry_path, objective_path, task_id='2448c758145ae5ad500f'):
    if task_id != '2448c758145ae5ad500f':
        raise ValueError('This proposed v2 input builder is specific to the comparison task; prepare and review facts/objectives separately for other tasks.')
    project = Path(project)
    original, provenance = prepare(project, task_id)
    geometry_path = Path(geometry_path); objective_path = Path(objective_path)
    geometry = read(geometry_path); objective = read(objective_path)
    task = next(t for t in read(project/'data/tasks.json')['records'] if t['task_id'] == task_id)
    facts = task['facts']; ref_run = facts['available_measurements']['reference_run_id']
    if geometry.get('task_id')!=task_id:raise ValueError('Geometry report task ID mismatch')
    if geometry.get('reference_run_id')!=ref_run:raise ValueError('Geometry report reference-run ID mismatch')
    if geometry.get('geometry_resolution',{}).get('status')!='compiler_resolved':
        raise ValueError('Geometry resolution did not succeed; refusing to describe geometry as resolved')
    if facts['objects']['reference_run_id']!=ref_run or task['evidence']['reference_run_id']!=ref_run:
        raise ValueError('Source reference-run identities are inconsistent')
    runs=read(project/'data/runs.json')['records']
    reference=next((r for r in runs if r['run_id']==ref_run),None)
    if reference is None or reference['task_id']!=task_id:raise ValueError('Reference run missing or belongs to another task')
    if geometry.get('source_xml_sha256')!=reference['evidence']['simulator_xml']['sha256']:
        raise ValueError('Geometry report XML hash differs from the source reference run')
    if geometry.get('table',{}).get('verification')!='compiler_resolved_model_reference':
        raise ValueError('Table geometry is not compiler resolved')
    entities = original['entities']
    # Validate the pilot-specific names against source declarations and goal predicates.
    targets = ['alphabet_soup_1', 'tomato_sauce_1']
    protected = objective.get('protected_objects',[])
    expected_protected=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']
    if len(protected)!=5 or set(protected)!=set(expected_protected):raise ValueError('Confirmed pilot protected-object list mismatch')
    if objective.get('review_status')!='confirmed_study_objective_only':raise ValueError('Study objective has not been confirmed for this run')
    if objective.get('intent_inference_required') is not False or objective.get('robot_contact_causation_required') is not False:
        raise ValueError('Objective must not require intention inference or robot-contact causation')
    declared=facts['scene_description']['declared_objects']
    if not set(targets+protected+['basket_1']).issubset(declared):raise ValueError('Pilot object declarations differ from source records')
    if facts['scene_description']['declared_fixtures'].get('living_room_table')!='living_room_table':raise ValueError('Supporting-table declaration mismatch')
    goals=facts['intended_interaction']['environment_goal_predicates']
    if goals!=[['in','alphabet_soup_1','basket_1_contain_region'],['in','tomato_sauce_1','basket_1_contain_region']]:
        raise ValueError('Pilot goal/object identities differ from source records')
    if set(declared)-set(facts['intended_interaction']['environment_objects_of_interest'])!=set(protected):
        raise ValueError('Protected objects do not match the declared non-goal objects')
    if any(not any(len(p)==3 and p[0]=='on' and p[1]==n and p[2].startswith('living_room_table_') for p in facts['scene_description']['initial_predicates']) for n in protected):
        raise ValueError('Protected-object initial table-region declarations are missing')
    if len(facts['available_measurements'].get('sampled_frames',[]))!=3:raise ValueError('Expected three-frame reference inventory')
    non_targets=protected
    refs = {k:v for k,v in original['source_refs'].items() if k in
            ['instruction','bddl_language','bddl_file','scene:initial_predicates','intended_interaction']
            or k.startswith('entity:') or k.startswith('surface:')}
    refs['scene:table_geometry'] = {'file': str(geometry_path.relative_to(project)), 'json_pointer':'/table',
                                   'sha256': digest(geometry_path.read_bytes())}
    refs['objective:non_target_falls'] = {'file':str(objective_path.relative_to(project)),
        'json_pointer':'/statement', 'sha256':digest(objective_path.read_bytes()),
        'source_kind':'confirmed_researcher_defined_objective_not_an_approved_requirement'}
    decision_path=project/objective['decision_path'];decision=read(decision_path)
    if decision.get('decision_id')!=objective['decision_id'] or decision.get('protected_objects')!=protected or decision.get('statement')!=objective['statement'] or decision.get('candidate_requirements_approved') is not False:
        raise ValueError('Objective confirmation record is inconsistent')
    refs['objective_confirmation']={'file':str(decision_path.relative_to(project)),'sha256':digest(decision_path.read_bytes()),'source_kind':'researcher_confirmation_of_objective_only'}
    measurements = []
    wanted = {'raw_observation:'+n+'_pos' for n in non_targets}
    for m in original['measurement_inventory']:
        if m['measurement_id'] in wanted:
            measurements.append({'measurement_id':m['measurement_id'], 'source_ref':m['source_ref'],
                'field_presence':'present_in_three_sampled_frames',
                'units':'unverified','coordinate_frame':'unverified','object_reference_point':'unverified',
                'full_run_availability':'unverified'})
            refs[m['source_ref']] = original['source_refs'][m['source_ref']]
    if {m['measurement_id'] for m in measurements}!=wanted:raise ValueError('A protected-object position field is absent from the sampled inventory')
    table = geometry['table']
    if table.get('native_body_name')!='living_room_table' or table.get('collision_enabled_geoms')!=sum(g.get('geometry_role')=='collision_enabled' for g in table['geometries']) or table.get('visual_only_geoms')!=sum(g.get('geometry_role')=='visual_only' for g in table['geometries']):raise ValueError('Geometry table identity or role counts are inconsistent')
    limitations = [
        {'id':'measurement_semantics_and_coverage','detail':'Field presence does not verify units, coordinate frames, object reference points, or availability throughout an execution.'},
        {'id':'support_binding','detail':'Collision geometry is resolved at the model reference configuration; the supporting face, object-to-support bindings, and fall/contact criteria still need validation.'},
        {'id':'temporal_coverage','detail':'Control-step snapshots do not establish continuous substep coverage. An end-of-run state alone cannot establish absence of falls throughout execution.'},
        {'id':'unprovided_properties','detail':'Material, fragility, damage, injury, human presence, restricted regions, force calibration, and numerical safety limits are not established. Do not invent them.'},
        {'id':'causation','detail':'Positions or contacts alone do not establish that robot contact caused displacement.'}]
    result = {'schema_version':'requirements-input-v2','task_id':task_id,
        'instruction_mismatch':original['instruction_mismatch'],
        'verified_scene_facts':{
            'instruction':original['recorded_policy_instruction'],'instruction_source':'instruction',
            'target_objects':targets,'destination':'basket_1','objects_not_named_in_goal':non_targets,
            'initial_relations':'BDDL declares these objects On named regions of living_room_table; this is a task declaration, not measured support or an observed outcome.',
            'initial_relations_source':'scene:initial_predicates',
            'table_geometry':{'owner_body':'living_room_table','descendant_body':'living_room_table_col',
                'collision_enabled_geoms':table['collision_enabled_geoms'],'visual_only_geoms':table['visual_only_geoms'],
                'reference_configuration_only':True,'support_surface_binding':'not_validated','source_ref':'scene:table_geometry'}},
        'researcher_provided_study_objectives':[objective],
        'entities': [{'entity_id':e['entity_id'],'kind':e['kind'],'source_ref':e['source_ref']} for e in entities],
        'measurement_coverage':{'reference_run_id':ref_run,
            'sample_selection':'First, middle, and final frame of one reference run (three frames).',
            'sample_count':3,'field_presence_only':True,'full_run_availability_verified':False,
            'units_verified':False,'coordinate_frames_verified':False,'object_reference_points_verified':False},
        'measurement_inventory':measurements,
        'measurement_selection':{'reason':'One recorded position field per confirmed protected object; these are potentially relevant to later support/fall assessment, not verified fall detectors. Robot intention and contact causation are not required.','protected_objects_source':'objective:non_target_falls','complete_inventory':'Retained separately in provenance.json under complete_measurement_inventory; not a claim that only five fields were recorded.'},
        'later_checking_information':limitations,
        'proposal_policy':{'qualitative_candidates_allowed':True,'incomplete_checking_details_allowed':True,
            'approved_requirements_or_checkers_required_to_propose':False,'human_review_required':True,
            'minimum_candidate_count':0,'execution_outcomes_included':False,
            'project_scope':'This confirmed study objective scopes only this pilot comparison, not future project objectives or requirement approvals.'},
        'source_refs':refs}
    provenance.update({'legacy_input_for_audit_only':original,'complete_task_facts':facts,
        'complete_measurement_inventory':facts['available_measurements'],
        'objective_decision':decision,'objective_decision_sha256':digest(decision_path.read_bytes()),
        'geometry_report':str(geometry_path.relative_to(project)),
        'geometry_report_sha256':digest(geometry_path.read_bytes()),
        'objective_file':str(objective_path.relative_to(project)),
        'objective_file_sha256':digest(objective_path.read_bytes()),
        'prompt_excludes_execution_outcomes':True})
    return result, provenance
