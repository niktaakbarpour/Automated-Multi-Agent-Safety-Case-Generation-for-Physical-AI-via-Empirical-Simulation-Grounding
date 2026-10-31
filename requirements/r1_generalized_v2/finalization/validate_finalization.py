"""Phase 1.6 document/schema QA only; no V4 assessment or physical inference."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
HERE=Path(__file__).resolve().parent
P=HERE.parent
R=P.parents[1]
BASE='e3694f715dddcf17afa524a05e1b8e784315cd40'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def main():
    assert socket.gethostname().lower()=='hestia'
    out=HERE/'VALIDATION_RESULTS.json'
    assert not out.exists(),'Refuse overwrite; preserve QA history'
    required=['DECISION_REGISTER.md','FINALIZED_R1_V2_CONTRACT.md','RESTRICTED_V4_SCOPE.md','EMPIRICAL_GATES.md','SPECIFICATION_CHANGELOG.md','V4_ENTRY_CHECKLIST.md','VALIDATION_REPORT.md']
    assert all((HERE/n).is_file() for n in required)
    qa=json.loads((HERE/'SPEC_QA_RESULTS.json').read_text())
    assert qa['passed'] and not qa['errors']
    assert qa['configuration_fixture_count']==33 and qa['examples_checked']==4
    assert qa['human_scoring_protected_files_verified']==8
    assert qa['audited_source_files']==16
    assert not qa['V4_implemented'] and not qa['V4_physical_tests_run']
    rows=list(csv.DictReader((P/'decision_review/D01_D11_DECISION_MATRIX.csv').open()))
    decisions=['D%02d'%i for i in range(1,12)]
    assert [row['decision_id'] for row in rows]==decisions
    reg=(HERE/'DECISION_REGISTER.md').read_text()
    assert re.findall(r'^\| (D\d\d) \|',reg,re.M)==decisions
    assert all(d in (P/'decision_review/APPROVAL_CHECKLIST.md').read_text() for d in decisions)
    amendments=['A01','A02','A03','A04','A06','A08','A09','A11']
    proposed=(P/'decision_review/PROPOSED_AMENDMENTS.md').read_text()
    changes=(HERE/'SPECIFICATION_CHANGELOG.md').read_text()
    assert all('## '+a+' ' in proposed and '| '+a+' |' in changes for a in amendments)
    testmd=(P/'V4_TEST_MATRIX.md').read_text()
    ids=re.findall(r'^\| ([A-Z]+\d+[A-Z]*\d*) \|',testmd,re.M)
    assert len(ids)==len(set(ids))
    assert all(t in set(ids) for row in rows for t in row['test_ids'].split())
    assert len([t for t in ids if t.startswith('R16')])==13
    for p in (P/'EXAMPLE_CONFIGS').glob('*.json'):
        v=json.loads(p.read_text());m=v['assessment_manifest']
        assert v['specification_status']=='approved_restricted_design'
        assert v['validation_status']=='illustrative_unvalidated'
        assert m['purpose']=='analytical_fixture' and m['validation_status']=='pending'
        assert m['calibration_records']==[]
        assert all(v['fall_detection_rules']['numeric_policy'][k] is None for k in ['physical_distance_uncertainty_m','persistence_window_s','hysteresis_m','calibration_ref'])
        assert v['temporal_alignment']['state_phase_uncertainty_s'] is None
        assert v['temporal_alignment']['camera_phase_uncertainty_s'] is None
    old=json.loads(git('show',BASE+':requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json'))
    new=json.loads((P/'R1_V2_CONFIG_SCHEMA.json').read_text())
    assert all(new[k]==v for k,v in old.items() if k not in {'$id','title','required','properties','$defs'})
    assert new['required']==old['required']+['assessment_manifest']
    for k,v in old['properties'].items():
        if k!='specification_status':assert new['properties'][k]==v,k
    for k,v in old['$defs'].items():assert new['$defs'][k]==v,k
    changed=git('diff','--name-only',BASE).decode().splitlines()
    assert all(n.startswith('requirements/r1_generalized_v2/') for n in changed)
    assert not any('/decision_review/' in n for n in changed)
    archived=[]
    for n in git('ls-tree','-r','--name-only',BASE,'requirements/r1_generalized_v2/decision_review').decode().splitlines():
        assert (R/n).read_bytes()==git('show',BASE+':'+n),n
        archived.append(n)
    for n in ['QA_RESULTS.json','QA_REPORT.md','AUDIT_SOURCE_BINDINGS.json','CURRENT_R1_AUDIT.md']:
        assert (P/n).read_bytes()==git('show',BASE+':requirements/r1_generalized_v2/'+n)
    status=git('status','--porcelain','--untracked-files=all').decode().splitlines()
    files=sorted({line[3:] for line in status if not line[3:].endswith('.pyc')})
    assert all(n.startswith('requirements/r1_generalized_v2/') for n in files)
    files=sorted(set(files+[str(out.relative_to(R))]))
    subprocess.run(['git','diff','--check'],cwd=R,check=True)
    report=dict(passed=True,host=socket.gethostname(),checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        baseline_commit=BASE,branch=git('branch','--show-current').decode().strip(),
        decisions_recorded=decisions,amendments_integrated=amendments,
        planned_acceptance_cases=len(ids),new_planned_restricted_cases=13,
        archived_review_files_byte_unchanged=len(archived),
        checks=['All seven required finalization documents exist','Four examples and 33 config mutations pass fresh Hestia QA',
        'Draft 2020-12 schema valid; manifest semantic cross-bindings linted',
        'All original schema properties/definitions except approved status preserved; no numeric tolerances introduced',
        'D01-D11 exact matrix/checklist reviewed; dispositions unique; all eight proposed amendments mapped',
        'Acceptance case IDs unique; all historical decision-matrix test references resolve; deferred profile behavior explicit',
        'All tracked changes confined to specification subtree; review/old audit and QA artifacts byte-identical',
        'Frozen V3/predictions, both evaluation seals/members and eight human-scoring safeguards rechecked by SPEC_QA_RESULTS',
        'git diff --check passes'],
        formal_review='Manual: configuration rejection outside assessed algebra; T/F/U and IC distinct; A/Origin/Loss/DownAway/InInterval/handling gate positive admission; dependent contradiction suspends witness; essential shared invalidity blocks; local unrelated gaps do not erase admitted positives; remaining essential contract IC separate from U; negative cells/joins/suffix qualified; aggregate V>IC>U>N>NA and empty/NA excluded. No executed V4 algorithm.',
        commands=['python3 requirements/r1_generalized_v2/validate_spec.py requirements/r1_generalized_v2/finalization/SPEC_QA_RESULTS.json',
        'PYTHONDONTWRITEBYTECODE=1 python3 requirements/r1_generalized_v2/finalization/validate_finalization.py','git diff --check'],
        modified_or_added_files=files,
        package_sha256={str(p.relative_to(P)):sha(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.md','.json','.py'] and p!=out},
        V4_implemented=False,new_simulations=False,RAG_or_multiagent_implemented=False,
        empirical_calibration='BLOCKED_ON_EVIDENCE',independent_empirical_validation='PENDING',
        pushed=False,merged=False)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','planned_acceptance_cases','new_planned_restricted_cases','archived_review_files_byte_unchanged']},indent=2))
if __name__=='__main__':main()
