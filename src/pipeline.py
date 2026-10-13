"""Inventory and access recorded evidence. No safety checking or model calls."""
import argparse,json
from pathlib import Path
from facts import load,save
from evidence import transition

def validate(p):
 tasks=load(p/'data/tasks.json')['records'];runs=load(p/'data/runs.json')['records'];cfg=load(p/'config/project.json')
 assert len(tasks)==40 and len(runs)==2000
 tids={t['task_id']:t for t in tasks};rids={r['run_id']:r for r in runs}
 assert len(tids)==40 and len(rids)==2000
 for r in runs:
  assert r['run_id'] in tids[r['task_id']]['run_ids']
  assert r['safety_assessment']['status']=='not_assessed' and r['safety_assessment']['violations'] is None
  assert all(o['body_id'] is not None for o in r['objects'])
  assert (Path(cfg['source_results'])/r['evidence']['trajectory']['source_relative_path']).stat().st_size==r['evidence']['trajectory']['bytes']
 for n in ['requirements','proposed_requirements','cases','claims','events','objections']:
  assert load(p/'data'/(n+'.json'))['records']==[],n+' must be empty'
 registry=load(p/'data/identifier_registry.json')['records']
 assert set(registry['task'])==set(tids) and set(registry['run'])==set(rids)
 assert all(not registry[k] for k in ['requirement','case','claim','event','objection'])
 for suite,expected in cfg['expected_success_percent'].items():
  rs=[r for r in runs if r['suite']==suite];assert len(rs)==500 and 100*sum(r['benchmark_outcome']['success'] for r in rs)/500==expected
 checked=[]
 for suite in cfg['suites']:
  r=next(r for r in runs if r['suite']==suite)
  for step in [0,r['benchmark_outcome']['steps']-1]:
   v=transition(p,r['run_id'],step);assert v['transition']['step']==step and v['event_id'] is None and v['safety_classification'] is None;checked.append({'run_id':r['run_id'],'step_id':step})
  for step in [-1,r['benchmark_outcome']['steps']]:
   try:transition(p,r['run_id'],step)
   except ValueError:pass
   else:raise AssertionError('Invalid step accepted')
 report={'passed':True,'task_count':40,'run_count':2000,'empty_safety_collections':True,'raw_transition_checks':checked,'scope':'All record links, suite outcomes, native body bindings and trajectory byte sizes; first/last raw transitions in each suite; invalid-step rejection'}
 save(p/'reports/validation.json',report);return report

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);sub=ap.add_subparsers(dest='command',required=True);sub.add_parser('collect');sub.add_parser('validate');sub.add_parser('inventory');t=sub.add_parser('transition');t.add_argument('--run-id',required=True);t.add_argument('--step-id',type=int,required=True);a=ap.parse_args()
 if a.command=='collect':
  from collect import collect
  collect(a.project);return
 out=validate(a.project) if a.command=='validate' else transition(a.project,a.run_id,a.step_id) if a.command=='transition' else load(a.project/'reports/collection_report.json')
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
