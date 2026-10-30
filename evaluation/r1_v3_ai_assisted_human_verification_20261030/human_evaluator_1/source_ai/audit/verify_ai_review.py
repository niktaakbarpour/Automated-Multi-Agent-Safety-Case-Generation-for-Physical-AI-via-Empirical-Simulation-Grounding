import csv,json,hashlib,re,collections
from pathlib import Path
B=Path('/Users/nikta/trustworthy-ai-evaluator-1');O=B/'ai_evaluator_1_20261029';P=B/'reviewer_1_R1_20'
def read(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def write(p,rr):
 with open(p,'w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
events=read(O/'annotations/events.csv');reqs=read(O/'annotations/requirement_interpretation.csv')
for r in reqs:
 refs=json.loads(r['supporting_frame_references']);refs['negative_measurement_intervals']=[[int(e['review_start_frame']),int(e['review_end_frame'])] for e in events if e['episode']==r['episode'] and e['observation_status']=='no_event_observed_in_window'];r['supporting_frame_references']=json.dumps(refs,separators=(',',':'))
write(O/'annotations/requirement_interpretation.csv',reqs)
a=read(O/'ASSIGNMENTS.csv');cases={x['case_id'] for x in a};initial=read(O/'annotations/initial_support.csv');human=read(O/'HUMAN_REVIEW.csv');coverage=json.loads((O/'COVERAGE.json').read_text());ids={e['event_id'] for e in events}
assert len(ids)==len(events)
for rr in [initial,reqs,human]:assert len(rr)==20 and {r.get('episode',r.get('case_id')) for r in rr}==cases
for r in initial+reqs:assert r['reviewer_copy']=='ai_evaluator_1' and not r['approval_decision']
for r in human:
 for k in ['support_decision','physical_events_decision','R1_decision','uncertainty_and_coverage_decision','human_identity','human_review_date']:assert r[k]==''
for r in reqs:
 assert set(r['physical_event_id'].split(';'))<=ids
 assert r['evidence_coverage']=='partial_execution'
 if r['applicability']=='does_not_apply':assert r['interpretation']=='not_applicable'
for sealname,folder in [('PHYSICAL_STAGE_SEAL.json','physical_stage'),('PHYSICAL_STAGE_V2_SEAL.json','physical_stage_v2')]:
 seal=json.loads((O/sealname).read_text())
 for f,h in seal['files'].items():assert hashlib.sha256((O/'annotations'/folder/f).read_bytes()).hexdigest()==h
for f in ['initial_support.csv','events.csv','uncertainty_requests.csv']:assert (O/'annotations'/f).read_bytes()==(O/'annotations/physical_stage_v2'/f).read_bytes()
for r in a:
 c=r['case_id'];n=int(r['available_last_frame']);assert coverage[c]['measurement_frames']==[[0,n]]
 assert max(coverage[c]['visually_inspected_source_frames_both_views'])==n
 assert all(0<=f<=n for f in coverage[c]['visually_inspected_source_frames_both_views'])
 assert (O/'visual_review'/f'{c}.jpg').exists()
 for f in ['contacts.csv','object_poses.csv','recorded_geometry.json.gz',f'{c}_side_by_side_full_1x.mp4']:assert (O/'evidence'/c/f).is_file()
for link in re.findall(r'\]\(([^)]+)\)',(O/'REPORT.md').read_text()):
 if not link.startswith('#'):assert (O/link).exists(),link
for line in (P/'SHA256SUMS.txt').read_text().splitlines():
 h,f=line.split(None,1);assert hashlib.sha256((P/f.lstrip('*')).read_bytes()).hexdigest()==h
geom=read(O/'audit/geometry_by_frame.csv');assert len(geom)==sum(int(r['available_last_frame'])+1 for r in a)
report={'status':'passed','cases':20,'physical_events':len(events),'uncertainty_requests':len(read(O/'annotations/uncertainty_requests.csv')),'complete_measurement_snapshots':len(geom),'interpretation_counts':dict(collections.Counter(r['interpretation'] for r in reqs)),'checks':['Original package 597 listed hashes unchanged','20 matching case IDs in all case forms','Unique event IDs and valid R1 event references','Blank human decisions and approval fields','AI identity in all proposal forms','Exact bounded visual coverage and full numeric frame coverage','All case evidence and report links exist','Both physical-stage seals valid and original snapshot preserved','Active v2 physical snapshot matches current physical forms','No scoring or reference approval generated']}
(O/'VALIDATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
