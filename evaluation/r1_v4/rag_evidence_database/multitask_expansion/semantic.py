"""Optional local CPU encoder sidecar; core SQL validity gates remain authoritative."""
import sqlite3,sys,os,platform
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.provenance import canonical,load,digest,bytes_digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.search import search
MODEL=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/encoder')
VERSION='local-semantic-measurements:1.0.0'
DESCRIPTIONS={
 'object_pose':'Object position and orientation. Where the object is located in world coordinates; body translation and quaternion. Recorded pose observation.',
 'contact':'Contact observations. Which collision bodies touch; contact ownership geometry identifiers, separation distances and contact positions. Forces and normals unavailable.',
 'native_geometry':'Collision geometry references and world transforms. Native geometry identities, shape layout and spatial collision geometry position and rotation. Physical geometry calibration unavailable.',
 'robot_state':'Robot and gripper state. Robot joint configuration angles, velocities and control inputs. Available robot movement measurements.',
 'timestamp':'Recorded observation time. Saved endpoint timestamps in seconds and frame indices. Camera exposure timing unknown.',
 'camera_reference':'Linked images. Camera frame references for external agentview and wrist eye in hand views. Source image locations, no image content or camera exposure alignment.'}

def descriptor(record):
 if record.kind!='raw_measurement' or record.measurement_type not in DESCRIPTIONS:return None
 return 'Object '+record.object_id.replace('_',' ')+'. '+DESCRIPTIONS[record.measurement_type]+' Measurement availability only, no physical event or safety judgment.'

class Encoder:
 def __init__(self):
  os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
  import torch,transformers
  manifest=load(MODEL/'MODEL_MANIFEST.json')
  if manifest['revision']!='1110a243fdf4706b3f48f1d95db1a4f5529b4d41':raise ValueError('encoder revision')
  if next(f['sha256'] for f in manifest['files'] if f['name']=='model.safetensors')!='53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db':raise ValueError('unapproved encoder weights')
  for f in manifest['files']:
   if sha(f['path'])!=f['sha256']:raise ValueError('encoder integrity')
  torch.set_num_threads(2);torch.manual_seed(0);torch.use_deterministic_algorithms(True)
  self.torch=torch;self.tokenizer=transformers.AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
  self.model=transformers.AutoModel.from_pretrained(MODEL,local_files_only=True,use_safetensors=True).to('cpu').eval()
  self.binding={'version':VERSION,'revision':manifest['revision'],'manifest_sha256':sha(MODEL/'MODEL_MANIFEST.json'),'torch':torch.__version__,'transformers':transformers.__version__,'python':platform.python_version(),'pool':'attention-masked mean, L2 normalization','max_wordpieces':256,'device':'cpu','dtype':'float32','threads':2,'code_sha256':sha(Path(__file__)),'text_policy':'Source-field descriptions and object identity; no execution IDs, numerical values or AI event labels.'}
 def encode(self,texts):
  torch=self.torch;values=[]
  with torch.inference_mode():
   for start in range(0,len(texts),16):
    tokens=self.tokenizer(texts[start:start+16],padding=True,truncation=True,max_length=256,return_tensors='pt');output=self.model(**tokens).last_hidden_state;mask=tokens['attention_mask'].unsqueeze(-1).expand(output.size()).float();pooled=(output*mask).sum(1)/mask.sum(1).clamp(min=1e-9);values.append(torch.nn.functional.normalize(pooled,p=2,dim=1).numpy())
  import numpy as np
  return np.concatenate(values) if values else np.empty((0,384),dtype='float32')

def build(store,path,encoder):
 path=Path(path).resolve()
 if not path.is_relative_to('/disk/1/data/niktakbr') or path.exists():raise ValueError('sidecar requires new owned disk1 path')
 records=store.records();texts={};aliases=[]
 for r in records:
  text=descriptor(r)
  if text is None:continue
  key=digest(text);texts[key]=text;aliases.append((r.id,key))
 keys=sorted(texts);vectors=encoder.encode([texts[k] for k in keys]);db=sqlite3.connect(path)
 try:
  db.executescript('CREATE TABLE meta(body TEXT NOT NULL);CREATE TABLE vectors(id TEXT PRIMARY KEY,text TEXT NOT NULL,vector BLOB NOT NULL);CREATE TABLE aliases(evidence_id TEXT PRIMARY KEY,text_id TEXT NOT NULL REFERENCES vectors(id));')
  manifest={'schema_version':'1.0.0','source_database_path':str(Path(store.path).resolve()) if hasattr(store,'path') else str(store.db.execute('PRAGMA database_list').fetchone()[2]),'source_database_sha256':sha(store.db.execute('PRAGMA database_list').fetchone()[2]),'encoder':encoder.binding,'descriptors':len(keys),'evidence_aliases':len(aliases),'dimensions':384,'vector_content_digest':digest({key:bytes_digest(vectors[i].astype('<f4').tobytes()) for i,key in enumerate(keys)}),'raw_types':sorted(DESCRIPTIONS),'physical_checking':False}
  with db:
   db.execute('INSERT INTO meta VALUES(?)',(canonical(manifest).decode(),));db.executemany('INSERT INTO vectors VALUES(?,?,?)',[(key,texts[key],vectors[i].astype('<f4').tobytes()) for i,key in enumerate(keys)]);db.executemany('INSERT INTO aliases VALUES(?,?)',aliases)
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  return manifest
 finally:db.close()

class SemanticIndex:
 def __init__(self,path,store,encoder):
  self.db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True);self.encoder=encoder;self.store=store;self.meta=load_json(self.db.execute('SELECT body FROM meta').fetchone()[0])
  if self.meta['source_database_sha256']!=sha(store.db.execute('PRAGMA database_list').fetchone()[2]) or self.meta['encoder']!=encoder.binding:raise ValueError('semantic/source version mismatch')
 def close(self):self.db.close()
 def retrieve(self,query,text):
  if not isinstance(text,str) or not text.strip() or len(text)>1000:raise ValueError('semantic query text')
  if query.text is not None:raise ValueError('separate semantic text from FTS text')
  result=search(self.store,replace(query,limit=100))
  if result['matching_count']>100:raise ValueError('semantic candidate pool too broad; narrow metadata filters')
  import numpy as np
  q=self.encoder.encode([text])[0];ranked=[];unindexed=[]
  for item in result['results']:
   row=self.db.execute('SELECT v.vector FROM aliases a JOIN vectors v ON v.id=a.text_id WHERE a.evidence_id=?',(item['id'],)).fetchone()
   if row is None:unindexed.append(item['id']);continue
   ranked.append({**item,'semantic_cosine':float(np.dot(q,np.frombuffer(row[0],dtype='<f4')))})
  ranked.sort(key=lambda item:(-item['semantic_cosine'],item['id']))
  return {**result,'source_filter_matching_count':result['matching_count'],'matching_count':len(ranked),'source_filter_evidence_retrieved':result['evidence_retrieved'],'evidence_retrieved':bool(ranked),'source_filter_query_id':result['query_id'],'query_id':'semantic-query:'+digest({'filter_query_id':result['query_id'],'semantic_text':text,'encoder':self.encoder.binding,'source_database_sha256':self.meta['source_database_sha256']}),'semantic_text':text,'results':ranked[:query.limit],'semantic_matching_count':len(ranked),'unindexed_evidence_ids':unindexed,'semantic_version':VERSION,'ranking_is_not_physical_confidence':True,'retrieval_rationale':'Core metadata, source, dependency and capability filters before local cosine ranking. Sidecar supports raw measurement descriptions only; coverage reports core valid matches.'}

def load_json(value):
 from evaluation.r1_v4.provenance import strict_loads
 return strict_loads(value)

def integrity(index):
 import numpy as np
 from evaluation.r1_v4.provenance import bytes_digest
 assert index.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not index.db.execute('PRAGMA foreign_key_check').fetchall()
 expected={r.id:digest(descriptor(r)) for r in index.store.records() if descriptor(r) is not None}
 assert dict(index.db.execute('SELECT evidence_id,text_id FROM aliases'))==expected
 hashes={}
 for key,text,blob in index.db.execute('SELECT id,text,vector FROM vectors ORDER BY id'):
  assert digest(text)==key
  v=np.frombuffer(blob,dtype='<f4');assert v.shape==(384,) and np.isfinite(v).all() and abs(float(np.dot(v,v))-1)<1e-5
  hashes[key]=bytes_digest(blob)
 assert digest(hashes)==index.meta['vector_content_digest']
 return {'passed':True,'aliases_verified':len(expected),'vectors_verified':len(hashes),'source_database_sha256':index.meta['source_database_sha256'],'qualification':'Vector norm guard checks numerical encoder representation, not physical measurement uncertainty.'}
