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
    assert ref_run == geometry['reference_run_id'], 'Geometry and field inventory must use the same reference run'
    entities = original['entities']
    # Preserve instruction/task declarations, never observed poses, results, or failure labels.
    targets = ['alphabet_soup_1', 'tomato_sauce_1']
    non_targets = ['cream_cheese_1', 'ketchup_1', 'orange_juice_1', 'milk_1', 'butter_1']
    refs = {k:v for k,v in original['source_refs'].items() if k in
            ['instruction','bddl_language','bddl_file','scene:initial_predicates','intended_interaction']
            or k.startswith('entity:') or k.startswith('surface:')}
    refs['scene:table_geometry'] = {'file': str(geometry_path.relative_to(project)), 'json_pointer':'/table',
                                   'sha256': digest(geometry_path.read_bytes())}
    refs['objective:non_target_falls'] = {'file':str(objective_path.relative_to(project)),
        'json_pointer':'/statement', 'sha256':digest(objective_path.read_bytes()),
        'source_kind':'proposed_researcher_defined_objective_not_approved'}
    measurements = []
    wanted = {'raw_observation:'+n+'_pos' for n in non_targets}
    for m in original['measurement_inventory']:
        if m['measurement_id'] in wanted:
            measurements.append({'measurement_id':m['measurement_id'], 'source_ref':m['source_ref'],
                'field_presence':'present_in_three_sampled_frames',
                'units':'unverified','coordinate_frame':'unverified','object_reference_point':'unverified',
                'full_run_availability':'unverified'})
            refs[m['source_ref']] = original['source_refs'][m['source_ref']]
    table = geometry['table']
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
        'measurement_inventory':measurements,'later_checking_information':limitations,
        'proposal_policy':{'qualitative_candidates_allowed':True,'incomplete_checking_details_allowed':True,
            'approved_requirements_or_checkers_required_to_propose':False,'human_review_required':True,
            'minimum_candidate_count':0,'execution_outcomes_included':False,
            'project_scope':'This proposed objective scopes only this pilot comparison, not future project objectives.'},
        'source_refs':refs}
    provenance.update({'legacy_input_for_audit_only':original,'complete_task_facts':facts,
        'geometry_report':str(geometry_path.relative_to(project)),
        'geometry_report_sha256':digest(geometry_path.read_bytes()),
        'objective_file':str(objective_path.relative_to(project)),
        'objective_file_sha256':digest(objective_path.read_bytes()),
        'prompt_excludes_execution_outcomes':True})
    return result, provenance
