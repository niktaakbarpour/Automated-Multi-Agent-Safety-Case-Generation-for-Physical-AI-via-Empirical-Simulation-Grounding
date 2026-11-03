"""Freeze the evaluated release and acceptance criteria before authoring questions."""
import json,subprocess,sqlite3,importlib.metadata,sys
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder,MODEL
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.config import ASSURANCES,PROVENANCE_SCOPE
from .config import *

def run():
 assert sha(DATABASE)==DATABASE_SHA;assert json.loads((WORK/'BASELINE_VERIFICATION.json').read_text())['passed']
 encoder=Encoder();tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE_COMMIT,'evaluation/r1_v4']).decode().splitlines()
 files={p:sha(REPO/p) for p in tracked if p.endswith(('.py','.sql')) and '/readiness_evaluation/' not in p}
 side=DATABASE.parent/'legacy_f/semantic.sqlite'
 r=dict(version='phase5j-evaluation-1',baseline_commit=BASE_COMMIT,database=dict(path=str(DATABASE),sha256=DATABASE_SHA),implementation_files=files,encoder=encoder.binding,encoder_manifest=dict(path=str(MODEL/'MODEL_MANIFEST.json'),sha256=sha(MODEL/'MODEL_MANIFEST.json')),legacy_semantic_sidecar=dict(path=str(side),sha256=sha(side)),modes=list(MODES),hybrid='NOT_IMPLEMENTED_NOT_EVALUATED',top_k=20,metric_cutoffs=[1,5,20],verification_mode='verified_session',strict_integrity_challenges=True,assurance_levels=list(ASSURANCES),provenance_scope=PROVENANCE_SCOPE,query_preprocessing='No harness tokenizer, synonym expansion, rewriting, reranking or NL-to-filter parser; exact text passed unchanged. Existing channel FTS uses OR of Unicode word tokens; legacy FTS uses AND. Existing encoder uses 256 wordpieces, masked mean L2 pooling and cosine.',ranking='Existing BM25/ID and local cosine/ID only; exact mode is structured-intent diagnostic, not NL understanding',scope='Explicit execution/task/variant and request constraints manually authored and frozen. Positive channel labels supplied only to exact diagnostic; NL modes receive scope and genuine interpretation constraints, never relevance labels.',filter_policy='Case-specific endpoint and explicit object/time/assurance/interpretation constraints frozen with questions; no result-dependent fallback or query decomposition',dependencies={n:importlib.metadata.version(n) for n in ('numpy','h5py','torch','transformers','tokenizers','safetensors')},runtime=dict(python=sys.version,sqlite=sqlite3.sqlite_version),selection_seed=SEED,ordering='Stable SHA256(seed+case_id+mode), development before final',reserved_payload_access=False,question_target=198,planned_split=dict(development=36,final=162),case_categories=9)
 criteria=dict(version='phase5j-gate-1',frozen_before_final=True,decisions=['READY','READY WITH CONDITIONS','NOT READY','NOT EVALUATED'],no_weighted_score=True,capabilities={
 'exact_source_value_retrieval':dict(ready='all eligible final direct/temporal/narrow-claim samples correct, attribution 1, complete required fields 1; oracle-structured only',minimum_numeric_correctness=1.),
 'natural_language_evidence_retrieval':dict(ready='at least one existing NL mode reaches all thresholds on answerable final cases, with supplied scope; no claim of autonomous intent parsing',precision_at_1=.90,recall_at_5=.90,recall_at_20=.95),
 'multi_source_completeness':dict(ready='all required evidence facets retrievable for >=95% final multi-source questions; action/clock facets count separately',complete_case_rate=.95),
 'scope_isolation':dict(ready='zero wrong execution/task/variant/time samples',maximum_errors=0),
 'source_integrity':dict(ready='all scratch missing/corrupt/redirected-source challenges fail closed; no false verified result',maximum_false_verified=0),
 'provenance_assurance':dict(ready='all explicit assurance requests honor scope and missing historical attestation; no silent downgrade',maximum_false_assurance=0),
 'uncertainty_abstention':dict(ready='all explicitly unsupported typed requests reject or clearly qualify raw-only results; ambiguity without typed parsing is conditional',minimum_correct_typed_handling=1.,maximum_unsupported_acceptance=0),
 'physical_interpretation':dict(ready='all requested positive physical properties verified; conditional/unavailable clocks/world transforms cannot be promoted',physical_safety_sufficiency='NOT_EVALUATED'),
 'independent_reproducibility':dict(ready='frozen dataset/config/reference hashes hold, second automated full replay and partial resume produce identical canonical results and metric aggregates',maximum_canonical_differences=0)},recommendation_rules=dict(A='No foundational failures and NL/multi-source capabilities ready for an explicitly bounded pilot',B='Integrity/scope foundations hold but NL, completeness, interface or ambiguity blockers need focused database-only correction',C='Foundational source integrity, scope isolation or false-assurance failures remain unmet'),rubric='External deterministic narrow-fact rubric only. No production sufficiency classifier or safety judge is added.')
 for n,d in [('FROZEN_EVALUATION_CONFIGURATION.json',r),('ACCEPTANCE_CRITERIA.json',criteria)]:
  with (HERE/n).open('x') as f:json.dump(d,f,sort_keys=True,indent=2)
 print('FROZEN',sha(HERE/'FROZEN_EVALUATION_CONFIGURATION.json'),sha(HERE/'ACCEPTANCE_CRITERIA.json'),flush=True)
if __name__=='__main__':run()
