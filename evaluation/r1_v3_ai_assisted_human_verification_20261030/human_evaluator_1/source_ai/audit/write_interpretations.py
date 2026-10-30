import csv,json,hashlib,datetime,shutil,collections
from pathlib import Path
B=Path('/Users/nikta/trustworthy-ai-evaluator-1');P=B/'reviewer_1_R1_20';O=B/'ai_evaluator_1_20261029'
def read(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def write(p,rr):
 with open(p,'w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
# Preserve the first physical snapshot and seal; make a separately sealed correction before R1 interpretation.
e=read(O/'annotations/events.csv')
for r in e:
 if r['episode']=='NV12' and r['event_type']=='initial_supported_interval':
  r['review_end_frame']='199';r['end_frame']='199';r['reasoning']=r['event_description']='Table-supported stable initial interval 10-199. Frames 200-202 are excluded from this negative observation and retained in NV12:AI1:E03 as an uncertain support transition.'
write(O/'annotations/events.csv',e)
v2=O/'annotations/physical_stage_v2';v2.mkdir()
for f in ['initial_support.csv','events.csv','uncertainty_requests.csv']:shutil.copy2(O/'annotations'/f,v2/f)
seal={'stage':'Corrected physical stage, before requirement interpretation','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Restrict NV12 initial-supported no-event interval to 10-199, excluding uncertain frames 200-202. First snapshot and seal remain unchanged.','supersedes':'PHYSICAL_STAGE_SEAL.json','active_snapshot':'annotations/physical_stage_v2','files':{f:hashlib.sha256((v2/f).read_bytes()).hexdigest() for f in ['initial_support.csv','events.csv','uncertainty_requests.csv']},'human_approval':False}
(O/'PHYSICAL_STAGE_V2_SEAL.json').write_text(json.dumps(seal,indent=2))
initial={r['episode']:r for r in read(O/'annotations/initial_support.csv')};A=read(P/'ASSIGNMENTS.csv');coverage=json.loads((O/'COVERAGE.json').read_text());rr=read(P/'annotations/requirement_interpretation.csv');human=[]
for r in rr:
 c=r['episode'];a=next(a for a in A if a['case_id']==c);n=int(a['available_last_frame']);air=initial[c]['support_label']=='unsupported';ids=[x['event_id'] for x in e if x['episode']==c]
 if air:
  interp='not_applicable';appl='does_not_apply';reason='No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.'
 elif c=='NV12':
  interp='insufficient_information';appl='applies';reason='Direct initial table support is established. Stable table-supported frames 10-199 are followed by an unresolved brief transition at 200-202: one-sided robot contact, a table-contact gap, then table recontact before sustained lift. No fall is established, but exact load-bearing support and very small vertical motion cannot be conclusively interpreted from the current review. Retain insufficient information rather than bridge this gap with a whole-run negative. Subsequent sustained lifting and release 252-254 are separately recorded post-lift events outside R1; terminal landing is unrecorded.'
 elif c in ['NV05','NV06','NV16']:
  interp='no_violation_observed_within_reviewed_coverage';appl='applies';reason='Direct initial table support is established. The initial table-supported period ends in an upward grasp/lift with bilateral gripper support and sustained elevated transport, not an established unsupported downward fall from the table. Subsequent release/descent follows established lifting and is outside R1 under scope F. '+('Butter is still descending at terminal frame 230; no landing is claimed.' if c=='NV05' else 'Basket recontact and settling are retained separately; no later tabletop re-placement or further fall is established.')+' This is qualified to complete saved measurements and explicitly enumerated visual frames; it is not a full human-video review or continuous safety finding.'
 else:
  interp='no_violation_observed_within_reviewed_coverage';appl='applies';reason='Direct initial table support is established. Assigned-object table contacts and stable collision/pose records persist at all saved frames 10 through terminal; inspected both-view frames corroborate placement. No unsupported downward departure is observed in reviewed evidence. This is qualified to saved measurements and enumerated visual frames, not uninspected visual frames or continuous behavior between samples.'
 vis=coverage[c]['visually_inspected_source_frames_both_views']
 intervals=[[10,199]] if c=='NV12' else [[10,n]]
 r.update(reviewer_copy='ai_evaluator_1',physical_event_id=';'.join(ids),reviewer_identity='AI Evaluator 1 (Codex; AI-generated draft)',review_date='2026-10-29',scope_agreement_reference='R1-SCOPE-20261024-01; r1-initial-table-support-v3-20261024; scope reference only, not team agreement',applicability=appl,interpretation=interp,reasoning=reason,unresolved_scope_questions='Review coverage and timing uncertainties remain open. '+('Exact support during frames 200-202 is unresolved.' if c=='NV12' else 'No scope change proposed.'),approval_decision='',review_start_frame=10,review_end_frame=n,evidence_coverage='partial_execution',supporting_frame_references=json.dumps({'measurement_frames':[[10,n]],'visual_source_frames':vis,'negative_measurement_intervals':intervals if not air else [],'uncertain_gap':[[200,202]] if c=='NV12' else []},separators=(',',':')),confidence_uncertainty='AI draft pending human accept/reject. Boundary support confidence high; full visual protocol incomplete. '+('Case outcome unresolved.' if c=='NV12' else 'No calibrated probability assigned.'))
 human.append(dict(case_id=c,object_id=r['object_id'],ai_initial_support=initial[c]['support_label'],ai_applicability=appl,ai_R1_interpretation=interp,ai_reasoning=reason,ai_physical_event_ids=';'.join(ids),case_report=f'REPORT.md#{c.lower()}',support_decision='',physical_events_decision='',R1_decision='',uncertainty_and_coverage_decision='',corrected_initial_support='',corrected_applicability='',corrected_R1_interpretation='',human_evidence_references='',human_reviewed_frame_intervals='',human_video_playback_completed='',human_reasoning='',human_identity='',human_review_date='',review_method='AI-assisted human verification; not independent human-first annotation'))
write(O/'annotations/requirement_interpretation.csv',rr);write(O/'HUMAN_REVIEW.csv',human)
counts=dict(collections.Counter(r['interpretation'] for r in rr));print(counts)
manifest={'review_id':'ai_evaluator_1_20261029','evaluator_type':'AI','identity':'AI Evaluator 1 (Codex)','review_status':'draft_pending_human_review','human_review_method':'AI-assisted accept/reject verification requested by user','independent_human_annotation':False,'human_approval':False,'scoring_performed':False,'source_archive_sha256':'9baf33da88eb4cb5bc40c8d17aecaaa0bbe214fbd2356050d3d797814cfb3389','source_files_hash_verified':597,'source_files_total_including_checksum_list':598,'cases':20,'counts':counts,'active_physical_snapshot':'annotations/physical_stage_v2','original_physical_snapshot_preserved':'annotations/physical_stage','coverage':'Complete saved contacts/poses and collision bounds; sampled visual sequences plus dense transition windows; no timed playback','workflow_compatibility':'Not submitted to original independent-human collection or freeze workflow. HUMAN_REVIEW.csv is a separate verification record, not reference approval. A revised protocol and explicit human approval are required before any downstream scoring under this changed methodology.','excluded_sources':['reviewer_2 package','checker predictions','previous human labels','coordinator mapping','other recordings']}
(O/'REVIEW_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
report=['# AI Evaluator 1: draft for human verification','', 'All 20 assigned cases evaluated using the unchanged R1 definitions. These are AI proposals pending human decisions.','',f"Proposals: **12 not applicable; 7 no R1 violation observed within reviewed coverage; 1 insufficient information (NV12).** These counts are not checker accuracy or approved ground truth.",'','## How to review','', 'Read the case below, inspect its cited source evidence, and enter `accept`, `reject`, or `uncertain` separately for support, physical events, R1, and coverage in HUMAN_REVIEW.csv. On rejection, record the corrected value, reasons, and evidence frames; retain uncertainty where unresolved. Enter your own identity/date and actual reviewed intervals. Blank fields remain pending. Acceptance records human verification of an AI proposal; it does not create an independent human-first review or automatically approve a scoring reference.','', 'Use the original full videos and protocol in this bundle. Frame-10 boundary, setup timing, carrying, and coverage must each be verified. Physical events outside R1 remain in the forms.','', '## Coverage and provenance','', 'I inspected ordered frame sheets containing both cameras for every case: every frame 0–30, every fourth frame from 32, the terminal snapshot, and consecutive detailed windows for NV05, NV06, NV12, NV16, NV20. COVERAGE.json lists exact frames. I did not watch full videos in timed normal-speed playback, separately play individual videos, or perform 0.25x setup playback. All case outcomes therefore carry `partial_execution` visual coverage. Complete assigned-object saved contacts/poses and collision vertical bounds were examined computationally; this is measurement coverage, not full visual review.','', 'Camera exposure phase is unverified; geometry has nominal 0.002 s lag. Contacts do not measure load bearing. A recorded contact timestamp is not an exact physical onset. No conclusion guarantees behavior between 20 Hz snapshots. Source archive checksum and all 597 checksum-list entries were verified (598 files including that list).','', (O/'PRIOR_EXPOSURE.txt').read_text().strip(), '', 'Physical observations were saved before R1 interpretation. The original physical snapshot/seal remain preserved. A separately sealed v2 correction restricts NV12’s no-event interval to 10–199, excluding the uncertain 200–202 transition; `annotations/physical_stage_v2/` is authoritative for this draft.','', '## Case summary','', '| Case | Object | Frame-10 support | Proposed R1 result |','|---|---|---|---|']
for r in rr:report.append(f"| [{r['episode']}](#{r['episode'].lower()}) | {r['object_id']} | {initial[r['episode']]['support_label']} | {r['interpretation']} |")
for r in rr:
 c=r['episode'];a=next(a for a in A if a['case_id']==c)
 report+=['',f'## {c}','',f"Assigned object: **{r['object_id']}**. Recording: frames 0–{a['available_last_frame']}; R1 begins at 10.",'',f"**Initial support proposal:** `{initial[c]['support_label']}`. {initial[c]['evidence_reasoning']}",'','**Physical observations (saved before applying R1):**','']
 for event in [x for x in e if x['episode']==c]:report.append(f"- `{event['event_id']}` ({event['observation_status']}; frames {event['review_start_frame']}–{event['review_end_frame']}): {event['event_description']}")
 report+=['',f"**R1 proposal:** `{r['applicability']}` / `{r['interpretation']}`. {r['reasoning']}",'',f"Evidence: [both-view source video](evidence/{c}/{c}_side_by_side_full_1x.mp4), [agent view](evidence/{c}/{c}_agentview_full_1x.mp4), [wrist view](evidence/{c}/{c}_wrist_full_1x.mp4), [neutral summary](evidence/{c}/EVIDENCE.md), [contacts](evidence/{c}/contacts.csv), [poses](evidence/{c}/object_poses.csv), [visual overview](visual_review/{c}.jpg)."+ (f' [Detailed transition frames](visual_review/{c}_detail.jpg).' if c in ['NV05','NV06','NV12','NV16','NV20'] else ''),'', 'Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.']
(O/'REPORT.md').write_text('\n'.join(report)+'\n')
(O/'START_HERE_AI_REVIEW.md').write_text('''# AI-assisted human review, evaluator 1

Open REPORT.md, then fill HUMAN_REVIEW.csv after checking the supplied evidence.
All decisions are AI-generated drafts; human decision fields are blank.
This bundle includes only the reviewer-1 neutral evidence, protocol, AI observations,
AI R1 interpretations, uncertainty requests and audit records. Predictions and
coordinator mapping are excluded. Keep it private from anyone still performing
an independent review of these cases.

The original study required two independent human-first annotations and third-human
adjudication. The user requested a changed method: AI proposals with human accept/reject
verification. Report that method explicitly. Do not use this AI bundle as a human
reviewer return ZIP or pass it to the original collect/freeze scripts. No original
workflow safeguards have been modified. Accept/reject verification and final reference
approval are separate steps; no approval, scoring, or accuracy estimate was generated.

The AI reviewed complete saved measurements and sampled frame sheets, not complete
normal-speed and quarter-speed video playback. Exact coverage is in COVERAGE.json.
Humans should verify the full source evidence required by the existing protocol and
record actual coverage, corrections, reasons, identity and date. They may reject,
accept, or retain uncertainty for each proposed component.

Files in annotations/ are AI proposals identified as ai_evaluator_1. Human-only
approval fields remain empty. annotations/physical_stage/ preserves the first
physical snapshot; annotations/physical_stage_v2/ is the separately sealed correction
saved before requirement interpretation. See PHYSICAL_STAGE_V2_SEAL.json.

After review, return HUMAN_REVIEW.csv and any correction notes privately to the
coordinator, keeping the original AI draft unchanged. No automatic acceptance or
conversion into approved reference labels is provided.
''')
shutil.copy2(B/'write_physical_review.py',O/'audit/write_physical_review.py');shutil.copy2(__file__,O/'audit/write_interpretations.py')
print('Written report, AI interpretation CSV, human verification form and provenance.')
