import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import requirement_inputs_v2 as inputs
import requirement_proposals as rp
import pilot_storage as storage
R=Path(__file__).resolve().parents[1]

class ConfirmedInputTest(unittest.TestCase):
    def prepare(self,geometry_change=None,task_change=None):
        original=inputs.read
        def read(path):
            value=original(path)
            if str(path).endswith('resolved_geometry.json') and geometry_change:geometry_change(value)
            if str(path).endswith('data/tasks.json') and task_change:task_change(next(t for t in value['records'] if t['task_id']=='2448c758145ae5ad500f'))
            return value
        with patch('requirement_inputs_v2.read',side_effect=read):return inputs.prepare_v2(R,R/'evidence/geometry_v2/resolved_geometry.json',R/'config/study_objective_v2.json')
    def test_confirmation_is_not_requirement_approval(self):
        value,provenance=self.prepare();objective=value['researcher_provided_study_objectives'][0]
        self.assertEqual(objective['review_status'],'confirmed_study_objective_only')
        self.assertTrue(objective['not_an_approved_requirement'])
        self.assertFalse(objective['intent_inference_required']);self.assertFalse(objective['robot_contact_causation_required'])
        self.assertEqual(len(objective['protected_objects']),5)
        self.assertFalse(provenance['objective_decision']['candidate_requirements_approved'])
        self.assertNotIn('proposed_pending',json.dumps(value))
    def test_rejects_geometry_task_run_or_resolution_mismatch(self):
        for change in [lambda g:g.update(task_id='wrong'),lambda g:g.update(reference_run_id='wrong'),lambda g:g['geometry_resolution'].update(status='unresolved'),lambda g:g.update(source_xml_sha256='wrong')]:
            with self.subTest(change=change),self.assertRaises(ValueError):self.prepare(geometry_change=change)
    def test_rejects_source_object_or_goal_mismatch(self):
        for change in [lambda t:t['facts']['scene_description']['declared_objects'].pop('milk_1'),lambda t:t['facts']['intended_interaction'].update(environment_goal_predicates=[])]:
            with self.subTest(change=change),self.assertRaises(ValueError):self.prepare(task_change=change)
    def test_selected_fields_and_complete_inventory_are_separate(self):
        value,p=self.prepare();self.assertEqual(len(value['measurement_inventory']),5)
        self.assertIn('one recorded position field',value['measurement_selection']['reason'].lower())
        self.assertGreater(len(p['complete_measurement_inventory']['common_raw_observation_keys']),5)
        self.assertFalse(value['measurement_coverage']['full_run_availability_verified'])
        self.assertEqual(value['source_refs']['objective_confirmation']['source_kind'],'researcher_confirmation_of_objective_only')

class StorageTest(unittest.TestCase):
    def config(self,root):
        c={'model_repo':'test/model','revision':'revision','snapshot_path':str(root/'data/model/revision'),'model_cache':str(root/'data/model'),'environment_path':str(root/'data/env'),'runtime_cache':str(root/'data/cache'),'runtime_report_dir':str(root/'home/reports'),'weight_bytes':10,'environment_budget_gib':20,'disk_reserve_gib':1,'runtime_cache_budget_gib':2,'output_budget_gib':1,'vllm_version':'0.31.0','transformers_version':'5.17.0'}
        path=root/'reports/requirement_pilot_queue';path.mkdir(parents=True)
        snap=Path(c['snapshot_path']);snap.mkdir(parents=True);(snap/'part.safetensors').write_bytes(b'abcd')
        (path/'model_manifest.json').write_text(json.dumps({'repo':'test/model','revision':'revision','files':{'part.safetensors':{'bytes':4,'sha256':'unused-for-budget'}}}))
        env=Path(c['environment_path'])/'bin';env.mkdir(parents=True);(env/'python').touch()
        return c
    def test_actual_filesystems_grouped_and_existing_items_credited(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c=self.config(root)
            def probe(p):return {'device':2 if '/data/' in str(p) else 1,'anchor':str(p),'free_bytes':100*storage.GIB}
            plan=storage.storage_plan(c,root,root/'home/output',probe)
            self.assertTrue(plan['sufficient']);self.assertEqual(plan['existing_weight_bytes_credited'],4)
            self.assertTrue(plan['existing_environment_credited']);self.assertEqual(len(plan['filesystems']),2)
            roles={r['role']:r for g in plan['filesystems'] for r in g['roles']}
            self.assertEqual(roles['model_cache']['incremental_budget_bytes'],6)
            self.assertEqual(roles['environment']['incremental_budget_bytes'],0)
            for g in plan['filesystems']:self.assertEqual(g['required_free_bytes'],g['incremental_budget_bytes']+storage.GIB)
    def test_missing_environment_and_low_actual_cache_disk(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c=self.config(root);(Path(c['environment_path'])/'bin/python').unlink()
            def probe(p):return {'device':2 if '/data/' in str(p) else 1,'anchor':str(p),'free_bytes':storage.GIB if '/data/' in str(p) else 1000*storage.GIB}
            plan=storage.storage_plan(c,root,root/'home/output',probe)
            self.assertFalse(plan['sufficient']);self.assertFalse(plan['existing_environment_credited'])
            env=next(r for g in plan['filesystems'] for r in g['roles'] if r['role']=='environment');self.assertEqual(env['incremental_budget_bytes'],20*storage.GIB)
    def test_symlinked_and_future_paths_use_destination_filesystem(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'actual';target.mkdir();(root/'link').symlink_to(target,target_is_directory=True)
            result=storage.filesystem(root/'link/not-created/output')
            self.assertEqual(result['device'],target.stat().st_dev);self.assertEqual(result['anchor'],str(target))
    def test_runtime_mismatch_fails_without_installation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c=self.config(root);(root/'reports/requirement_pilot_queue/package_versions.txt').write_text('vllm==0.31.0\ntransformers==5.17.0\njsonschema==4.26.0\n')
            with patch('pilot_storage.subprocess.check_output',return_value=json.dumps({'vllm':'wrong'})),patch('pilot_storage.subprocess.run') as run:
                with self.assertRaises(RuntimeError):storage.verify_existing_runtime(c,root,root)
                run.assert_not_called()
    def test_no_budget_credit_for_wrong_model_revision(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c=self.config(root);c['revision']='other';self.assertEqual(storage.cached_weights(c,root),0)
