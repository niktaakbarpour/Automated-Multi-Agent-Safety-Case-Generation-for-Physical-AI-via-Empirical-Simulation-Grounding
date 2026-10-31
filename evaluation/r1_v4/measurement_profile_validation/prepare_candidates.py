"""AI-assisted proposals from exact development rows; never reference labels."""
import csv,json,socket
from .analyze import HERE,DATA
from evaluation.r1_v4.libero_evidence_audit.audit_sources import csvwrite,save,sha
CASES=[
 ('C01','initial_support',0,'cream_cheese_1',[9,10,11],'Static geometry and four table contacts at each sample; no other contacts','Load-bearing alternative, phase-qualified t0 and uncertainty remain unvalidated'),
 ('C02','initial_non_applicability',0,'ketchup_1',[9,10,11],'Separated collision shape and zero recorded contacts around t0','Proposed setup-airborne/NA example; no admitted absence or boundary certificate'),
 ('C03','stable_support',14,'cream_cheese_1',[10,260],'Numerically near-static saved geometry at cited endpoints with table contacts','Not continuous support proof; omitted transitions still need profile qualification'),
 ('C04','sliding',None,None,[],'No verified support-preserving sliding example prepared','Lateral/rocking motion and persistent contacts cannot prove sliding; category remains unfilled'),
 ('C05','lifting',14,'cream_cheese_1',[270,274,276,280],'Table+robot contact transitions to bilateral robot contacts and increasing collision heights','Provisional lifting hypothesis; contact alone does not establish holding'),
 ('C06','transport',14,'cream_cheese_1',[276,280,281],'Collision shape moves while both finger groups remain in recorded contact','Possible robot-supported motion; load-bearing/holding and phase require independent review'),
 ('C07','support_loss',14,'cream_cheese_1',[270,274],'Table contact present then absent while robot contacts remain','This is loss of table contact, not a verified unsupported support-loss event'),
 ('C08','downward_departure',14,'cream_cheese_1',[281,282,283,284],'Frames282-283 have zero recorded contacts and downward corresponding vertices after frame281 robot contacts','Candidate post-handling downward motion; no genuine in-scope R1 positive reference'),
 ('C09','post_lift_drop',14,'cream_cheese_1',[274,276,281,282,283,284],'Linked possible lift/contact release/downward movement/recontact sequence','Provisional post-lift proposal; exclusion requires independently established handling'),
 ('C10','ambiguous_contact',2,'cream_cheese_1',[0,1],'Simultaneous table and orange-juice contact at setup','Competing interaction/penetration; cannot infer stable load-bearing from contact'),
 ('C11','setup_origin_departure',2,'cream_cheese_1',[0,7,8,10,12],'Departure/descent precedes frame10; floor contact appears after start','Later landing does not make the setup departure an in-scope R1 fall'),
]
def main():
 assert socket.gethostname().lower()=='hestia'
 rows=list(csv.DictReader((HERE/'DIAGNOSTIC_SAMPLES.csv').open()));out=[]
 for cid,cat,ep,obj,indices,hyp,uncertainty in CASES:
  selected=[next(r for r in rows if int(r['episode'])==ep and r['object_id']==obj and int(r['frame'])==i) for i in indices]
  path=DATA/'long/task_00'/f'episode_{ep:03d}'/'trajectory.h5' if ep is not None else None
  out.append(dict(candidate_id=cid,category=cat,episode=ep,object_id=obj,frames=json.dumps(indices),endpoint_times=json.dumps([float(r['time']) for r in selected]),proposal_status='AI_ASSISTED_PROVISIONAL' if indices else 'NO_VERIFIED_EXAMPLE_PREPARED',proposal=hyp,uncertainty=uncertainty,observed_contacts=json.dumps([{k:r[k] for k in ('frame','table_contacts','robot_contacts','floor_contacts','other_contacts')} for r in selected]),source_path=str(path) if path else '',source_sha256=sha(path) if path else '',hdf5_citations=json.dumps([f'/frames/{i:06d}/simulator/{name}/value' for i in indices for name in ('body_xpos','geom_xpos','geom_xmat','ncon','time')]+[f'/frames/{i:06d}/simulator/contacts@json' for i in indices]),diagnostic_citation='DIAGNOSTIC_SAMPLES.csv: episode/object/frame keys',dependency_group=f'episode_{ep:03d}' if ep is not None else '',camera_review='EXTRACTED_SELECTED_EXCERPTS; VISUAL_REVIEW_NOT_PERFORMED',human_validated=False,independent_review=False,usable_as_ground_truth=False,admitted_R1_violation=False))
 csvwrite(HERE/'DEVELOPMENT_REFERENCE_CANDIDATES.csv',out)
 csvwrite(HERE/'REFERENCE_REVIEW_FORM.csv',[dict(candidate_id=r['candidate_id'],reviewer_id='',evidence_inspected='',physical_observations='',support_status='',event_category='',onset_bracket='',scope_status='',uncertainty='',decision='',rationale='',reviewer_source_hashes='') for r in out if r['source_path']])
 save(HERE/'REFERENCE_PROVENANCE.json',dict(proposal_count=len(out),categories_with_cited_measurements=sum(bool(r['source_path']) for r in out),single_AI_assisted_review=True,reviewer='Current Codex conversation; prior development/audit/V3 context exposure retained',fresh_context=False,human_reviews=0,independent_reference_cases=0,genuine_R1_violations_verified=0,visual_review_performed=False,visual_review_blocker='Automatic approval review rejected image transfer to local agent; permission request pending',source_dependencies=['Original development records','Prior measurement audits and development interpretations','This conversation and deterministic diagnostic tools'],empirical_admission_enabled=False))
 print('Provisional proposals:',len(out),'verified physical references:0')
if __name__=='__main__':main()
