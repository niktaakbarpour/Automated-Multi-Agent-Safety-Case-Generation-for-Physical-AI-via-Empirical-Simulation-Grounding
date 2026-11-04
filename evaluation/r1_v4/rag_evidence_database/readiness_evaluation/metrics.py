"""Explicit denominators, category separation, and execution-cluster uncertainty."""
import json,collections,statistics,random
from .config import *
IR=('precision_at_1','recall_at_5','recall_at_20','MRR')
def mean(v):return sum(v)/len(v) if v else None
def summary(rows,cases):
 eligible=[r for r in rows if r['assessment']['relevance_eligible']];required=[r for r in rows if cases[r['case_id']]['abstention_required']];positive=[r for r in rows if cases[r['case_id']]['expected_status'] in ('SUFFICIENT','CONDITIONALLY_SUFFICIENT')];a=[r['assessment'] for r in rows]
 return dict(mode_instances=len(rows),unique_questions=len({r['case_id'] for r in rows}),relevance_denominator=len(eligible),**{k:mean([r['assessment'][k] for r in eligible]) for k in IR},coverage_denominator=sum(x['required_evidence_coverage'] is not None for x in a),mean_required_evidence_coverage=mean([x['required_evidence_coverage'] for x in a if x['required_evidence_coverage'] is not None]),complete_cases=sum(x['complete_required_evidence'] for x in a),sufficiency_counts=dict(collections.Counter(x['sufficiency'] for x in a)),required_abstentions=len(required),correct_abstentions=sum(r['assessment']['correct_abstention'] for r in required),correct_abstention_rate=mean([float(r['assessment']['correct_abstention']) for r in required]),positive_reference_denominator=len(positive),incorrect_abstentions=sum(r['assessment']['incorrect_abstention'] for r in positive),unsupported_evidence_returns=sum(bool(r['output']['items']) for r in required),unsupported_claim_acceptances=sum(x['unsupported_claim_acceptance'] for x in a),false_assurance=sum(x['false_assurance'] for x in a),scope_errors=sum(len(x['scope_errors']) for x in a),source_errors=sum(len(x['source_errors']) for x in a),temporal_errors=sum(len(x['temporal_errors']) for x in a),numeric_errors=sum(len(x['numeric_errors']) for x in a),numeric_comparisons=sum(x['numeric_comparisons'] for x in a),uncertainty_label_errors=sum(not x['uncertainty_label_correct'] for x in a),target_statuses=dict(collections.Counter(r['output']['status'] for r in rows)))
def cluster_ci(rows,cases,metric,repeats=2000):
 groups=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in rows:
  v=r['assessment'].get(metric)
  if v is not None:
   q=cases[r['case_id']];groups[q['suite']][q['execution_id']].append(v)
 if not groups:return None
 rng=random.Random(SEED+metric);values=[]
 for i in range(repeats):
  v=[]
  for suite,executions in sorted(groups.items()):
   keys=sorted(executions)
   for j in range(len(keys)):v+=executions[rng.choice(keys)]
  values.append(mean(v))
 values.sort();return dict(lower=values[int(.025*(repeats-1))],upper=values[int(.975*(repeats-1))],repeats=repeats,method='Suite-stratified execution-cluster percentile bootstrap on selected scopes; descriptive, not population confidence or human-language independence',clusters=sum(len(g) for g in groups.values()))
def calculate(rows,cases):
 out={}
 for split in ('development','final'):
  out[split]={}
  for mode in MODES:
   rs=[r for r in rows if r['split']==split and r['mode']==mode];entry=summary(rs,cases);entry['per_category']={cat:summary([r for r in rs if r['category']==cat],cases) for cat in sorted({q['category'] for q in cases.values()})};entry['cluster_intervals']={m:cluster_ci(rs,cases,m) for m in IR} if split=='final' else {};out[split][mode]=entry
 return out
