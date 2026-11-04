"""Phase 5G channel contracts. No physical interpretation of generic arrays."""
from pathlib import Path
import json,sqlite3,hashlib,socket
import numpy as np
from evaluation.r1_v4.provenance import canonical,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.registry import VariantStore

HERE=Path(__file__).resolve().parent
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working')
BASE=Path('/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite')
BASE_SHA='a0f9347db719902f275d0f3e89f0682f093d5ded858ab7c2823067930337baa9'
VERSION='phase5g-channel-1.0.0'
CHANNELS={
 'raw.robot0_gripper_qpos':dict(field='raw_observation/robot0_gripper_qpos/value',shape=[2],object_id='robot0',description='Recorded raw gripper position vector; physical units and component binding unverified.'),
 'raw.robot0_gripper_qvel':dict(field='raw_observation/robot0_gripper_qvel/value',shape=[2],object_id='robot0',description='Recorded raw gripper velocity vector; physical units and component binding unverified.'),
 'raw.robot0_joint_pos':dict(field='raw_observation/robot0_joint_pos/value',shape=[7],object_id='robot0',description='Recorded raw robot joint position vector; physical units and joint order unverified.'),
 'raw.robot0_joint_vel':dict(field='raw_observation/robot0_joint_vel/value',shape=[7],object_id='robot0',description='Recorded raw robot joint velocity vector; physical units and joint order unverified.'),
 'raw.simulator_actuator_force':dict(field='simulator/actuator_force/value',shape=[9],object_id='*',description='Recorded raw simulator actuator force array; actuator order and force units unverified.'),
 'simulator.ncon':dict(field='simulator/ncon/value',shape=[],object_id='*',description='Recorded simulator contact entry count; no contact force, support or collision-event judgment.'),
}

def contract(channel):
 d=CHANNELS[channel];count=channel=='simulator.ncon'
 return dict(version=VERSION,channel_id=channel,**d,origin='direct_recording',transformation='identity',units='count' if count else None,coordinate_frame='not_applicable_count' if count else 'uninterpreted_raw_array',validation_status='validated_recorded_count' if count else 'validated_raw_values_only',phase='native_last_forward_cache_phase_uncalibrated' if channel.startswith('simulator.') or 'simulator_' in channel else 'raw_observable_cache_phase_unknown',clock='saved_frame_index',frequency='Per saved snapshot; no uniform physical sampling guarantee',alignment='Exact saved frame key only; no interpolation, unit conversion, normalization or endpoint/cache co-location assumption',geometry_mapping='No spatial interpretation permitted; XML and native map retained for provenance only',missing_policy='Missing dataset, shape/type mismatch, nonfinite values or negative/noninteger count: unsupported sample; never fill',retrieval='Execution required; optional task, variant, channel, object, inclusive saved-frame interval, origin, units and frame. Values are decoded from original source on explicit interval request.',physical_claims=False)

def sample(dataset,channel):
 """Decode only the declared dataset; malformed samples are explicit abstentions."""
 if dataset is None:return None,'missing_dataset'
 a=np.asarray(dataset[()]);d=CHANNELS[channel]
 if list(a.shape)!=d['shape']:return None,'unsupported_shape'
 if a.dtype.kind not in 'fiu' or not np.isfinite(a).all():return None,'invalid_numeric_value'
 if channel=='simulator.ncon' and (a.dtype.kind not in 'iu' or int(a)<0):return None,'invalid_count'
 return a,None

def owned(path):
 p=Path(path)
 if str(p).startswith('/local/home/niktakbr/'):
  # Verified local bind mount of /disk/0; never broaden to NFS homes.
  alias=Path('/disk/0/home/niktakbr')/p.relative_to('/local/home/niktakbr')
  if (p.stat().st_dev,p.stat().st_ino)!=(alias.stat().st_dev,alias.stat().st_ino):raise ValueError('disk0 alias mismatch')
  p=alias
 if not str(p).startswith(('/disk/1/data/niktakbr/','/disk/0/home/niktakbr/')):raise ValueError('source outside owned disk roots')
 resolved=p.resolve()
 if not str(resolved).startswith(('/disk/1/data/niktakbr/','/disk/0/home/niktakbr/')):raise ValueError('source resolves outside owned disk roots')
 return p

class ChannelStore(VariantStore):
 def __init__(self,path,writable=False):
  super().__init__(path,writable=writable);self.hash_cache={}
  if not self.db.execute("select 1 from sqlite_master where name='rag_channel_schema'").fetchone():
   if not writable:raise ValueError('channel migration required on separate working database')
   self.db.executescript((HERE/'schema.sql').read_text())
   with self.db:self.db.execute('insert into rag_channel_schema values(?,?,?)',(VERSION,sha(HERE/'schema.sql'),sha(HERE/'CHANNEL_SELECTION.json')))
  expected=[(VERSION,sha(HERE/'schema.sql'),sha(HERE/'CHANNEL_SELECTION.json'))]
  if self.db.execute('select * from rag_channel_schema').fetchall()!=expected:raise ValueError('channel schema/selection mismatch')
 def verify_file(self,path,expected):
  p=owned(path);s=p.stat();signature=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  previous=self.hash_cache.get(str(p))
  if previous is None or previous[0]!=signature:self.hash_cache[str(p)]=(signature,sha(p))
  if self.hash_cache[str(p)][1]!=expected:raise ValueError('source hash mismatch: '+str(p))
 def verify_binding(self,b):
  from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.retrieval import guard
  paths=[(b[k+'_path'],b[k+'_sha256']) for k in ('xml','asset_manifest','mapping')]
  if b.get('profile_path'):paths.append((b['profile_path'],b['profile_sha256']))
  v=json.loads(self.db.execute('select body from rag_env_variants where id=?',(b['variant_id'],)).fetchone()[0]);paths += [(a['path'],a['sha256']) for a in v['assets']]
  for p,h in paths:self.verify_file(p,h)
  guard(self,b,{p:h for p,h in paths})
 def channel_snapshot(self):
  tables=('rag_channel_schema','rag_channel_records','rag_channel_jobs','rag_channel_fts')
  values={t:self.db.execute('select * from '+t+' order by 1').fetchall() for t in tables}
  return dict(version=VERSION,records=len(values['rag_channel_records']),executions=len(values['rag_channel_jobs']),logical_digest=digest(values),empirical_admission_enabled=False)

def execution_sources(store):
 rows=store.db.execute("select execution_id,json_extract(body,'$.source_path'),json_extract(body,'$.source_sha256') from evidence where kind='raw_measurement' group by execution_id order by execution_id").fetchall()
 assert len(rows)==432
 return rows

def require_hestia():
 if socket.gethostname().lower()!='hestia':raise RuntimeError('All processing must run on Hestia')
