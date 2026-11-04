"""Phase 5I assurance metadata over unchanged strict Phase 5H sources."""
import json
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.store import PhysicalStore
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceError,SourceVerifier
from .build import producers,enc
from .config import VERSION
class ProvenanceStore(PhysicalStore):
 def __init__(self,path,expected_sha256=None,**kw):
  super().__init__(path,expected_sha256=expected_sha256,**kw)
  meta=dict(self.db.execute('select * from i_meta'))
  if meta.get('version')!=VERSION or meta.get('producer')!=enc(producers()):raise SourceError('provenance_schema_or_producer_mismatch')
 def provenance(self,execution,mode='strict'):
  rows=self.db.execute('select distinct a.path,a.sha256 from i_artifacts a join i_scope_nodes s on s.node=a.id where s.execution=? order by a.path',(execution,)).fetchall()
  if not rows:raise SourceError('missing_provenance_scope')
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
  for p,h in rows:self.verifier.verify(str(owned(p)),h,mode)
  depv=SourceVerifier(roots=('/disk/1/data/niktakbr','/disk/0/home/niktakbr','/usr/bin','/usr/lib','/usr/lib64'))
  deps=self.db.execute("select distinct a.path,a.sha256 from i_artifacts a join i_edges e on e.target=a.id where e.relation='current_artifact'").fetchall()
  for p,h in deps:depv.verify(p,h,mode)
  return dict(current_dependency_artifacts=len(deps),scope='release-evidence-graph-v1',verified_artifacts=len(rows),historical_runtime_attested=False)
