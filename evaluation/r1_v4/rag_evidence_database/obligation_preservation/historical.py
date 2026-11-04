"""Single exposed K regression comparison after implementation/dataset freeze; no tuning."""
import json,statistics
from dataclasses import asdict
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.audit_values import RawAudit
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.evaluate import fault
from .config import *
from .retrieve import Retriever,BundleRequest

def run():
 frozen=json.loads((HERE/'FROZEN_CONFIGURATION.json').read_text());from evaluation.r1_v4.evidence_registry_gsn.builder import sha
 for n,h in frozen['files'].items():assert sha(HERE/n)==h,n
 k=HERE.parent/'retrieval_remediation';cases=[json.loads(l) for l in (k/'FROZEN_HOLDOUT_DATASET.jsonl').read_text().splitlines()];r=Retriever();audit=RawAudit();rows=[]
 try:
  for q in cases:
   with fault(r.store,dict(q,fault=q.get('fault'))):b=r.retrieve(BundleRequest(q['query'],**q['request']))
   families=[g['family'] for g in b['groups'] if g['status']=='AVAILABLE'];items=[i for g in b['groups'] for i in g['items']];eligible=q['ranking_eligible'];required=set(q['expected_families']);check=audit.check(items,q);rows.append(dict(case_id=q['id'],query=q['query'],status=b['completeness_status'],eligible=eligible,precision_at_1=float(bool(families) and families[0] in required) if eligible else None,recall_at_20=len(required&set(families[:20]))/len(required) if eligible else None,critical=q['critical_abstention'],correct_abstention=q['critical_abstention'] and not items,source_errors=check['errors'],families=families,query_obligations=b['query_obligations']))
 finally:r.close();audit.close()
 eligible=[x for x in rows if x['eligible']];result=dict(exposed_historical_not_generalization=True,questions=len(rows),eligible=len(eligible),precision_at_1=statistics.mean(x['precision_at_1'] for x in eligible),recall_at_20=statistics.mean(x['recall_at_20'] for x in eligible),critical=sum(x['critical'] for x in rows),correct_abstentions=sum(x['correct_abstention'] for x in rows),source_errors=[x['case_id'] for x in rows if x['source_errors']],rows=rows);(WORK/'HISTORICAL_K_REGRESSION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print({k:v for k,v in result.items() if k!='rows'},flush=True)
if __name__=='__main__':run()
