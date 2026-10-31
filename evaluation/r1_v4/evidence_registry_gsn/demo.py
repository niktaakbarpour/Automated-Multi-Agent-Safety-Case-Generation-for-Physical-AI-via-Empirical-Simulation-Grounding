"""Reproducible R1 -> retrieval -> unresolved GSN demonstration."""
from pathlib import Path
from .builder import build,HERE
from .registry import Registry
from .retrieval import Query,retrieve
from .adapter import assessment
from .gsn import Node,Edge,Graph
from evaluation.r1_v4.provenance import load,write_new


def demonstrate(out):
 out=Path(out).resolve()
 if not out.is_relative_to('/disk/1/data/niktakbr') or out.exists():raise ValueError('fresh owned disk1 output required')
 out.mkdir(parents=True)
 registry=Registry(out/'registry.sqlite',create=True);binding=build(registry)
 q=Query('G_R1','R1','2.0.0',binding['execution_id'],'cream_cheese_1',('object_pose','contact','native_geometry','timestamp','camera_reference'),(9,12),'frame','saved_frame_index',{'measurement_availability':'VERIFIED'})
 found=retrieve(registry,q)
 gates=load(HERE.parent/'evidence_review_readiness/READINESS_STATUS.json')
 assessed=assessment(found,{g['gate_id']:g['status_after_review'] for g in gates['gates']})
 scope={k:getattr(q,k) for k in ('requirement_id','requirement_version','execution_id','object_id','interval','domain','clock')}
 prov={'phase':'5A','claim_source':'Finalized R1 v2.0; demonstration scope only'}
 nodes=[Node('G_R1','goal','R1 physical safety claim remains unresolved.',scope,prov,'unresolved','unresolved_conclusion',physical_claim=True),Node('S1','strategy','Inspect available measurements and capability gates before any physical checking.',scope,prov,'proposed','llm_proposal'),Node('C1','context','Development-only saved frames 9 through 12 requested; 9,10,11 indexed.',scope,prov,'provisional','normative_document'),Node('A1','assumption','No assumption of load-bearing support or camera exposure alignment is admitted.',scope,prov,'provisional','llm_proposal'),Node('J1','justification','Source integrity and recorded measurement validity do not establish physical safety.',scope,prov,'provisional','normative_document'),Node('D1','defeater','Missing frame 12, physical support/fall/coverage contracts and independent references.',scope,{'assessment':assessed},'unresolved','unresolved_conclusion'),Node('U1','unresolved_claim','Initial support and subsequent in-scope falling cannot be assessed under an admitted empirical profile.',scope,{'assessment':assessed},'unresolved','unresolved_conclusion',physical_claim=True)]
 edges=[Edge('G_R1','S1','supported_by'),Edge('S1','U1','supported_by'),Edge('G_R1','D1','challenged_by')]+[Edge('G_R1',n,'in_context_of') for n in ('C1','A1','J1')]
 for i,r in enumerate(found['evidence']):
  key=f'E{i:03d}';nodes.append(Node(key,'solution','Available '+r['measurement_type']+' observation; physical truth unknown.',{**scope,'interval':r['interval']}, {'source_path':r['source_path'],'source_sha256':r['source_sha256'],'selector':r['selector']},r['validation_status'],'retrieved_observation',r['id']));edges.append(Edge('S1',key,'supported_by'))
 graph=Graph(tuple(nodes),tuple(edges)).validate(registry)
 for name,value in [('REGISTRY_EXPORT.json',registry.export()),('BUILD_MANIFEST.json',binding),('RETRIEVAL.json',found),('ASSESSMENT.json',assessed),('GRAPH.json',graph.export()),('REGISTRY_INTEGRITY.json',registry.integrity())]:write_new(out/name,value)
 report=f'''# Development R1 safety argument scaffold

Execution: {q.execution_id}; object: {q.object_id}; requirement R1 2.0.0.

1. Evidence retrieved: {len(found['matching_evidence_ids'])} records from saved frames 9, 10, 11.
2. Measurement records structurally valid: {len(assessed['measurement_records_valid'])}. Exact source hashes, selectors and dependencies appear in RETRIEVAL.json and REGISTRY_EXPORT.json.
3. Sufficient for physical checking: false. Each requested type lacks frame 12 in this index; source existence beyond the index does not fill its scope. Physical support, fall, negative, phase/uncertainty and independent-reference gates remain blocked.
4. Safety claim supported: false. G_R1 and U1 remain unresolved. No empirical V4 assessment was invoked.

GRAPH.json exports {len(nodes)} typed nodes and {len(edges)} constrained edges. Solution nodes trace to immutable registry IDs. A supported_by structural edge records argument organization, not a verified support verdict. Contact records do not prove load-bearing support. Geometry is exact-source BOX metadata; physical uncertainty is uncalibrated. Camera references retain unknown exposure times. AI interpretation is separately indexed as provisional, not retrieved as a measurement or human reference.

No raw images, videos or numerical arrays are exported. SQLite is a local index, not a safety certificate. The fixed development example is not an accuracy evaluation.
'''
 (out/'ARGUMENT.md').write_text(report)
 registry.close();return binding
