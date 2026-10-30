from pathlib import Path
import csv,json,shutil,hashlib,datetime
P=Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20');O=P.parent.parent/'ai_evaluator_2_blind_20261029';A=O/'annotations';A.mkdir(exist_ok=True)
ID='AI Evaluator 2 (Codex; independent isolated context; not human)';DATE='2026-10-29'
PRIOR='No Evaluator 1 results, checker predictions, prior labels, coordinator maps, other review directories or repository history accessed. Earlier independent inspection of this same neutral package retained in context after user deleted local files; remaining review and reconstruction performed on Hestia.'
LIMIT='Ordered saved-frame sheets, both cameras; no timed video playback. 20 Hz snapshots, nominal geometry/contact lag 0.002 s, unverified camera exposure; geometric contacts are not force measurements. No continuous-time guarantee.'
rows={};headers={}
for name in ['initial_support','events','requirement_interpretation','uncertainty_requests']:
 with (P/f'annotations/{name}.csv').open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f);headers[name]=rd.fieldnames;rows[name]=list(rd)
 for r in rows[name]:
  if 'evidence_links' in r:r['evidence_links']=r['evidence_links'].replace('../evidence/','../../packages/reviewer_2_R1_20/evidence/')
measure=json.loads((O/'measurement_summary.json').read_text());geom=json.loads((O/'geometry_bounds.json').read_text());assign=list(csv.DictReader((P/'ASSIGNMENTS.csv').open(encoding='utf-8-sig')))
def write(name,rs):
 with (A/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=headers[name]);w.writeheader();w.writerows(rs)
for r in rows['initial_support']:
 c=r['episode'];obj=r['object_id'];z=measure[c]['poses']['10'][2];lo,hi=geom[c]['10'];flat=obj in ['butter_1','cream_cheese_1']
 r.update(reviewer_identity=ID,review_date=DATE,support_label='direct_table' if flat else 'unsupported',prior_exposure_disclosure=PRIOR,confidence_uncertainty='High confidence at saved boundary from converging motion, collision geometry and contacts; between-frame timing uncertain.',unresolved_questions='Camera exposure alignment and instantaneous support forces unverified.',visibility='Both boundary camera sequences inspected. '+('Flat package visible resting on table.' if flat else 'Tall object partly/fully above camera field near apex/boundary; identity followed from setup and re-entry. Invisibility alone is not evidence of no support.'))
 r['evidence_reasoning']=f'Frame10 root z={z:.6f} m; collision z extent [{lo:.6f},{hi:.6f}] m versus tabletop z=0.436760 m. '+('Table contacts and stable pose8-13 corroborate visibly resting directly on table. No supporting intermediary or robot lift at boundary.' if flat else 'No contacts at10; positive collision clearance and descending setup trajectory establish absence of table/indirect support. Departure bracket0-1, apex7, descent8 onward. Later table contact does not alter boundary support.')
write('initial_support',rows['initial_support'])
events=[];index={};bases={r['episode']:r for r in rows['events']}
def add(c,start,end,typ,desc,onset=None,depart='',land='',finish='',status='observed',why='',questions=''):
 n=index.get(c,0)+1;index[c]=n;r=dict(bases[c]);eid=f'{c}:E{n:02d}'
 if n>1:r['record_id']=bases[c]['record_id']+f':E{n:02d}'
 r.update(event_id=eid,reviewer_identity=ID,review_date=DATE,review_start_frame=start,review_end_frame=end,observation_status=status,event_type=typ,event_description=desc,earliest_onset_frame='' if onset is None else onset[0],latest_onset_frame='' if onset is None else onset[1],departure_frame=depart,landing_contact_frame=land,end_frame=finish,onset_outside_window='true' if onset is not None and onset[0]<start else ('false' if onset is not None else ''),end_outside_window='true' if questions.startswith('Landing remains') else 'false',timing_uncertain='true',camera_measurement_references=f'{c}: side-by-side full saved frames {start}-{end}; contacts.csv and object_poses.csv; boundary PNG0,8-13; native_geometry.csv and recorded_geometry.json.gz. See COVERAGE.json for inspected method.',reasoning=why,confidence_uncertainty=LIMIT,visibility='Both streams inspected as ordered sheets; gripper/basket may occlude contact interfaces, wrist field changes. Geometry/contacts corroborate motion.',unresolved_questions=questions,prior_exposure_disclosure=PRIOR)
 events.append(r);return eid
carry={'NV05':(182,183,228,229,229,230,None),'NV06':(72,73,142,143,144,148,148),'NV12':(202,203,252,253,253,254,None),'NV16':(69,70,141,142,143,146,146)}
for a in assign:
 c=a['case_id'];obj=a['object_id'];end=int(a['available_last_frame']);butter=obj=='butter_1';tall=obj not in ['butter_1','cream_cheese_1']
 if tall or butter:
  apex=1 if butter else 7;landing=4 if butter else (16 if obj=='ketchup_1' else 14)
  add(c,0,end,'setup_upward_separation','Object starts at table and rises during settling; first no-contact snapshot1. No causal agent assigned.',(0,1),depart=1,finish=apex,why='Table contact0, none1; root rises and camera shows separation. departure_frame is first recorded separated snapshot, not exact instant.')
  add(c,0,end,'setup_unsupported_descent','After setup apex, object descends without recorded supporting contacts toward table.',(apex,apex+1),depart=1,finish=landing,why=f'Root decreases after{apex}, no contacts until recorded return{landing}. '+('Small bounce ends before boundary10.' if butter else 'Descent continues through10 following setup departure; landing separately recorded.'))
  add(c,0,end,'table_landing_after_setup','Setup descent arrests and table contact reappears; object settles.',(landing-1,landing),land=landing,finish=landing,why=f'First recorded table contact{landing}, then stable samples. Actual impact may precede this within sample/lag uncertainty; departure remains0-1.')
 if c in carry:
  lasttable,lift,lastgrip,release,down,lastdrop,landing=carry[c]
  negend=199 if c=='NV12' else lasttable
  add(c,10,negend,'no_unsupported_table_departure_observed','Object stays at table before separately recorded manipulation; no unsupported downward departure observed.',status='no_event_observed_in_window',why='Ordered dual-camera sequence, stable table-level poses and table contacts support this explicit interval. It does not bridge lift/drop.')
  if c=='NV12':
   add(c,198,202,'grasp_adjustment_at_table','Butter shifts as fingers close; table contact absent200, returns201, overlaps gripper202. No established unsupported descent away from table.',(199,200),finish=202,why='Root z0.44548 at200,0.44545 at201,0.44576 at202. Package remains at table; isolated contact absence does not establish fall or carrying.',questions='Exact load distribution at200 unknown; existing synchronized force records could clarify.')
  add(c,lasttable,min(lift+15,end),'robot_lift_from_table','Fingers secure package; object rises with gripper away from table.',(lasttable,lift),depart=lift,finish=lift+10,why=f'Table contacts end{lasttable}; gripper contacts persist from{lift}, with rising pose and visually coupled motion. No prior unsupported downward phase.')
  add(c,lift,lastgrip,'robot_supported_transport','Raised package travels with gripper above basket, including supported lowering before release.',(lasttable,lift),finish=lastgrip,why='Relative stability in gripper, paired finger/tip contacts, elevation and lateral relocation jointly establish carrying. No duration threshold imposed.')
  add(c,lastgrip,min(end,release+1),'gripper_release','Finger/tip support ceases above basket; first snapshot with no contacts recorded separately from descent.',(lastgrip,release),depart=release,finish=release,why='Tip contacts followed by no contacts and camera separation; exact loss of support lies between saved states.')
  add(c,lastgrip,lastdrop,'post_carry_unsupported_drop','Object descends after established robot transport and release over basket.',(down-1,down),depart=release,finish=landing or '',why=f'No contacts after release{release}, followed by falling root z and visible separation/downward movement. '+(f'Descent arrests near basket{landing}.' if landing else f'Recording ends{end} after descent begins; no landing inferred.'),questions='' if landing else 'Landing remains unrecorded at terminal; no landing/end invented. Later existing frames only if available.')
  if landing:
   add(c,landing-1,min(end,landing+2),'basket_landing','Package lands in basket and remains after gripper withdrawal.',(landing-1,landing),land=landing,finish=landing,why='First recorded basket contact and root settling align with visible motion arrest; basket partly occludes interface.')
   add(c,landing+1,end,'no_further_unsupported_departure_observed','Package stays supported in basket through terminal.',status='no_event_observed_in_window',why='Persistent basket contacts, stable pose and inspected sequence; no additional unsupported departure observed.')
 elif c=='NV20':
  add(c,14,179,'no_unsupported_table_departure_observed','After setup landing milk remains at table before supported adjustment.',status='no_event_observed_in_window',why='Table contacts every sample and inspected sequence; interval excludes later supported motion.')
  add(c,180,204,'supported_tipping_translation_with_incidental_robot_contact','Milk shifts/tilts near gripper then settles; table contact persists, incidental robot contacts195,200,202.',(179,185),finish=204,why='Visible rocking/displacement; root rises to0.51112 at185 then returns near0.5065. Table contacts persist; no unsupported downward departure or carrying. Onset bracket describes visible adjustment, not first microscopic motion.')
  add(c,205,end,'no_unsupported_table_departure_observed','Milk remains upright at table through terminal after adjustment.',status='no_event_observed_in_window',why='Stable table contacts/pose; all ordered camera snapshots inspected.')
 else:
  start=landing if tall else 10
  add(c,start,end,'no_unsupported_table_departure_observed','No further unsupported departure observed in this explicit interval; object remains at table.',status='no_event_observed_in_window',why='All saved dual-camera frames reviewed; contacts remain table-associated and poses stabilize. Saved-coverage negative, not continuous safety.')
write('events',events)
unc=[]
def request(c,start,end,question,evidence):
 r={h:'' for h in headers['uncertainty_requests']};r.update(request_id=f'AI2:U{len(unc)+1:02d}',reviewer_copy='reviewer_2',episode=c,run_id=c,object_id=measure[c]['object_id'] if c else '',start_frame=start,end_frame=end,cannot_determine=question,additional_existing_evidence_requested=evidence,reviewer_identity=ID,review_date=DATE,resolution_status='open');unc.append(r)
request('','','','Timed1x/0.25x playback and human assessment were not performed by this image-based AI interface. Complete saved-frame inspection is a protocol-method deviation.','Human reviewer should watch supplied full individual/side-by-side videos and setup1x/0.25x before accepting, rejecting or correcting AI annotations.')
request('','','','Exact camera exposure relative to cached contacts and load-bearing forces unverified; between-snapshot events cannot be ruled out.','Existing synchronized render/physics timestamps or force records if available; no new experiment requested.')
for c in ['NV05','NV12']:
 end=int(assign[int(c[2:])-1]['available_last_frame']);request(c,end,end,'Post-carry descent reaches recording endpoint before landing is observed.','Later frames from same existing recording only if available; otherwise retain unknown landing/end.')
request('NV12',199,202,'Instantaneous support during isolated table-contact absence200 is not established. No unsupported downward fall away from table demonstrated.','Existing synchronized force or higher-rate state records if available; do not infer fall from contact absence alone.')
write('uncertainty_requests',unc)
write('requirement_interpretation',rows['requirement_interpretation'])
snap=A/'physical_stage';snap.mkdir(exist_ok=False)
for name in ['initial_support','events','uncertainty_requests']:shutil.copyfile(A/f'{name}.csv',snap/f'{name}.csv')
stage={'stage':'physical_saved_before_requirement_interpretation','saved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_identity':ID,'requirement_answers_blank_at_snapshot':True,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snap.glob('*.csv')}}
(O/'PHYSICAL_STAGE.json').write_text(json.dumps(stage,indent=2))
print('PHYSICAL SAVED',len(rows['initial_support']),len(events),len(unc),stage['saved_utc'])
