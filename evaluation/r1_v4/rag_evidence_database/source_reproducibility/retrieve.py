"""Explicit assurance requests cannot silently downgrade."""
from dataclasses import dataclass,asdict,replace
import math
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.retrieve import PhysicalQuery,retrieve as physical,empty
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceError
from .config import ASSURANCES,PROVENANCE_SCOPE
@dataclass(frozen=True)
class ProvenanceQuery(PhysicalQuery):
 assurance:str='verified_source_values'
 provenance_scope:str|None=None
 clock_domain:str='saved_frame_index'
 seconds_interval:tuple|None=None

def retrieve(store,q,**kw):
 if not isinstance(q,ProvenanceQuery):raise TypeError('ProvenanceQuery required')
 if q.assurance not in ASSURANCES:return empty(q,'unsupported_assurance','Unknown assurance')
 if q.assurance=='historical_producer_attestation':return empty(q,'unattested_historical_producer','No exact historical binary/process attestation; no downgrade')
 if q.assurance=='provenance_complete' and q.provenance_scope!=PROVENANCE_SCOPE:return empty(q,'unsupported_provenance_scope','Explicit bounded graph scope required; full historical closure unavailable')
 if q.clock_domain not in ('saved_frame_index','simulator_endpoint_label'):return empty(q,'unsupported_clock','No per-sensor timestamps or calibrated clock mapping')
 if (q.seconds_interval is None)!=(q.clock_domain=='saved_frame_index'):return empty(q,'invalid_clock_query','Simulator labels require a recorded-seconds window')
 fields={k:v for k,v in asdict(q).items() if k in PhysicalQuery.__dataclass_fields__}
 if q.assurance=='verified_physical_interpretation':
  fields['required_properties']=tuple(set(q.required_properties)|{'component_order','units','coordinate_frame'});fields['allow_conditional']=False
 if q.seconds_interval is not None:
  w=q.seconds_interval
  if q.interval is not None or not isinstance(w,(tuple,list)) or len(w)!=2 or any(type(x) not in (float,int) or not math.isfinite(x) for x in w) or w[1]<w[0]:return empty(q,'invalid_clock_query','Finite ordered simulator-label interval required')
  frames=store.db.execute('select frame from i_clock_labels where execution=? and sim_time>=? and sim_time<=? order by frame',(q.execution_id,*w)).fetchall()
  if not frames:return empty(q,'no_matching_record','No recorded simulator endpoint labels in window')
  fields['interval']=(frames[0][0],frames[-1][0])
 # The inherited reader checks immutable DB, task/variant/source/unit/frame before ranking and descriptor reads.
 result=physical(store,PhysicalQuery(**fields),**kw)
 if not result['results']:return result
 if q.assurance=='provenance_complete':
  try:result['provenance_verification']=store.provenance(q.execution_id,q.verification_mode)
  except (SourceError,OSError,ValueError) as e:return empty(q,'provenance_integrity_failure',str(e))
 result['assurance']=q.assurance;result['clock_domain']=q.clock_domain;result['historical_runtime_attested']=False
 return result
