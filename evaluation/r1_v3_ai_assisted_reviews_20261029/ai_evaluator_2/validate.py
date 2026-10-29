from pathlib import Path
import csv,json,hashlib,datetime,zipfile
P=Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20');O=P.parent.parent/'ai_evaluator_2_blind_20261029';A=O/'annotations'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f);return r.fieldnames,list(r)
checks={};data={}
for name in ['initial_support','events','requirement_interpretation','uncertainty_requests']:
 h,rs=read(A/f'{name}.csv');orig,_=read(P/f'annotations/{name}.csv');checks[name+'_original_header']=h==orig;data[name]=rs
 checks[name+'_well_formed']=all(None not in r and all(v is not None for v in r.values()) for r in rs)
 checks[name+'_ai_identity']=all('AI Evaluator 2' in r['reviewer_identity'] for r in rs)
 for r in rs:
  if 'evidence_links' in r:
   assert all((A/x).is_file() for x in r['evidence_links'].split(';'))
checks['all_evidence_links_resolve']=True
_,ass=read(P/'ASSIGNMENTS.csv');cases={r['case_id'] for r in ass};last={r['case_id']:int(r['available_last_frame']) for r in ass}
for n in ['initial_support','requirement_interpretation']:
 checks[n+'_all20']=len(data[n])==20 and {r['episode'] for r in data[n]}==cases
 checks[n+'_human_approval_blank']=all(r['approval_decision']=='' for r in data[n])
events=data['events'];ids={r['event_id']:r for r in events};checks['unique_event_ids']=len(ids)==len(events);checks['unique_record_ids']=len({r['record_id'] for r in events})==len(events)
checks['physical_references_valid']=all(all(x in ids and ids[x]['episode']==r['episode'] and ids[x]['object_id']==r['object_id'] for x in r['physical_event_id'].split(';')) for r in data['requirement_interpretation'])
checks['event_frame_bounds']=all(all(r[k]=='' or 0<=int(r[k])<=last[r['episode']] for k in ['review_start_frame','review_end_frame','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','end_frame']) and int(r['review_start_frame'])<=int(r['review_end_frame']) for r in events)
checks['support_vocabulary']=all(r['support_label'] in {'direct_table','indirect','unsupported','uncertain'} for r in data['initial_support'])
checks['event_vocabulary']=all(r['observation_status'] in {'observed','no_event_observed_in_window','uncertain'} for r in events)
checks['interpretation_vocabulary']=all(r['applicability'] in {'applies','does_not_apply','insufficient_information'} and r['interpretation'] in {'violation','no_violation_observed_within_reviewed_coverage','not_applicable','insufficient_information'} for r in data['requirement_interpretation'])
stage=json.loads((O/'PHYSICAL_STAGE.json').read_text());inter=json.loads((O/'INTERPRETATION_STAGE.json').read_text())
checks['immutable_physical_snapshot']=all(hashlib.sha256((A/'physical_stage'/n).read_bytes()).hexdigest()==h and (A/n).read_bytes()==(A/'physical_stage'/n).read_bytes() for n,h in stage['sha256'].items())
checks['physical_precedes_interpretation']=stage['saved_utc']<inter['saved_utc'] and stage['requirement_answers_blank_at_snapshot']
cov=json.loads((O/'COVERAGE.json').read_text());checks['coverage_all20']=len(cov['cases'])==20;checks['coverage_saved_frame_counts']=sum(x['unique_original_frames_visually_inspected'] for x in cov['cases'])==5347
checks['remote_derivatives_exist']=all((O/d['path']).is_file() for c in cov['cases'] for d in c['remote_inspected_derivatives'])
checks['no_playback_claims']=all(not c['timed_full_video_playback_performed'] and not c['setup_025x_playback_performed'] for c in cov['cases'])
_,hr=read(O/'HUMAN_REVIEW.csv');checks['human_form_blank']=len(hr)==20 and all(all(v=='' for k,v in r.items() if k not in {'case_id','object_id','ai_review_file'}) for r in hr)
checks['source_manifest_unchanged']=all(hashlib.sha256((P/f).read_bytes()).hexdigest()==h for h,f in (line.split('  ',1) for line in (P/'SHA256SUMS.txt').read_text().splitlines()))
with zipfile.ZipFile(O/'reviewer_2_R1_20_return.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(A.rglob('*.csv')):z.write(p,p.relative_to(O))
with zipfile.ZipFile(O/'reviewer_2_R1_20_return.zip') as z:checks['zip_annotations_only']=len(z.namelist())==7 and all(n.startswith('annotations/') for n in z.namelist()) and z.testzip() is None
result={'validated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'structural_checks_only_not_scientific_validation':True,'all_pass':all(checks.values()),'checks':checks,'rows':{k:len(v) for k,v in data.items()},'human_approval_pending':True,'protocol_timed_playback_pending':True}
(O/'VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['all_pass']
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(O))+'\n' for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt')
(O/'SHA256SUMS.txt').write_text(manifest)
print('OUTPUT_MANIFEST_ENTRIES',len(manifest.splitlines()))
