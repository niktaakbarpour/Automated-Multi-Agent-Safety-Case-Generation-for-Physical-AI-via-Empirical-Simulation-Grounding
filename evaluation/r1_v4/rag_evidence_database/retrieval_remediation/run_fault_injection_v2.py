"""Reproduce only frozen C8 source-integrity fault cases with planner v2.

This tool creates a private temporary fixture per case, redirects only the exact
frozen trajectory path for that request, and removes only its own temporary
fixture. It never modifies an authoritative source, database, or catalogue.
"""
from __future__ import annotations
import argparse, contextlib, csv, hashlib, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
from importlib import metadata
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.run_eval_v2 import read_rows, evaluate_case, file_sha256, canonical_sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle_v2 import RequestedObligationsRetriever
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.store import BundleStore, SourceVerifier
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.config import DATABASE, DATABASE_SHA

HERE=Path(__file__).resolve().parent
DEFAULT_REFERENCES=HERE/'FROZEN_HOLDOUT_DATASET.jsonl'
DEFAULT_CASES=("KH2-C8-04","KH2-C8-05","KH2-C8-06","KH2-C8-07",
               "KH2-C8-12","KH2-C8-13","KH2-C8-14","KH2-C8-15",
               "KH2-C8-20","KH2-C8-21","KH2-C8-22","KH2-C8-23")

class Redirect:
    def __init__(self, base, canonical, path):
        self.base, self.canonical, self.path=base,str(canonical),str(path)
    @contextlib.contextmanager
    def access(self, path, expected, mode='strict'):
        with self.base.access(self.path if str(path)==self.canonical else path,expected,mode) as pair:
            yield pair
    def verify(self,path,expected,mode='strict'):
        with self.access(path,expected,mode) as (_,attestation): return attestation
    def __getattr__(self,name): return getattr(self.base,name)

def fixture_for(kind, original, expected, directory):
    fixture=directory/'source.h5'
    if kind=='missing_source':
        return fixture, 'designated fixture path intentionally absent'
    shutil.copyfile(original,fixture)
    if kind=='corrupt_source':
        with fixture.open('ab') as stream: stream.write(b'modified-source')
        return fixture, 'copied source with literal bytes appended'
    if kind=='symlink_source':
        target=directory/'other.h5'
        fixture.rename(target); fixture.symlink_to(target)
        return fixture, 'designated fixture path is a symlink to copied source'
    if kind=='replace_source':
        verifier=SourceVerifier(namespace='phase5k-descriptor-bound-v1')
        verifier.verify(str(fixture),expected,'verified_session')
        replacement=directory/'replacement'; replacement.write_bytes(b'replaced source')
        os.replace(replacement,fixture)
        return fixture, 'copied source verified first, then atomically replaced'
    raise ValueError('unsupported frozen fault fixture: '+str(kind))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--database',type=Path,default=DATABASE)
    ap.add_argument('--database-sha256',default=DATABASE_SHA)
    ap.add_argument('--catalogue',type=Path,required=True)
    ap.add_argument('--catalogue-sha256',required=True)
    ap.add_argument('--source-root',type=Path,required=True)
    ap.add_argument('--references',type=Path,default=DEFAULT_REFERENCES)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--temporary-root',type=Path,required=True)
    ap.add_argument('--case-id',action='append',dest='case_ids')
    args=ap.parse_args()
    if args.output.exists():
        raise SystemExit('refusing to overwrite existing output: '+str(args.output))
    if not args.temporary_root.is_dir():
        raise SystemExit('temporary root must be a pre-existing writable directory')
    references=read_rows(args.references); by_id={r['id']:r for r in references}
    selected=args.case_ids or list(DEFAULT_CASES)
    if len(selected)!=len(set(selected)) or any(cid not in by_id for cid in selected):
        raise SystemExit('case IDs must be unique frozen reference IDs')
    rows=[by_id[cid] for cid in selected]
    if any(r.get('fault') not in ('missing_source','corrupt_source','symlink_source','replace_source') for r in rows):
        raise SystemExit('selected row is not a supported frozen fault case')
    root=args.source_root.resolve(strict=True)
    input_hashes={'database_sha256':file_sha256(args.database),
                  'catalogue_sha256':file_sha256(args.catalogue),
                  'references_sha256':file_sha256(args.references)}
    if input_hashes['database_sha256']!=args.database_sha256:
        raise SystemExit('database hash mismatch')
    if input_hashes['catalogue_sha256']!=args.catalogue_sha256:
        raise SystemExit('catalogue hash mismatch')
    for row in rows:
        for artifact in row.get('source_artifacts',[]):
            source=Path(artifact['path'])
            if not source.resolve(strict=True).is_relative_to(root):
                raise SystemExit('frozen source falls outside declared source root')
            if file_sha256(source)!=artifact['sha256']:
                raise SystemExit('frozen source hash mismatch: '+row['id'])
    args.output.mkdir(parents=True)
    records=[]
    for row in rows:
        original=Path(row['source_path']); expected=row['source_sha256']
        if file_sha256(original)!=expected: raise SystemExit('source hash mismatch before fixture')
        with tempfile.TemporaryDirectory(prefix='rq1-fixture-',dir=args.temporary_root) as td:
            fixture_dir=Path(td)
            fixture,procedure=fixture_for(row['fault'],original,expected,fixture_dir)
            retriever=RequestedObligationsRetriever(args.catalogue,args.catalogue_sha256,
                store=BundleStore(args.database,expected_sha256=args.database_sha256))
            old_base=retriever.store.verifier.base
            retriever.store.verifier.base=Redirect(old_base,original,fixture)
            started=time.perf_counter()
            try: record=evaluate_case(row,retriever)
            finally:
                retriever.store.verifier.base=old_base
                retriever.close()
            response=record.get('response') or {}
            reason=str(response.get('reason') or '')
            reason_code='primary_proof_verification_failed' if 'primary_proof_verification_failed' in reason else 'other_integrity_or_contract_rejection'
            family_groups=[{'family':g.get('family'),'status':g.get('status')} for g in response.get('groups',[]) if isinstance(g,dict)]
            item={'case_id':row['id'],'fault_condition':row['fault'],
                  'fixture_procedure':procedure,'planner_version':response.get('planner_version'),
                  'planner_status':record.get('obligation_plan_status'),
                  'requested_families':record.get('requested_families',[]),
                  'retrieval_status':record.get('retrieval_status'),
                  'claimed_complete':bool(record.get('claimed_complete')),
                  'correct_abstention':bool(record.get('abstention') and not record.get('execution_error')),
                  'rejection_code':reason_code,'group_statuses':family_groups,
                  'execution_error':record.get('execution_error') is not None,
                  'authoritative_source_unchanged':file_sha256(original)==expected,
                  'latency_seconds':record.get('latency_seconds')}
            records.append(item)
    summary={}
    for item in records:
        key=item['retrieval_status']; summary[key]=summary.get(key,0)+1
    report={'schema':'rq1-planner-v2-fault-injection-v1','normal_retrieval_rerun':False,
            'database_sha256':input_hashes['database_sha256'],
            'catalogue_sha256':input_hashes['catalogue_sha256'],
            'references_sha256':input_hashes['references_sha256'],
            'fault_runner_sha256':file_sha256(Path(__file__)),
            'retrieval_source_sha256':{name:file_sha256(HERE/name) for name in ('run_eval_v2.py','bundle_v2.py','requested_obligations_v2.py','bundle.py','store.py','planner.py')},
            'python_version':__import__('sys').version,
            'selected_cases':selected,'summary':summary,'case_count':len(records),'cases':records}
    report['report_sha256']=canonical_sha(report)
    (args.output/'FAULT_INJECTION_RESULTS.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    with (args.output/'FAULT_INJECTION_CASES.csv').open('w',newline='') as stream:
        fields=['case_id','fault_condition','planner_version','planner_status','requested_families',
                'retrieval_status','correct_abstention','rejection_code','execution_error',
                'authoritative_source_unchanged','latency_seconds']
        writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
        for item in records:
            row=dict(item);row['requested_families']=';'.join(row['requested_families'])
            writer.writerow({k:row.get(k) for k in fields})
    print(json.dumps({'cases':len(records),'summary':summary,
       'all_correct_abstentions':all(x['correct_abstention'] for x in records),
       'all_sources_unchanged':all(x['authoritative_source_unchanged'] for x in records),
       'no_execution_errors':not any(x['execution_error'] for x in records),
       'report_sha256':report['report_sha256']},sort_keys=True))
if __name__=='__main__':main()

