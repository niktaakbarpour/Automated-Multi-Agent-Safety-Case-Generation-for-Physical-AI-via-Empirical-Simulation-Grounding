import json,sys,unittest,tempfile,types
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from requirement_proposals import prepare,validate,assign_ids,final_response,review_file,pilot
R=Path(__file__).resolve().parents[1]
class ProposalsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.input,_=prepare(R);cls.schema=json.loads((R/'schemas/candidate_requirements.schema.json').read_text())
    def example(self):
        e=self.input['entities'][0]['entity_id'];m=self.input['measurement_inventory'][0]['measurement_id'];ref=self.input['entities'][0]['source_ref']
        return {'task_id':self.input['task_id'],'candidate_requirements':[{'requirement_id':None,'statement':'Example pending proposal','hazard_or_consequence':'Hypothetical consequence','entities':[e],'applies_when':'During manipulation','required_measurements':[{'measurement_id':m,'description':'Recorded field','availability':'present'}],'checkability':'potentially_checkable','suggested_check':'Review the relevant recorded fields.','assumptions':[],'supporting_input_refs':[ref],'review_status':'pending'}],'missing_information':[]}
    def test_outcomes_excluded(self):
        text=json.dumps(self.input)
        for forbidden in ['benchmark_outcome','success_rate','sampled_frames','root_groups','video_frame_id','initial_position_world_m','initial_orientation_wxyz']:self.assertNotIn(forbidden,text)
        self.assertFalse(self.input['selection']['selected_using_outcomes'])
    def test_zero_allowed(self):
        d=self.example();d['candidate_requirements']=[];d['missing_information']=['Insufficient justified safety facts'];self.assertEqual(validate(d,self.input,self.schema),[])
    def test_references_and_measurements(self):
        d=self.example();self.assertEqual(validate(d,self.input,self.schema),[])
        d['candidate_requirements'][0]['entities']=['invented_human'];self.assertTrue(validate(d,self.input,self.schema))
        d=self.example();d['candidate_requirements'][0]['required_measurements'][0]['measurement_id']='imaginary_force';self.assertTrue(validate(d,self.input,self.schema))
    def test_pending_and_duplicate_ids(self):
        d=self.example();d['candidate_requirements'][0]['review_status']='approved';self.assertTrue(validate(d,self.input,self.schema))
        d=self.example();r=d['candidate_requirements'][0];r['requirement_id']='same';d['candidate_requirements'].append(dict(r));self.assertTrue(validate(d,self.input,self.schema))
    def test_missing_measurement(self):
        d=self.example();m=d['candidate_requirements'][0]['required_measurements'][0];m.update(measurement_id=None,availability='missing');self.assertTrue(validate(d,self.input,self.schema))
        d['candidate_requirements'][0]['checkability']='needs_more_information';self.assertEqual(validate(d,self.input,self.schema),[])
    def test_ids_and_review(self):
        a=assign_ids(self.example(),'pilot',1);b=assign_ids(self.example(),'pilot',1);c=assign_ids(self.example(),'pilot',2)
        self.assertEqual(a,b);self.assertNotEqual(a,c);self.assertEqual(review_file(a)['reviews'][0]['decision'],'pending')
    def test_truncation_and_reasoning(self):
        for reason,content in [('length','{}'),('stop','<think>x</think>{}')]:
            with self.assertRaises(ValueError):final_response({'choices':[{'finish_reason':reason,'message':{'content':content}}]})
    def test_pilot_three_independent_outputs_and_one_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'data/requirement_inputs').mkdir(parents=True);(p/'prompts').mkdir();(p/'schemas').mkdir();q=p/'reports/requirement_pilot_queue';q.mkdir(parents=True)
            (p/'data/requirement_inputs/development.json').write_text(json.dumps(self.input));(p/'data/requirement_inputs/provenance.json').write_text('{}')
            (p/'prompts/requirements-v1.txt').write_text((R/'prompts/requirements-v1.txt').read_text());(p/'schemas/candidate_requirements.schema.json').write_text(json.dumps(self.schema))
            for name in ['model_manifest.json','package_versions.txt','backend_settings_audit.json','server_command.json']:(q/name).write_text('{}')
            config=json.loads((R/'config/requirement_generation.json').read_text());cp=p/'config.json';cp.write_text(json.dumps(config))
            calls=[]
            def completion(config,messages,seed,tokenizer):
                calls.append((messages,seed));value={'smoke':'ok'} if seed==900 else self.example()
                if seed==1001 and len(messages)==2:value['task_id']='wrong'
                raw={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value),'reasoning':'Mock reasoning'}}],'usage':{'prompt_tokens':10}}
                return raw,{'input_tokens':10,'template_matches':True}
            stub=types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a,**k:object()))
            with patch.dict(sys.modules,transformers=stub),patch('requirement_proposals.complete',side_effect=completion):pilot(p,cp,p/'outputs')
            self.assertEqual(len(calls),5)
            for index in [1,2,4]:self.assertEqual(len(calls[index][0]),2)
            self.assertEqual(len(calls[3][0]),3)
            summary=json.loads((p/'outputs/pilot_summary.json').read_text());self.assertEqual(len(summary['generations']),3)
            self.assertTrue(all(x['valid'] for x in summary['generations']))
            second=p/'outputs/generation_02';self.assertTrue((second/'attempt_1_raw.json').exists());self.assertTrue((second/'attempt_2_raw.json').exists())
            self.assertEqual(json.loads((second/'human_review.json').read_text())['reviews'][0]['decision'],'pending')
if __name__=='__main__':unittest.main()
