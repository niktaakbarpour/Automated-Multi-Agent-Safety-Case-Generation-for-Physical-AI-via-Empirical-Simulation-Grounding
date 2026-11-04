"""Representation only. No query interpretation or completeness decisions here."""
from evaluation.r1_v4.provenance import digest
from .config import VERSION

def obligation(query,kind,target,basis,families=(),status='RESOLVED',scope=None,temporal=None,mandatory=True,uncertainty=None):
 start,end=basis if isinstance(basis,tuple) else (None,None)
 origin=dict(span=[start,end],text=query[start:end],source='original_query') if start is not None else dict(source=basis)
 identity=dict(type=kind,target=target,basis=origin,required_families=list(families),scope=scope or {},temporal=temporal)
 return dict(id='obligation:'+digest(identity),type=kind,target=target,basis=origin,required_families=list(families),required_temporal_scope=temporal,scope=scope or {},verification_requirements=['descriptor_bound_source','execution_variant_identity'],mandatory=mandatory,resolution_status=status,uncertainty=uncertainty,contract_references=['Phase5H physical/source contracts','Phase5I provenance/clock contracts',VERSION])

def signature(o):return (o['type'],str(o['target']))
