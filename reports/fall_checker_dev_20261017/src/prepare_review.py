import json,sys,collections,csv,hashlib,platform,subprocess,importlib.metadata,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(sys.argv[1]);out=root/'outputs';summary=json.loads((out/'summary.json').read_text());sens=json.loads((out/'sensitivity.json').read_text());forms=root/'human_review';forms.mkdir(exist_ok=False)
rows=[];events=[];initial=collections.Counter();types=collections.Counter();gaps=0
for d in summary['development']:
 for name,a in d['objects'].items():
  initial[a['initial_applicability']]+=1;gaps+=len(a['gaps']);types.update(e['type'] for e in a['events'])
  rows.append({'run_id':d['run_id'],'episode':d['episode'],'object':name,'initial_applicability':a['initial_applicability'],'event_candidates':len(a['events']),'measurement_gaps':len(a['gaps']),'requirement_assessment':a['requirement_verdict'],'human_label':None})
  for e in a['events']:events.append(dict(run_id=d['run_id'],episode=d['episode'],object=name,**e))
with (out/'object_wise.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'physical_event_candidates.json').write_text(json.dumps(events,indent=2))
profiles={p:collections.Counter() for p in ['base','strict','broad']};differences=[]
for s in sens:
 for name,a in s['objects'].items():profiles[s['profile']].update(e['type'] for e in a['events'])
base={s['run_id']:s for s in sens if s['profile']=='base'}
for s in sens:
 if s['profile']=='base':continue
 for name,a in s['objects'].items():
  b=base[s['run_id']]['objects'][name];signature=lambda x:(x['initial_applicability'],[(e['type'],e['phase'],e['descent_frames'],e['ending']) for e in x['events']])
  if signature(a)!=signature(b):differences.append({'run_id':s['run_id'],'object':name,'profile':s['profile'],'base_initial':b['initial_applicability'],'profile_initial':a['initial_applicability'],'base_events':b['events'],'profile_events':a['events']})
(out/'sensitivity_differences.json').write_text(json.dumps(differences,indent=2))
# All forms remain blank. Provisional interpretations are in outputs, not pre-filled labels.
initialforms=[];eventforms=[]
for ep in [0,1,2,14]:
 run=next(d['run_id'] for d in summary['development'] if d['episode']==ep)
 for name in json.loads((root/'config.json').read_text())['objects']:
  initialforms.append({'run_id':run,'object':name,'frame':10,'initial_support_label':None,'supporting_entity':None,'direct_or_indirect':None,'evidence_frame_refs':[],'uncertainty':None,'reviewer_identity':'','decision':None})
 eventforms.append({'run_id':run,'camera_clips':[m['file'] for m in json.loads((root/'clip_manifest.json').read_text()) if m['run_id']==run],'event_type':None,'object':None,'first_possible_frame':None,'last_possible_frame':None,'interval_uncertainty':None,'physical_support_evidence':None,'camera_timing_uncertainty':None,'other_uncertainty':None,'reviewer_identity':'','decision':None})
(forms/'initial_support_forms.json').write_text(json.dumps(initialforms,indent=2));(forms/'event_forms.json').write_text(json.dumps(eventforms,indent=2))
(forms/'INSTRUCTIONS.md').write_text('''# Independent review instructions\n\nForms are blank. Do not treat detector outputs or captions as human labels. Where practical, inspect both-camera consecutive clips before reading provisional interpretations.\n\n1. For each object at frame 10, label direct table support, indirect support (identify intermediate entity), unsupported, or uncertain. Cite exact frames and geometry/contact evidence; appearance or contact count alone is insufficient.\n2. Label physical event type separately: supported tipping/sliding, direct table departure/descent, supported lift/carry, post-lift drop, catch, other landing, setup anomaly, no event observed in this excerpt, or uncertain. Multiple events may need separate copies of a form.\n3. Give first/last possible event frames and timing uncertainty. State whether onset precedes frame 10. Camera exposure time is not independently recorded; derived simulator geometry is nominally t−2 ms and images may have another observation phase.\n4. Record occlusion, missing data, unresolved indirect support and plausible alternatives. Do not label whole-run negatives from these excerpts.\n5. Leave requirement approval and safety interpretation to a separate review. Detector validation requires adjudicated independent labels; no identities or decisions have been entered here. Held-out runs remain reserved.\n''')
lines=['# Provisional development results','',f"Processed {len(summary['development'])} development runs and {sum(d['frames'] for d in summary['development'])} recorded frames; 200 object/run rows. Ten held-out recordings were not processed.",'','Initial support categories: '+str(dict(initial))+'.','','Physical candidate counts (setup and policy segments, not independent falls): '+str(dict(types))+'.',f'\nMeasurement/sequence gaps across object reports: {gaps}. No requirement verdicts, human labels, validated precision/recall, or continuous-safety claims are assigned.','', '## Sensitivity','']
for p,t in profiles.items():lines.append(f'- {p}: {dict(t)}')
lines+=['',f'{len(differences)} object/profile assessments differ from base in initial category, candidate type/interval or contact ending. Full differences are in outputs/sensitivity_differences.json. Sensitivity stability is not validation.','','## Supplied example agreement and unresolved interpretation','','Episode 002: setup airborne/descent evidence is retained; absent initial table support and later floor contact do not create an automatic policy violation. Strict support filtering may not establish origin at deeply penetrating frame zero, so unknown-origin setup descent is deliberately reported.','','Episode 014: inspect candidate output and clips for the bilateral-contact lift followed by unsupported descent and table recontact. Post-lift drop remains distinct from a direct table fall; no requirement violation is assigned.','','Episodes 000/001: initial airborne objects and settling motion are reported rather than passed. Selected clips cover setup and early policy only; full development bundles were processed for detector candidates, without establishing continuous absence of falls.','','No independent human labels exist in this release. Therefore there is no measured detector-versus-human agreement or disagreement rate. Unknown support, contact-force ambiguity, rotation-driven AABB motion, short events and phase uncertainty remain unresolved. Synthetic test successes are separate from recorded candidate outputs.']
(root/'RESULTS.md').write_text('\n'.join(lines)+'\n')
(root/'review_statistics.json').write_text(json.dumps({'initial':initial,'events':types,'profile_counts':profiles,'changed_object_profile_assessments':len(differences),'gaps':gaps},indent=2))
# Actual contact/model settings, without compiling or stepping a simulator.
p=Path(json.loads((root/'config.json').read_text())['source_root'])/'episode_000'/'simulator.xml';tree=ET.parse(p)
(root/'model_contact_settings.json').write_text(json.dumps({'source_xml':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'option':[e.attrib for e in tree.findall('./option')],'default_geom_settings':[e.attrib for e in tree.findall('.//default//geom')],'explicit_geom_contact_settings':[{'name':e.get('name'),'attributes':{k:e.get(k) for k in ['margin','gap','solref','solimp','friction','contype','conaffinity'] if e.get(k) is not None}} for e in tree.findall('.//geom') if any(e.get(k) is not None for k in ['margin','gap','solref','solimp'])],'qualification':'Unspecified defaults are not inferred as calibrated support or fall thresholds.'},indent=2))
print(json.dumps(json.loads((root/'review_statistics.json').read_text()),indent=2))

# Retain all five objects for all fifty run identities without processing held-out recordings.
split=json.loads((root/'proposed_split.json').read_text())
all_rows=[]
for row in rows:
 row=dict(row);row['partition']='development';row['evidence_status']='provisional_support_candidate' if row['initial_applicability']=='direct_table_support_candidate' else 'insufficient_information';row['uncertainty']='Initial support is not human verified; normals/forces and 20 Hz/inter-field timing limitations remain. Unknown applicability is never a pass.';all_rows.append(row)
for run in split['held_out']:
 for name in json.loads((root/'config.json').read_text())['objects']:
  all_rows.append({'run_id':run,'object':name,'partition':'held_out','initial_applicability':'not_processed','evidence_status':'not_evaluated','requirement_assessment':'not_assessed','human_label':None,'uncertainty':'Held-out event outcomes not inspected or used for rules/thresholds.'})
(root/'outputs/all_run_object_index.json').write_text(json.dumps(all_rows,indent=2))
