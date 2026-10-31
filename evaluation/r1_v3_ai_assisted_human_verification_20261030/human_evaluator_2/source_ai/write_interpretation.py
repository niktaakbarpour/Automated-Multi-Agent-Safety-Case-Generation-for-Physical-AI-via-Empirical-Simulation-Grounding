from pathlib import Path
import csv,json,datetime,hashlib
P=Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20');O=P.parent.parent/'ai_evaluator_2_blind_20261029';A=O/'annotations'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f);return r.fieldnames,list(r)
def write(p,h,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rs)
stage=json.loads((O/'PHYSICAL_STAGE.json').read_text())
for name,h in stage['sha256'].items():assert hashlib.sha256((A/'physical_stage'/name).read_bytes()).hexdigest()==h
hs,s=read(A/'initial_support.csv');he,e=read(A/'events.csv');h,rs=read(A/'requirement_interpretation.csv');_,ass=read(P/'ASSIGNMENTS.csv');end={r['case_id']:int(r['available_last_frame']) for r in ass}
# Case conclusions independently chosen after physical snapshot; this is transcription, not a detector.
applicable={'NV03','NV05','NV06','NV11','NV12','NV13','NV16','NV17'}
carry={'NV05','NV06','NV12','NV16'}
for r in rs:
 c=r['episode'];ev=[x for x in e if x['episode']==c];r.update(reviewer_identity=s[0]['reviewer_identity'],review_date='2026-10-29',physical_event_id=';'.join(x['event_id'] for x in ev),scope_agreement_reference='R1-SCOPE-20261024-01; r1-initial-table-support-v3-20261024 (requester-selected scope, not human approval)',applicability='applies' if c in applicable else 'does_not_apply',interpretation='no_violation_observed_within_reviewed_coverage' if c in applicable else 'not_applicable',review_start_frame=10,review_end_frame=end[c],evidence_coverage='full_execution',supporting_frame_references=f'Full ordered dual-camera saved-frame inspection [0,{end[c]}]; R1 [10,{end[c]}]; boundary0,8-13. Physical row intervals: '+ '; '.join(x['event_id']+'=['+x['review_start_frame']+','+x['review_end_frame']+']' for x in ev),confidence_uncertainty='AI evidence review only, not human ground truth. Full saved-frame coverage via sheets, no timed playback. Small thumbnails/occlusions and unverified exposure/0.002 s geometry lag limit exact timing; sampled evidence cannot establish continuous safety. See COVERAGE.json and uncertainty requests.')
 if c not in applicable:
  r['reasoning']='Absence of initial table/indirect support at10 is established by positive clearance, no contacts and descending setup motion. Under decisionC, R1 does not apply; this is not a pass. Setup separation0-1 remains outside interval10-terminal underG even though table landing follows10. Physical setup descent and landing are retained.'
  if c=='NV20':r['reasoning']+=' Later supported rocking/translation and incidental robot contact do not establish a fall or carrying.'
 elif c in carry:
  r['reasoning']='Direct table support established at10. No unsupported downward departure from that initial support observed before robot lift. Coupled elevated transport with paired finger contacts establishes carrying; later release/drop is physically real but outside R1 underF. No re-placement on table is shown. This is coverage-qualified no violation, not continuous safety.'
  if c in {'NV05','NV12'}:r['reasoning']+=' Recording ends during drop; landing/end remain unknown without changing its observed post-carry origin.'
  if c=='NV12':r['reasoning']+=' Isolated table-contact absence200 during grasp adjustment does not establish unsupported descent; returning contact201 and table-level pose constrain that interpretation.'
 else:r['reasoning']='Direct table support established at10. Full saved interval shows stable table-associated contact/pose and no unsupported downward departure; no R1 violation observed within inspected saved coverage. Setup bounce in butter, where present, ended before10 and is retained separately.'
 r['unresolved_scope_questions']='No case-specific re-placement issue observed. Camera alignment, support-force limits and human protocol playback remain open; no scope expansion or detector validation asserted.'
write(A/'requirement_interpretation.csv',h,rs)
(O/'INTERPRETATION_STAGE.json').write_text(json.dumps({'saved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'physical_snapshot_saved_utc':stage['saved_utc'],'physical_snapshot_hashes_verified':True,'human_approval':False},indent=2))
humanh=['case_id','object_id','ai_review_file','human_reviewer','review_date','decision_accept_reject_correct','corrected_support','corrected_applicability','corrected_interpretation','corrected_events_or_timing','evidence_references','reason','approval']
write(O/'HUMAN_REVIEW.csv',humanh,[dict(case_id=r['episode'],object_id=r['object_id'],ai_review_file='annotations/requirement_interpretation.csv',**{x:'' for x in humanh[3:]}) for r in rs])
print('INTERPRETATION SAVED',len(rs),'HUMAN DECISIONS BLANK')
