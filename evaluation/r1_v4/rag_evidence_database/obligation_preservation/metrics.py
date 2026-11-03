"""Separate obligation, fulfillment, ranking and integrity metrics with denominators."""
import json,collections,statistics,math
from .config import *
def wilson(success,n):
 if not n:return None
 z=1.959963984540054;p=success/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return [mid-half,mid+half]
def mean(rows,k):
 vals=[r['metrics'][k] for r in rows if r['metrics'].get(k) is not None];return sum(vals)/len(vals) if vals else None
def summarize(rows):
 result={}
 for mode in ('legacy_k','checked'):
  rr=[r for r in rows if r['mode']==mode];eligible=[r for r in rr if r['metrics']['eligible']];critical=[r for r in rr if r['metrics']['critical']];conj=[r for r in rr if r['metrics']['conjunctive']];errors=collections.Counter(e for r in rr for e in r['metrics']['source_scope_errors']);false=sum(r['metrics']['false_complete'] for r in rr);full=sum(r['metrics']['complete_bundle'] for r in eligible)
  out=dict(cases=len(rr),eligible=len(eligible),critical=len(critical),obligation_recall=mean(rr,'obligation_recall'),obligation_precision=mean(rr,'obligation_precision'),exact_obligation_set=mean(rr,'exact_obligation_set'),measurement_family_recall=mean(rr,'measurement_recall') if mode=='checked' else None,temporal_preservation=mean(rr,'temporal_preserved') if mode=='checked' else None,scope_entity_preservation=mean(rr,'scope_preserved') if mode=='checked' else None,conjunction_cases=len(conj),conjunction_preservation=mean(conj,'conjunction_preserved') if mode=='checked' else None,complete_bundle_count=full,complete_bundle_rate=full/len(eligible) if eligible else None,false_complete=false,false_complete_rate=false/len(rr) if rr else None,false_complete_wilson95=wilson(false,len(rr)),correct_critical_abstentions=sum(r['metrics']['correct_abstention'] for r in critical),incorrect_abstentions=sum(r['metrics']['incorrect_abstention'] for r in rr),status_correct=sum(r['metrics']['status_correct'] for r in rr),false_assurance=sum(r['metrics']['false_assurance'] for r in rr),errors=dict(errors),source_sample_checks=sum(r['metrics']['source_sample_checks'] for r in rr),metadata_checks=sum(r['metrics']['metadata_checks'] for r in rr),family_recall=mean(eligible,'family_recall'),precision_at_1=mean(eligible,'precision_at_1'),recall_at_20=mean(eligible,'recall_at_20'),MRR=mean(eligible,'MRR'),latency_median=statistics.median(r['latency_seconds'] for r in rr) if rr else None)
  result[mode]=out
 return result

def run(label='final_v1',dataset='FROZEN_EVALUATION_DATASET.jsonl'):
 qs={q['id']:q for q in map(json.loads,(HERE/dataset).read_text().splitlines())};rows=[json.loads(p.read_text()) for p in (WORK/label).glob('*.json')];m=summarize(rows);m['categories']={c:summarize([r for r in rows if qs[r['case_id']]['category']==c]) for c in sorted({q['category'] for q in qs.values()})};(WORK/(label+'_METRICS.json')).write_text(json.dumps(m,sort_keys=True,indent=2));return m
if __name__=='__main__':run()
