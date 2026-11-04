"""Capability classifications name exact bounded contracts, not general safety accuracy."""
import json
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def write():
 rows=[]
 def add(name,state,scope,limits):rows.append(dict(capability=name,status=state,scope=scope,limitations=limits))
 add('structured_exact_lookup','SUPPORTED','Exact registered channel/field and original record ID within one indexed execution','Does not expose every legacy evidence family or arbitrary SQL')
 add('raw_measurements','SUPPORTED','Six registered source arrays/count; descriptor-bound values at selected saved frames','No normalization, invented observations or new channels')
 add('physical_interpretation_metadata','SUPPORTED WITH CONDITIONS','Existing Phase5H verified/conditional native component/unit contracts','Native/model convention, not physical calibration or world coordinates')
 add('temporal_windows','SUPPORTED WITH CONDITIONS','Inclusive saved frames and exact stored simulator-label windows','No decimal rounding, interpolation, action/sensor synchronization; labels are associations')
 add('execution_task_variant_isolation','SUPPORTED','One explicit indexed execution with exact constraints; each obligation same scope','Cross-execution comparison not supported by this endpoint')
 add('geometry_identity','SUPPORTED WITH CONDITIONS','Exact registered object to verified native body/geom binding','Identity only; no pose/support/contact claim')
 add('main_table_symbolic_alias','SUPPORTED WITH CONDITIONS','Existing 147-execution/98-variant tabletop symbolic audit only','No floor/living-room alias extrapolation, support inference or time/pose query')
 add('explicit_multisource_bundles','SUPPORTED WITH CONDITIONS','Validated registered families with independent per-obligation temporal coverage','Mandatory-only completeness; optional absence stays visible; no shared physical instant')
 add('structured_completeness','SUPPORTED WITH CONDITIONS','All mandatory explicit obligations schema-valid, source-verified and independently fulfilled','Final release acceptance gate must pass; no claim or R1 sufficiency')
 add('source_integrity','SUPPORTED','Strict default; explicit verified-session policy with identity invalidation','Caller trusts Git-bound release; no unverified source fallback; current bytes only')
 add('provenance_assurance','SUPPORTED WITH CONDITIONS','Current source identity or explicit release-evidence-graph-v1 closure','Bounded inherited data/dependency graph plus current release manifest; not historical closure')
 add('recorded_metadata_references','SUPPORTED WITH CONDITIONS','Recorded clocks, policy/inference, camera/contact refs, execution declarations','Requires primary source closure including HDF5; references do not establish events or sensor exposure time')
 for name in ('natural_language_interpretation','lexical_retrieval','semantic_retrieval','legacy_general_record_search'):
  add(name,'EXPERIMENTAL','Preserved earlier routes for exploratory inspection','No production completeness; K.1 limitations/results remain unchanged')
 for name,limit in [('historical_producer_attestation','No complete contemporary binary/process attestation; 103/104 producer-file discrepancy remains documented'),('sensor_synchronization','No independent per-sensor clock mapping/calibration'),('world_transformations','No verified world transforms or calibrated pixel coordinates'),('physical_support_contact_fall','Metadata/counts/geometry do not establish physical events'),('empirical_R1_admission','Disabled; no checker decision changes'),('safety_case_agents','Not implemented or authorized')]:add(name,'UNSUPPORTED','No supported production contract',limit)
 registry=dict(version=VERSION,database_sha256=DATABASE_SHA,catalogue_sha256=CATALOGUE_SHA,capabilities=rows,families={f:dict(field=field,temporal_required=f in TEMPORAL_FAMILIES,kind='recorded_measurement' if f in CHANNELS else 'metadata_or_verified_reference',source='Existing Phase5G/H/I/K contracts; final decoder references unchanged') for f,field in REGISTRY.items()},evidence_universe='432 indexed executions /104 verified variants; no reserved/preflight/candidate payloads',route_boundary='Only explicit structured requests are eligible; experimental result objects fail query schema')
 (HERE/'CAPABILITY_REGISTRY.json').write_text(json.dumps(registry,sort_keys=True,indent=2));return registry
if __name__=='__main__':write()
