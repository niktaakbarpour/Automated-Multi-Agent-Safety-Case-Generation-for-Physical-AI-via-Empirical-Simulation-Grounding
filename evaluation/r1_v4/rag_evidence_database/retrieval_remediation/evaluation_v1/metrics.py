"""Predefined family-level metrics with explicit denominators, never safety accuracy."""
import json,math,collections,statistics
from pathlib import Path
import numpy as np
from .config import *
def wilson(success,n):
 if not n:return None
 p=success/n;z=1.959963984540054;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return [mid-half,mid+half]
def summarize(rows,questions):
 byid={q['id']:q for q in questions};result={}
 def group(rs):
  eligible=[r for r in rs if r['metrics']['eligible']];multi=[r for r in rs if byid[r['case_id']]['multisource_eligible']];critical=[r for r in rs if r['metrics']['critical_abstention']];times=[r['latency_seconds'] for r in rs]
  required=sum(len(byid[r['case_id']]['expected_families']) for r in multi);hits=sum(len(set(byid[r['case_id']]['expected_families'])&set(r['returned_families'])) for r in multi);complete=sum(r['metrics']['complete_required_set'] for r in multi);abstained=sum(r['metrics']['correct_abstention'] for r in critical)
  out=dict(instances=len(rs),eligible=len(eligible),critical=len(critical),multisource=len(multi),multisource_complete_count=complete,multisource_complete=complete/len(multi) if multi else None,multisource_wilson95=wilson(complete,len(multi)),required_family_hits=hits,required_families=required,required_family_recall=hits/required if required else None,correct_abstentions=abstained,critical_abstention_rate=abstained/len(critical) if critical else None,incorrect_abstentions=sum(r['metrics']['incorrect_abstention'] for r in rs),false_assurance=sum(r['metrics']['false_assurance'] for r in rs),errors=dict(collections.Counter(e for r in rs for e in r['metrics']['scope_or_value_errors'])),comparison_operations=sum(r['metrics']['numeric_checks'] for r in rs),metadata_comparisons=sum(r['metrics']['geometry_checks'] for r in rs),returned_sample_instances=sum(len(i.get('samples',[])) for r in rs for i in r['items']),latency_seconds=dict(median=statistics.median(times),p95=float(np.quantile(times,.95)),max=max(times)) if times else None,statuses=dict(collections.Counter(r['status'] for r in rs)))
  for k in ('precision_at_1','recall_at_5','recall_at_20','MRR'):out[k]=statistics.mean(r['metrics'][k] for r in eligible) if eligible else None
  out['p1_wilson95']=wilson(sum(r['metrics']['precision_at_1'] for r in eligible),len(eligible));return out
 for mode in MODES:
  rs=[r for r in rows if r['mode']==mode]
  if not rs:continue
  result[mode]=group(rs);result[mode]['categories']={cat:group([r for r in rs if r['category']==cat]) for cat in sorted({r['category'] for r in rs})};result[mode]['common_channel_only']=group([r for r in rs if byid[r['case_id']]['ranking_eligible'] and set(byid[r['case_id']]['expected_families'])<=set(CHANNELS)])
  eligible=[r for r in rs if r['metrics']['eligible']];scope=collections.defaultdict(list)
  for r in eligible:scope[byid[r['case_id']]['execution_id']].append(r)
  suites=collections.defaultdict(list)
  for e,rr in scope.items():suites[byid[rr[0]['case_id']]['suite']].append(e)
  rng=np.random.default_rng(51005);means=[]
  for b in range(1000):
   sample=[]
   for suite,es in sorted(suites.items()):
    for e in rng.choice(es,size=len(es),replace=True):sample+=scope[e]
   if sample:means.append(statistics.mean(r['metrics']['precision_at_1'] for r in sample))
  result[mode]['p1_stratified_execution_bootstrap95']=list(np.quantile(means,[.025,.975])) if means else None
 return result
def run(label='holdout_v1',dataset='FROZEN_HOLDOUT_DATASET.jsonl'):
 qs=[json.loads(l) for l in (HERE/dataset).read_text().splitlines()];rs=[json.loads(p.read_text()) for p in sorted((WORK/label).glob('*.json'))];out=summarize(rs,qs);(WORK/(label+'_METRICS.json')).write_text(json.dumps(out,sort_keys=True,indent=2));return out
if __name__=='__main__':run()
