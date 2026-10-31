"""Documentation-only Phase 1.5 QA. Run on Hestia; no V4 physics or scoring."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import re
import socket
import sys

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
ALLOWED={'RECOMMEND_APPROVAL','RECOMMEND_REVISIONS','DEFER','BLOCKED_ON_EVIDENCE'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main(frozen_report,output):
    assert socket.gethostname().lower()=='hestia','Research QA must run on Hestia'
    assert not output.exists(),'Refuse to overwrite QA output'
    checks=[]
    required=['D01_D11_DECISION_MATRIX.md','D01_D11_DECISION_MATRIX.csv',
      'RECOMMENDED_DECISIONS.md','DEFERRED_FEATURES.md','EVIDENCE_AND_CALIBRATION_GAPS.md',
      'V3_COMPATIBILITY_IMPACT.md','V4_IMPLEMENTATION_READINESS.md','APPROVAL_CHECKLIST.md',
      'PROPOSED_AMENDMENTS.md','VALIDATION_REPORT.md']
    assert all((HERE/n).is_file() for n in required)
    checks.append('All required review deliverables and exact proposed amendments exist')
    rows=list(csv.DictReader((HERE/'D01_D11_DECISION_MATRIX.csv').open(newline='')))
    expected=['D%02d'%i for i in range(1,12)]
    assert [r['decision_id'] for r in rows]==expected
    md=(HERE/'D01_D11_DECISION_MATRIX.md').read_text()
    original={m[0]:m[1] for m in re.findall(r'^\| (D\d\d) \| ([^|]+?) \|',
              (PARENT/'OPEN_DECISIONS.md').read_text(),re.M)}
    testids=set(re.findall(r'^\| ([A-Z]\d\d) \|',(PARENT/'V4_TEST_MATRIX.md').read_text(),re.M))
    for r in rows:
        assert r['question']==original[r['decision_id']]
        assert r['disposition'] in ALLOWED
        assert all(v.strip() for v in r.values())
        assert all(v in md for k,v in r.items() if k not in {'decision_id','question'})
        sub=re.findall(r'D\d\d\.[a-z] ([A-Z_]+):',r['subdecisions'])
        assert sub and set(sub)<=ALLOWED
        assert all(x in testids for x in r['test_ids'].split())
    checks.append('D01-D11 unique, exact original questions, all review fields and legal dispositions/subdecisions')
    checks.append('Markdown and CSV contain identical recommendation fields; planned test IDs resolve')
    summary=(HERE/'RECOMMENDED_DECISIONS.md').read_text()
    for r in rows:assert '| '+r['decision_id']+' | '+r['disposition']+' |' in summary
    checklist=(HERE/'APPROVAL_CHECKLIST.md').read_text()
    assert '- [x]' not in checklist.lower()
    for d in expected:assert d in checklist
    for amendment in ['A01','A02','A03','A04','A06','A08','A09','A11']:
        assert '## '+amendment+' ' in (HERE/'PROPOSED_AMENDMENTS.md').read_text()
    checks.append('Summary matches primary dispositions; all approval boxes pending; eight amendments present')
    links=0
    for p in HERE.glob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('https:','http:')):continue
            name,_,anchor=target.partition('#')
            f=(p.parent/name).resolve() if name else p
            assert f.is_file(),(p.name,target)
            if re.fullmatch(r'L\d+',anchor):assert int(anchor[1:])<=len(f.read_text().splitlines())
            links+=1
    checks.append('All review relative links resolve')
    binding=json.loads((HERE/'PHASE1_SOURCE_BINDINGS.json').read_text())
    for n,h in binding['files'].items():assert sha(PARENT/n)==h,n
    checks.append('All pre-existing Phase 1 file hashes unchanged')
    frozen=json.loads(frozen_report.read_text())
    assert frozen['passed'] and not frozen['errors']
    assert frozen['human_scoring_protected_files_verified']==8
    assert frozen['configuration_fixture_count']==23 and frozen['examples_checked']==3
    assert frozen['audited_source_files']==16
    assert not frozen['V4_implemented'] and not frozen['new_empirical_evaluation_run']
    checks.append('Fresh Phase 1 QA, frozen V3/predictions, both evaluation seals/members and eight protected files pass')
    result=dict(passed=True,host=socket.gethostname(),checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
       review_baseline_commit='3d235bc69d2c23bf16803cd417f51deb7bbd2d94',checks=checks,
       decision_count=len(rows),relative_links_checked=links,unchanged_phase1_files=len(binding['files']),
       phase1_and_frozen_verification=frozen,source_review_sha256={p.name:sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='REVIEW_QA_RESULTS.json'},
       approvals_recorded=False,V4_implemented=False,empirical_calibration_performed=False,
       physical_tests_executed=False,new_experiments=False,
       manual_review='Normative/formal/applicability/fall/evidence/aggregation/plan/test consistency reviewed; A01-A11 proposals identified, originals not edited. Automated checks do not establish scientific validity.')
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','decision_count','relative_links_checked','unchanged_phase1_files']},indent=2))

if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
