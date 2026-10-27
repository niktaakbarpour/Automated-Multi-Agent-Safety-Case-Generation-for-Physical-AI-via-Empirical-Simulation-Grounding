"""Collect immutable independent submissions and freeze human-approved adjudication.

This module never reads checker predictions. It never selects or fills final labels.
"""
import argparse
import csv
import datetime
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
TABLES=['initial_support','events','requirement_interpretation','uncertainty_requests']
VERSION='r1-initial-table-support-v3-20261024'
SUPPORT={'direct_table','indirect','unsupported','uncertain'}
APPLICABILITY={'applies','does_not_apply','insufficient_information'}
OUTCOMES={'violation','no_violation_observed_within_reviewed_coverage','not_applicable','insufficient_information'}
STATUS={'observed','no_event_observed_in_window','uncertain'}
REFERENCE_FIELDS=['adjudication_id','run_id','object_id','requirement_version','final_label_json','human_approval_status','adjudicator_identity','approval_date','source_reviewers_json','evidence_references','remaining_uncertainty']


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csvwrite(p,fields,data):
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
def assignments(path):return json.loads(Path(path).read_text())
def cases(path):return {r['case_id']:r for r in assignments(path)['cases']}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()


def validate_submission(data,reviewer,case_map):
    errors=[]
    for table in TABLES:
        if table not in data:errors.append('Missing '+table+'.csv');continue
        seen=[];event_ids=set()
        for r in data[table]:
            alias=r.get('run_id','');case=case_map.get(alias)
            if case is None:errors.append('Unknown neutral case '+alias);continue
            if r.get('object_id')!=case['object_id'] and not (table=='uncertainty_requests' and not r.get('object_id')):errors.append('Wrong assigned object for '+alias)
            if r.get('reviewer_copy')!=reviewer:errors.append('Wrong reviewer_copy for '+alias)
            if not r.get('reviewer_identity','').strip() or not r.get('review_date','').strip():errors.append('Missing reviewer identity/date for '+alias)
            seen.append(alias)
            if table=='initial_support':
                if r.get('support_label') not in SUPPORT:errors.append('Missing/invalid initial support for '+alias)
                if r.get('boundary_frame')!='10':errors.append('Changed boundary frame for '+alias)
            if table=='events':
                if r.get('observation_status') not in STATUS:errors.append('Missing/invalid physical observation status for '+alias)
                eid=r.get('event_id','')
                if not eid or eid in event_ids:errors.append('Missing/duplicate physical event ID for '+alias)
                event_ids.add(eid)
                if r.get('observation_status')=='no_event_observed_in_window' and (not r.get('review_start_frame') or not r.get('review_end_frame')):errors.append('Negative physical window lacks explicit coverage for '+alias)
            if table=='requirement_interpretation':
                if r.get('requirement_version')!=VERSION:errors.append('Wrong R1 version for '+alias)
                if r.get('applicability') not in APPLICABILITY or r.get('interpretation') not in OUTCOMES:errors.append('Missing/invalid R1 interpretation for '+alias)
                if r.get('evidence_coverage') not in ['short_window','full_execution','partial_execution','insufficient_information']:errors.append('Missing/invalid reviewed coverage for '+alias)
                if r.get('evidence_coverage')!='insufficient_information' and (not r.get('review_start_frame') or not r.get('review_end_frame')):errors.append('Missing actual reviewed interval for '+alias)
            for field in ['review_start_frame','review_end_frame','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','end_frame','start_frame']:
                value=r.get(field,'')
                if value:
                    try:
                        number=int(value)
                        if str(number)!=value.strip() or not 0<=number<case['frame_count']:raise ValueError()
                    except ValueError:errors.append('Invalid/out-of-range '+field+' for '+alias)
            for lo,hi in [('review_start_frame','review_end_frame'),('earliest_onset_frame','latest_onset_frame')]:
                try:
                    if r.get(lo) and r.get(hi) and int(r[lo])>int(r[hi]):errors.append('Reversed interval for '+alias)
                except ValueError:pass
        if table in ['initial_support','requirement_interpretation'] and (len(seen)!=len(case_map) or set(seen)!=set(case_map)):errors.append('Need exactly one '+table+' row per assigned case')
        if table=='events' and set(seen)!=set(case_map):errors.append('Need an explicit physical observation/uncertainty row for every assigned case')
    return sorted(set(errors))


def normalized_rows(data,cm):
    normalized={}
    for t,rr in data.items():
        normalized[t]=[]
        for row in rr:
            case=cm.get(row.get('run_id'))
            if not case:continue
            normalized[t].append(dict(row,neutral_case_id=case['case_id'],run_id=case['run_id'],episode=f'episode_{case["episode"]:03d}',source_row_json=json.dumps(row,sort_keys=True)))
    return normalized


def collect(args):
    if args.reviewer not in ['reviewer_1','reviewer_2']:raise ValueError('Unknown reviewer')
    out=args.out/args.reviewer;out.mkdir(parents=True,exist_ok=False)
    original=out/'original_files'
    if args.submission.is_file():
        shutil.copyfile(args.submission,out/'original_submission.zip')
        with zipfile.ZipFile(args.submission) as z:
            for info in z.infolist():
                p=Path(info.filename)
                if p.is_absolute() or '..' in p.parts or '\\' in info.filename or stat.S_ISLNK(info.external_attr>>16):raise ValueError('Unsafe return ZIP member')
            z.extractall(original)
        source_sha=sha(out/'original_submission.zip')
    else:
        for p in args.submission.rglob('*'):
            if p.is_symlink():raise ValueError('Symlinked submission not accepted')
        shutil.copytree(args.submission,original)
        source_sha=None
    folder=original/'annotations' if (original/'annotations').is_dir() else original
    data={t:rows(folder/(t+'.csv')) for t in TABLES if (folder/(t+'.csv')).is_file()}
    cm=cases(args.assignments);errors=validate_submission(data,args.reviewer,cm)
    snapshots={}
    for t in ['initial_support','events','uncertainty_requests']:
        p=folder/'physical_stage'/(t+'.csv')
        if not p.is_file():errors.append('Missing pre-interpretation physical_stage/'+t+'.csv')
        else:snapshots[t]=sha(p)
    if len(snapshots)==3:
        physical_data=dict(data)
        for t in snapshots:physical_data[t]=rows(folder/'physical_stage'/(t+'.csv'))
        errors.extend('Physical-stage snapshot: '+e for e in validate_submission(physical_data,args.reviewer,cm))
    source_files={str(p.relative_to(original)):sha(p) for p in sorted(original.rglob('*')) if p.is_file()}
    if source_sha is None:source_sha=hashlib.sha256(json.dumps(source_files,sort_keys=True).encode()).hexdigest()
    normalized=normalized_rows(data,cm)
    save(out/'normalized_rows.json',normalized)
    receipt=dict(reviewer_id=args.reviewer,received_at_utc=utc(),submission_sha256=source_sha,original_file_hashes=source_files,physical_stage_hashes=snapshots,assignment_sha256=sha(args.assignments),normalized_rows_sha256=sha(out/'normalized_rows.json'),complete=not errors,validation_errors=errors,reviewer_identities=sorted({r.get('reviewer_identity','') for rr in data.values() for r in rr if r.get('reviewer_identity')}))
    save(out/'RECEIPT.json',receipt)
    print(json.dumps(receipt,indent=2))
    if errors:raise ValueError('Submission preserved but incomplete; use a NEW collection root for a corrected return. No original was overwritten.')


def verify_collected(root,assignment):
    receipts={};normalized={}
    for reviewer in ['reviewer_1','reviewer_2']:
        out=root/reviewer;r=json.loads((out/'RECEIPT.json').read_text())
        if not r['complete'] or r['assignment_sha256']!=sha(assignment):raise ValueError('Incomplete/mismatched independent submission')
        for n,h in r['original_file_hashes'].items():
            if sha(out/'original_files'/n)!=h:raise ValueError('Original human submission changed')
        if (out/'original_submission.zip').exists() and sha(out/'original_submission.zip')!=r['submission_sha256']:raise ValueError('Original return ZIP changed')
        original=out/'original_files';folder=original/'annotations' if (original/'annotations').is_dir() else original
        data={t:rows(folder/(t+'.csv')) for t in TABLES};cm=cases(assignment)
        if validate_submission(data,reviewer,cm):raise ValueError('Original submission no longer validates')
        regenerated=normalized_rows(data,cm)
        if sha(out/'normalized_rows.json')!=r['normalized_rows_sha256'] or json.loads((out/'normalized_rows.json').read_text())!=regenerated:raise ValueError('Normalized rows no longer match original human bytes')
        for table,h in r['physical_stage_hashes'].items():
            if sha(folder/'physical_stage'/(table+'.csv'))!=h:raise ValueError('Physical-stage snapshot changed')
        receipts[reviewer]=r;normalized[reviewer]=regenerated
    if set(receipts['reviewer_1']['reviewer_identities'])&set(receipts['reviewer_2']['reviewer_identities']):raise ValueError('Reviewer identities overlap; independent humans must be established')
    return receipts,normalized


def template(args):
    receipts,normalized=verify_collected(args.collected,args.assignments)
    args.out.mkdir(parents=True,exist_ok=False)
    cm=cases(args.assignments)
    for table in TABLES:
        result=[]
        if table!='uncertainty_requests':
            for alias,case in cm.items():
                sources={who:[r for r in tables[table] if r['neutral_case_id']==alias] for who,tables in normalized.items()}
                result.append(dict(adjudication_id=f'{alias}:{table}:01',run_id=case['run_id'],object_id=case['object_id'],requirement_version=VERSION,final_label_json='',human_approval_status='',adjudicator_identity='',approval_date='',source_reviewers_json=json.dumps(sources,sort_keys=True),evidence_references='',remaining_uncertainty=''))
        else:
            for who,tables in normalized.items():
                for i,row in enumerate(tables[table]):
                    result.append(dict(adjudication_id=f'{row["neutral_case_id"]}:uncertainty:{who}:{i}',run_id=row['run_id'],object_id=row['object_id'],requirement_version=VERSION,final_label_json='',human_approval_status='',adjudicator_identity='',approval_date='',source_reviewers_json=json.dumps({who:row},sort_keys=True),evidence_references='',remaining_uncertainty=''))
        csvwrite(args.out/('adjudicated_'+table+'.csv'),REFERENCE_FIELDS,result)
    save(args.out/'TEMPLATE_PROVENANCE.json',dict(assignment_sha256=sha(args.assignments),submission_hashes={k:r['submission_sha256'] for k,r in receipts.items()},final_answers_prefilled=False))
    print('Blank adjudication templates created. A third human must enter and approve all final labels; no checker data was used.')


def reference_rows(directory,assignment):
    cm=cases(assignment);keys={(c['run_id'],c['object_id']):c for c in cm.values()};data={}
    for table in TABLES:
        rr=rows(directory/('adjudicated_'+table+'.csv'));seen=[]
        for row in rr:
            key=(row['run_id'],row['object_id'])
            if table=='uncertainty_requests' and not row['object_id']:
                key=next((k for k in keys if k[0]==row['run_id']),key)
            if key not in keys or row['requirement_version']!=VERSION:raise ValueError('Reference identity/version mismatch')
            if row['human_approval_status']!='approved' or not row['adjudicator_identity'] or not row['approval_date']:raise ValueError('Reference row not explicitly human-approved')
            if not row['source_reviewers_json']:raise ValueError('Missing original human source provenance')
            label=json.loads(row['final_label_json']);row['final']=label;seen.append(key)
            if table=='initial_support':
                if label.get('boundary_frame')!=10 or label.get('support_label') not in SUPPORT:raise ValueError('Invalid final support label')
            elif table=='requirement_interpretation':
                if label.get('applicability') not in APPLICABILITY or label.get('interpretation') not in OUTCOMES:raise ValueError('Invalid final R1 label')
                if (label['applicability']=='does_not_apply')!=(label['interpretation']=='not_applicable'):raise ValueError('Inconsistent final non-applicability')
                if label['applicability']=='insufficient_information' and label['interpretation']!='insufficient_information':raise ValueError('Unknown applicability cannot become determinate outcome')
                if label.get('observation_domain')!='saved_frame_projection':raise ValueError('Explicit saved-frame comparison-domain qualification required')
                windows=label.get('reviewed_intervals',[])
                for pair in windows:
                    if len(pair)!=2 or any(type(x) is not int for x in pair) or not 10<=pair[0]<=pair[1]<keys[key]['frame_count']:raise ValueError('Invalid final reviewed domain')
                if label['interpretation'] in ['violation','no_violation_observed_within_reviewed_coverage'] and not windows:raise ValueError('Determinate reference lacks explicit actual coverage')
            elif table=='events':
                if label.get('observation_status')=='no_event_observed_in_window' and not label.get('reviewed_intervals'):raise ValueError('Final physical negative lacks explicit reviewed fragments')
                for component in label.get('subevents',[label]):
                    mapping=component.get('evaluation_mapping')
                    if mapping:
                        if 'offset_established_exact' in mapping and type(mapping['offset_established_exact']) is not bool:raise ValueError('Exact-offset flag must be boolean, never an inferred time')
                        for field in ['interval','onset_bracket']:
                            pair=mapping.get(field)
                            if pair is not None:
                                if len(pair)!=2 or any(x is not None and (type(x) is not int or not 0<=x<keys[key]['frame_count']) for x in pair):raise ValueError('Invalid approved phase bounds')
                                if all(type(x) is int for x in pair) and pair[0]>pair[1]:raise ValueError('Reversed approved phase bounds')
                if label.get('observation_status') not in STATUS or not label.get('event_type'):raise ValueError('Invalid final physical event')
                for pair in label.get('reviewed_intervals',[]):
                    if len(pair)!=2 or any(type(x) is not int for x in pair) or not 0<=pair[0]<=pair[1]<keys[key]['frame_count']:raise ValueError('Invalid physical reviewed interval')
        if table in ['initial_support','requirement_interpretation'] and (len(seen)!=len(keys) or set(seen)!=set(keys)):raise ValueError('Need exactly one approved support/R1 result per sampled unit')
        if table=='events' and set(seen)!=set(keys):raise ValueError('Missing explicit physical reference for a selected unit')
        if len({r['adjudication_id'] for r in rr})!=len(rr):raise ValueError('Duplicate adjudication IDs')
        data[table]=rr
    support={(r['run_id'],r['object_id']):r['final']['support_label'] for r in data['initial_support']}
    for r in data['requirement_interpretation']:
        expected={'direct_table':'applies','indirect':'applies','unsupported':'does_not_apply','uncertain':'insufficient_information'}[support[(r['run_id'],r['object_id'])]]
        if r['final']['applicability']!=expected:raise ValueError('Final support/applicability inconsistency requires human adjudication')
    return data


def approval_template(args):
    receipts,_=verify_collected(args.collected,args.assignments)
    if args.out.exists():raise FileExistsError(args.out)
    save(args.out,dict(approval_decision='',adjudicator_identity='',approval_date='',independent_submissions_confirmed=False,approval_statement='',assignment_sha256=sha(args.assignments),submission_hashes={k:r['submission_sha256'] for k,r in receipts.items()},adjudication_hashes={f'adjudicated_{t}.csv':sha(args.adjudication/f'adjudicated_{t}.csv') for t in TABLES}))
    print('Approval template created with BLANK decision/identity/date. A human must complete it after final evidence review.')


def freeze(args):
    receipts,_=verify_collected(args.collected,args.assignments)
    approval=json.loads(args.approval.read_text())
    if approval.get('approval_decision')!='approve' or approval.get('independent_submissions_confirmed') is not True or not all(approval.get(k,'').strip() for k in ['adjudicator_identity','approval_date','approval_statement']):raise ValueError('Missing explicit independent human approval')
    if approval.get('assignment_sha256')!=sha(args.assignments) or approval.get('submission_hashes')!={k:r['submission_sha256'] for k,r in receipts.items()}:raise ValueError('Approval does not bind the two original submissions/assignment')
    hashes={f'adjudicated_{t}.csv':sha(args.adjudication/f'adjudicated_{t}.csv') for t in TABLES}
    if approval.get('adjudication_hashes')!=hashes:raise ValueError('Adjudication changed after approval template; obtain renewed human approval')
    data=reference_rows(args.adjudication,args.assignments)
    if any(r['adjudicator_identity']!=approval['adjudicator_identity'] for rr in data.values() for r in rr):raise ValueError('Row/global approval identity mismatch')
    args.out.mkdir(parents=True,exist_ok=False)
    for n in hashes:shutil.copyfile(args.adjudication/n,args.out/n)
    shutil.copyfile(args.approval,args.out/'APPROVAL.json')
    save(args.out/'SOURCE_RECEIPTS.json',receipts)
    save(args.out/'REFERENCE_SEAL.json',dict(approved=True,frozen_at_utc=utc(),assignment_sha256=sha(args.assignments),recordings={c['run_id']:c['recording_sha256'] for c in cases(args.assignments).values()},files={p.name:sha(p) for p in sorted(args.out.iterdir()) if p.is_file()},prediction_inputs_used=False))
    print('Human-approved reference frozen. Original human submissions and adjudication CSV bytes preserved. Scoring may now run separately.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assignments',type=Path,default=HERE/'COORDINATOR_ASSIGNMENTS.json')
    sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('collect');c.add_argument('--reviewer',required=True);c.add_argument('--submission',type=Path,required=True);c.add_argument('--out',type=Path,required=True)
    t=sub.add_parser('adjudication-template');t.add_argument('--collected',type=Path,required=True);t.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('approval-template');a.add_argument('--collected',type=Path,required=True);a.add_argument('--adjudication',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    f=sub.add_parser('freeze');f.add_argument('--collected',type=Path,required=True);f.add_argument('--adjudication',type=Path,required=True);f.add_argument('--approval',type=Path,required=True);f.add_argument('--out',type=Path,required=True)
    args=p.parse_args();{'collect':collect,'adjudication-template':template,'approval-template':approval_template,'freeze':freeze}[args.command](args)
