"""Small paraphrase probe, never a physical-event reference annotation."""
from evaluation.r1_v4.provenance import write_new
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search

def probe(path,out):
 db=Store(path);execution='libero_long_openvla_oft_task00_seed1003_trial003_cfafd9ddc3db';rows=[]
 for typ,keyword,paraphrase in [('object_pose','pose','where is the object'),('contact','contact','which bodies touch'),('robot_state','robot state','robot movement measurements'),('timestamp','timestamp','show the recorded time of the observation'),('camera_reference','camera reference','which image is linked to this observation')]:
  base=dict(execution_id=execution,object_id='cream_cheese_1',evidence_types=(typ,),interval=(10,10))
  scoped=search(db,Query(**base));literal=search(db,Query(**base,text=keyword));natural=search(db,Query(**base,text=paraphrase))
  assert scoped['matching_count']==literal['matching_count']==1
  rows.append({'type':typ,'keyword':keyword,'paraphrase':paraphrase,'expected_id':scoped['results'][0]['id'],'structured_hits':scoped['matching_count'],'keyword_hits':literal['matching_count'],'paraphrase_hits':natural['matching_count']})
 db.close();write_new(out/'SEMANTIC_PROBE.json',{'schema_version':'1.0.0','cases':rows,'qualification':'Five hand-written source-target paraphrases on one new development execution; diagnostic only, not a representative semantic benchmark. No physical labels. No embedding comparison performed.'})
