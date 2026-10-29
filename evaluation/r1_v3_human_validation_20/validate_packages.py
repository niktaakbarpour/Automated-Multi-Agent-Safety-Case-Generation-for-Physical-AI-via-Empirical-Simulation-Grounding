"""Verify actual archives, case evidence, protocol fidelity and reviewer equivalence."""
import argparse
import csv
import gzip
import hashlib
import json
import math
import tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def digest_stream(f):
    h=hashlib.sha256()
    for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()


def validate(root):
    build=json.loads((root/'BUILD_REPORT.json').read_text());selection=json.loads((HERE/'COORDINATOR_ASSIGNMENTS.json').read_text())['cases'];cm={c['case_id']:c for c in selection}
    if len(cm)!=20 or len({c['run_id'] for c in cm.values()})!=20:raise ValueError('Not twenty distinct sampled recordings')
    freeze=json.loads((HERE/'PROVENANCE_FREEZE.json').read_text());source_ids=[c['run_id'].encode() for c in selection]
    checksums={};reports=[];normalized_forms={}
    answer_fields={'support_label','supporting_entity_if_indirect','evidence_reasoning','visibility','unresolved_questions','confidence_uncertainty','prior_exposure_disclosure','approval_decision','reviewer_identity','review_date','event_id','observation_status','event_description','event_type','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','end_frame','timing_uncertain','reasoning','applicability','interpretation','review_start_frame','review_end_frame','evidence_coverage','physical_event_id','supporting_frame_references','scope_agreement_reference','unresolved_scope_questions'}
    forbidden={'predictions.json','REFERENCE_SEAL.json','APPROVAL.json','COORDINATOR_ASSIGNMENTS.json','PROVENANCE_FREEZE.json'}
    for archive_info in build['archives']:
        who=archive_info['reviewer_id'];directory=root/(who+'_R1_20');archive=Path(archive_info['archive_path'])
        if sha(archive)!=archive_info['archive_sha256'] or archive.stat().st_size!=archive_info['archive_bytes']:raise ValueError('Archive checksum/size mismatch')
        expected={}
        for line in (directory/'SHA256SUMS.txt').read_text().splitlines():
            h,n=line.split(maxsplit=1)
            if Path(n).is_absolute() or '..' in Path(n).parts or sha(directory/n)!=h:raise ValueError('Package checksum mismatch')
            expected[n]=h
        actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
        if set(expected)!=actual or any(p.is_symlink() for p in directory.rglob('*')):raise ValueError('Unexpected/missing/symlinked package content')
        for p in directory.rglob('*'):
            if p.name in forbidden or p.name.startswith('adjudicated_'):raise ValueError('Private label/prediction material in package')
            if p.is_file() and p.suffix in ['.csv','.json','.md','.txt'] and any(run in p.read_bytes() for run in source_ids):raise ValueError('Canonical run identity leaked into reviewer material')
        for n in ['REVIEW_INSTRUCTIONS.md','REQUIREMENT_FOR_REVIEW.md','REQUIREMENT_SCOPE_DECISION.md','requirement_scope.v3.json']:
            if sha(directory/'protocol'/n)!=freeze['protected_files']['human_review_package/'+n]:raise ValueError('Original protocol definitions changed')
        assignment=rows(directory/'ASSIGNMENTS.csv')
        if {r['case_id'] for r in assignment}!=set(cm):raise ValueError('Wrong case assignment')
        normalized_forms[who]={}
        for p in (directory/'annotations').glob('*.csv'):
            rr=rows(p)
            if len(rr)!=(0 if p.name=='uncertainty_requests.csv' else 20):raise ValueError('Wrong number of blank form rows')
            for r in rr:
                if r['run_id'] not in cm or r['episode']!=r['run_id'] or r['object_id']!=cm[r['run_id']]['object_id'] or r['reviewer_copy']!=who:raise ValueError('Wrong neutral unit/reviewer form metadata')
                if any(r.get(k,'') for k in answer_fields):raise ValueError('Human answer/actual coverage field prefilled')
            normalized_forms[who][p.name]=[{k:v for k,v in r.items() if k!='reviewer_copy'} for r in rr]
        for case in cm.values():
            cid=case['case_id'];d=directory/'evidence'/cid;n=case['frame_count']
            videos=list(d.glob('*.mp4'))
            if len(videos)!=9:raise ValueError('Missing full/preview video')
            for view in ['agentview','wrist']:
                for fi in [0,8,9,10,11,12,13]:
                    if not (d/f'{cid}_frame{fi:06d}_{view}.png').is_file():raise ValueError('Missing boundary image')
            frames=rows(d/'frame_references.csv')
            if [int(r['frame']) for r in frames]!=list(range(n)):raise ValueError('Missing frame reference')
            imagehashes=rows(d/'raw_image_hashes.csv')
            if len(imagehashes)!=2*n or {(int(r['frame']),r['camera']) for r in imagehashes}!={(i,c) for i in range(n) for c in ['agentview_image','robot0_eye_in_hand_image']}:raise ValueError('Incomplete camera coverage')
            positions=[r for r in rows(d/'object_poses.csv') if r['object_id']==case['object_id']]
            if [int(r['frame']) for r in positions]!=list(range(n)):raise ValueError('Assigned-object pose evidence missing')
            if any(not math.isfinite(v) for r in positions for v in json.loads(r['xyz_m'])+json.loads(r['quat_wxyz'])):raise ValueError('Nonfinite pose evidence')
            with gzip.open(d/'recorded_geometry.json.gz','rt') as f:geometry=json.load(f)
            if [r['frame'] for r in geometry]!=list(range(n)) or any(set(r)!={'frame','time','geom_xpos','geom_xmat'} for r in geometry):raise ValueError('Incomplete/non-neutral geometry export')
        if len(list((directory/'evidence').glob('*/*.mp4')))!=180:raise ValueError('Wrong video count')
        proof={v['path']:v for v in build['video_verification']}
        for n,h in expected.items():
            if n.endswith('.mp4') and (n not in proof or h!=proof[n]['sha256']):raise ValueError('Video not bound to actual ffprobe verification')
        archived={}
        with tarfile.open(archive,'r:gz') as t:
            for member in t.getmembers():
                p=Path(member.name)
                if p.is_absolute() or '..' in p.parts or member.issym() or member.islnk() or not p.parts or p.parts[0]!=directory.name:raise ValueError('Unsafe/unexpected archive member')
                if member.isfile():archived[str(Path(*p.parts[1:]))]=digest_stream(t.extractfile(member))
        full_expected=dict(expected,**{'SHA256SUMS.txt':sha(directory/'SHA256SUMS.txt')})
        if archived!=full_expected:raise ValueError('Archive contents differ from validated package')
        checksums[who]=expected
        reports.append(dict(reviewer_id=who,archive_path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,case_count=20,distinct_recordings=20,videos=180,full_videos=60,preview_videos=120,verified_files=len(full_expected),all_answers_blank=True,all_selected_evidence_present=True,original_protocol_byte_identical=True,neutral_identifiers_verified=True))
    a,b=checksums['reviewer_1'],checksums['reviewer_2']
    if set(a)!=set(b):raise ValueError('Reviewers receive different file sets')
    varying={'REVIEWER_MANIFEST.json','RETURN_INSTRUCTIONS.md'}|{n for n in a if n.startswith('annotations/') and n.endswith('.csv')}
    if any(a[n]!=b[n] for n in a if n not in varying):raise ValueError('Reviewers receive non-equivalent evidence/protocol')
    if normalized_forms['reviewer_1']!=normalized_forms['reviewer_2']:raise ValueError('Blank form contents differ beyond reviewer ID')
    for who in ['reviewer_1','reviewer_2']:
        public=json.loads((root/(who+'_R1_20')/'REVIEWER_MANIFEST.json').read_text());public.pop('reviewer_id')
        if who=='reviewer_1':first=public
        elif public!=first:raise ValueError('Assignment manifest differs beyond reviewer ID')
    return dict(ready_to_distribute=True,unavailable_or_inadequate_evidence=[],equivalent_information_for_both_reviewers=True,source_archive_sha256=build['source_archive_sha256'],selected_source_files_preserved=all(c['source_stat_preserved'] and c['all_raw_camera_arrays_match_old_export'] for c in build['selected_source_cases']),archives=reports,predictions_and_previous_reference_answers_included=False,actual_reviews_completed=False,accuracy_computed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packages',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    result=validate(a.packages);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
