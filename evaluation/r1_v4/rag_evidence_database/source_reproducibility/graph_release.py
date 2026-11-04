"""Compact reproducible virtual graph edges over preserved extraction declarations."""
import json
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import HERE,VERSION

def supplement(c,database_sha256):
 release='release:'+VERSION;interface='interface:'+VERSION
 nodes=[dict(id=release,kind='release_descriptor',database_sha256=database_sha256,manifest_path=str(HERE/'ARTIFACT_MANIFEST.json'),manifest_trust='Caller must supply external SHA256; omitted here to avoid a content-hash cycle',historical_attestation='NOT_ATTESTED'),dict(id=interface,kind='retrieval_interface',files=[dict(path=str(HERE/n),sha256=sha(HERE/n)) for n in ('retrieve.py','store.py')],historical_attestation='NOT_APPLICABLE')]
 edges=[dict(source=release,target=interface,relation='packages_interface',basis='These files implement the release assurance API and are hash-bound by the manifest')];views=[];counts=0
 for family,table,idcol,expr in [('evidence','evidence','id',"coalesce(json_extract(body,'$.producer'),'UNSPECIFIED')"),('channel','rag_channel_records','id',"coalesce(json_extract(body,'$.contract.version'),'UNSPECIFIED')||':'||coalesce(json_extract(body,'$.contract_sha256'),'UNSPECIFIED')"),('interpretation','h_semantics','raw_id',"coalesce(json_extract(body,'$.version'),(select value from h_meta where key='version'),'UNSPECIFIED')")]:
  prefix='extraction_declaration:'+family+':'
  for value,n in c.execute('select '+expr+',count(*) from '+table+' group by '+expr):
   node=prefix+value;nodes.append(dict(id=node,kind='stored_extraction_contract_declaration',family=family,declared_identity=value,record_count=n,classification='RETROSPECTIVE_DATABASE_METADATA',historical_runtime_attested=False,basis='Verbatim producer or contract identity in preserved database; not a historical simulator producer claim'))
   edges.append(dict(source=release,target=node,relation='preserves_contract',basis='The pinned database contains these original declarations unchanged'))
  sql="SELECT '"+family+":'||"+idcol+" AS source, '"+prefix+"'||("+expr+") AS target, 'declares_extraction_contract' AS relation FROM "+table+" ORDER BY "+idcol
  rows=c.execute(sql).fetchall();assert all(r[0] and r[1] for r in rows);counts+=len(rows);views.append(dict(family=family,sql=sql,edge_count=len(rows),basis='Direct association from the same preserved row; no inferred historical execution edge'))
 # Every indexed record is a member of this pinned release, without repeating paths per record.
 membership="SELECT node AS source, '"+release+"' AS target, 'release_member' AS relation FROM i_record_scope ORDER BY node"
 membership_count=c.execute('select count(*) from i_record_scope').fetchone()[0];views.append(dict(sql=membership,edge_count=membership_count,basis='Explicit membership in the hash-pinned release database'))
 return dict(nodes=nodes,edges=edges,relationship_views=views,explicit_nodes=len(nodes),explicit_edges=len(edges),virtual_edges=counts+membership_count,scope='Release metadata links; not historical simulator producer attestation')
