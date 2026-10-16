import io,json,sys,tempfile,types,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import requirement_proposals as rp
from requirement_inputs_v2 import prepare_v2
R=Path(__file__).resolve().parents[1]

class RequirementV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value,cls.provenance=prepare_v2(R,R/'evidence/geometry_v2/resolved_geometry.json',R/'config/study_objective_v2.json')
        cls.schema=rp.read(R/'schemas/candidate_requirements.v2.schema.json')
    def test_other_tasks_cannot_receive_hardcoded_pilot_facts(self):
        with self.assertRaises(ValueError):prepare_v2(R,R/'evidence/geometry_v2/resolved_geometry.json',R/'config/study_objective_v2.json','different-task')
    def test_measurement_coverage_and_reference_run(self):
        c=self.value['measurement_coverage'];self.assertEqual(c['sample_count'],3)
        self.assertEqual(c['reference_run_id'],self.provenance['reference_run_id'])
        for k in ['units_verified','coordinate_frames_verified','object_reference_points_verified','full_run_availability_verified']:self.assertIs(c[k],False)
        for m in self.value['measurement_inventory']:
            self.assertEqual(m['field_presence'],'present_in_three_sampled_frames')
            self.assertEqual(m['object_reference_point'],'unverified')
    def test_input_categories_and_no_outcomes_or_checker_prerequisite(self):
        text=json.dumps(self.value)
        for f in ['benchmark_outcome','termination_reason','initial_position_world_m','initial_orientation_wxyz','success_rate']:self.assertNotIn(f,text)
        self.assertNotIn('\"sampled_frames\":',text)
        self.assertFalse(self.value['proposal_policy']['approved_requirements_or_checkers_required_to_propose'])
        self.assertEqual(self.value['researcher_provided_study_objectives'][0]['review_status'],'confirmed_study_objective_only')
        ids=[m['id'] for m in self.value['later_checking_information']];self.assertEqual(len(ids),len(set(ids)))
        self.assertNotIn('approved_safety_requirements_and_event_checkers',text)
    def example(self):
        return {'task_id':self.value['task_id'],'candidate_requirements':[{'requirement_id':None,'statement':'Non-target objects should not fall off their supporting table during manipulation.','hazard_or_consequence':'Hypothetical unintended fall; no damage or injury asserted.','applies_when':'Throughout the manipulation execution.','suggested_check':'Support bindings and temporal coverage need validation before a checker can be specified.','entities':['milk_1'],'required_measurements':[{'measurement_id':None,'description':'Validated support relation throughout execution','availability':'missing'}],'checkability':'needs_more_information','assumptions':[],'supporting_input_refs':['objective:non_target_falls','entity:milk_1'],'review_status':'pending'}],'missing_information':['Validated support relation and temporal coverage.']}
    def test_qualitative_incomplete_candidates_and_abstentions(self):
        self.assertEqual(rp.validate(self.example(),self.value,self.schema),[])
        d=self.example();d['candidate_requirements']=[];d['missing_information']=[]
        self.assertEqual(rp.validate(d,self.value,self.schema),[])
    def test_checkability_does_not_overclaim_sampled_presence(self):
        d=self.example();r=d['candidate_requirements'][0];r['required_measurements']=[{'measurement_id':'raw_observation:milk_1_pos','description':'Recorded field only','availability':'present'}];r['checkability']='potentially_checkable'
        self.assertTrue(rp.validate(d,self.value,self.schema))
    def test_duplicate_warnings_rejected_without_rewriting_output(self):
        d=self.example();d['missing_information']=['Support unknown.',' support   unknown ']
        self.assertTrue(rp.validate(d,self.value,self.schema));self.assertEqual(len(d['missing_information']),2)
    def test_configurable_prompt_input_schema_and_metadata(self):
        self.exercise_pilot()
    def test_transport_and_output_validation_are_separate(self):
        self.exercise_pilot(with_errors=True)
    def exercise_pilot(self,with_errors=False):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'custom').mkdir();(p/'runtime').mkdir()
            rp.write(p/'custom/objective.json',rp.read(R/'config/study_objective_v2.json'));rp.write(p/'custom/decision.json',rp.read(R/'config/study_objective_v2.decision.json'));rp.write(p/'custom/task.json',self.value);rp.write(p/'custom/provenance.json',{'audit':'full provenance stays separate'})
            (p/'custom/prompt.txt').write_text('CUSTOM PROMPT VERSION 42');rp.write(p/'custom/schema.json',self.schema)
            for n in ['model_manifest.json','package_versions.txt','backend_settings_audit.json','server_command.json']:(p/'runtime'/n).write_text('{}')
            c=rp.read(R/'config/requirement_generation.v2.json');c.update(task_input_path='custom/task.json',prompt_path='custom/prompt.txt',prompt_version='custom-v42',schema_path='custom/schema.json',runtime_report_dir='runtime',request_timeout_seconds=9876,objective_path='custom/objective.json',objective_decision_path='custom/decision.json')
            rp.write(p/'config.json',c);calls=[]
            def completion(config,messages,seed,tokenizer):
                calls.append((seed,messages));self.assertEqual(config['request_timeout_seconds'],9876)
                if with_errors and seed==1000:raise rp.TransportError('timed out',timeout_seconds=9876,elapsed_seconds=9876)
                value={'smoke':'ok'} if seed==900 else {'task_id':self.value['task_id'],'candidate_requirements':[],'missing_information':['Abstention retained.']}
                content='malformed' if with_errors and seed==1001 and len(messages)==2 else json.dumps(value)
                raw={'choices':[{'finish_reason':'stop','message':{'content':content,'reasoning':'mock separated reasoning'}}],'usage':{'prompt_tokens':10}}
                return raw,{'input_tokens':10,'template_matches':True,'elapsed_seconds':1}
            stub=types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a,**k:object()))
            with patch.dict(sys.modules,transformers=stub),patch('requirement_proposals.complete',side_effect=completion):
                if with_errors:
                    with self.assertRaises(ValueError):rp.pilot(p,p/'config.json',p/'output')
                else:rp.pilot(p,p/'config.json',p/'output')
            m=rp.read(p/'output/metadata.json');self.assertEqual(m['prompt_version'],'custom-v42');self.assertIn('git',m)
            self.assertEqual((p/'output/prompt.txt').read_text(),'CUSTOM PROMPT VERSION 42')
            self.assertEqual(rp.read(p/'output/objective.json')['review_status'],'confirmed_study_objective_only')
            self.assertFalse(rp.read(p/'output/objective_decision.json')['candidate_requirements_approved'])
            self.assertTrue(all('CUSTOM PROMPT VERSION 42' in messages[0]['content'] for seed,messages in calls if seed!=900))
            if with_errors:
                g=p/'output/generation_01';self.assertTrue((g/'attempt_1_transport_error.json').exists());self.assertFalse((g/'attempt_1_validation.json').exists())
                g=p/'output/generation_02';self.assertTrue((g/'attempt_1_validation.json').exists());self.assertFalse((g/'attempt_1_transport_error.json').exists());self.assertTrue((g/'attempt_2_raw.json').exists())
            else:
                summary=rp.read(p/'output/pilot_summary.json');self.assertTrue(all(g['valid'] for g in summary['generations']))
                self.assertTrue(all(not rp.read(p/f'output/generation_{i:02d}/candidates.json')['candidate_requirements'] for i in [1,2,3]))
    def test_http_timeout_forwarding_and_transport_errors(self):
        with patch('urllib.request.urlopen',side_effect=TimeoutError('timeout')) as call:
            with self.assertRaises(rp.TransportError) as caught:rp.request_json('http://localhost',{},timeout_seconds=4321)
            self.assertEqual(call.call_args.kwargs['timeout'],4321);self.assertEqual(caught.exception.details['timeout_seconds'],4321)
        with patch('urllib.request.urlopen',return_value=io.StringIO('not api json')):
            with self.assertRaises(rp.TransportError):rp.request_json('http://localhost',{})
        for v in [0,-1,True,float('inf'),float('nan')]:
            with self.assertRaises(ValueError):rp.request_json('http://localhost',{},timeout_seconds=v)
    def test_git_commit_and_dirty_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);subprocess.run(['git','init','-q',str(p)],check=True)
            (p/'source.py').write_text('pass\n');subprocess.run(['git','-C',str(p),'add','.'],check=True)
            subprocess.run(['git','-C',str(p),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
            clean=rp.git_state(p);self.assertFalse(clean['dirty']);self.assertEqual(len(clean['commit']),40)
            (p/'source.py').write_text('changed\n');self.assertTrue(rp.git_state(p)['dirty'])
    def test_queue_stale_status_and_separate_v2_runtime(self):
        import queue_requirement_pilot as queue
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'status.json';rp.write(p,{'status':'loading_model','queue_pid':99999999,'queue_process_start_ticks':'1'})
            self.assertEqual(queue.inspect_status(p)['status'],'stale_process_not_verified')
            rp.write(p,{'status':'completed_pending_human_review','queue_pid':99999999})
            self.assertEqual(queue.inspect_status(p)['status'],'completed_pending_human_review')
        c=rp.read(R/'config/requirement_generation.v2.json');old=rp.read(R/'data/requirement_pilots/20261016T154747Z/config.json')
        for k in ['model_repo','revision','precision','quantization','generation']:self.assertEqual(c[k],old[k])
