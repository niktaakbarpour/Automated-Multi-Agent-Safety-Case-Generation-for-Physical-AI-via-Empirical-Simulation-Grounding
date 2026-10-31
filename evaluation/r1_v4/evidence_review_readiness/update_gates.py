"""Review report only; no runtime gate mutation, calibration or classifier."""
import csv,socket
from .review_sources import HERE,PROFILE
from evaluation.r1_v4.libero_evidence_audit.audit_sources import csvwrite,save
MINIMUM={
 'G01':'None for the existing exact-source measurement scope; new models require new bindings.',
 'G02':'None for exact-input numerical arithmetic; physical input uncertainty is separate.',
 'G03':'Recover or justify native shape/serialization precision and verify designated faces; bind independent geometry uncertainty to this model.',
 'G04':'Independently review existing support/unsupported candidates and validate a load-bearing or force-free alternative plus t0 phase/uncertainty.',
 'G05':'One independently verified in-scope support-loss/downward reference with handling/origin controls, then a calibrated scoped profile; no post-lift/setup relabeling.',
 'G06':'Validated support/transition clear certificates for a prospectively fixed requested domain; partial static-looking samples do not certify the original execution.',
 'G07':'Admitted compatible static cells and explicit qualified join evidence on the same clock/scope, preserving shared dependencies.',
 'G08':'A separately approved dynamic/handling composition contract and validated inference profile; additional images alone cannot enable it.',
 'G09':'Independently validated load-bearing interpretation or justified force-free alternative with competing supports; normals/forces cannot be invented.',
 'G10':'Justified geometry/input/phase uncertainty bounds and dependency-aware propagation tests; null necessary bounds must continue to block claims.',
 'G11':'Version-matched recorder/engine phase contract or separately authorized instrumented timing reference; keep uncalibrated cameras qualitative if optional.',
 'G12':'Independent human/source review and adjudication, frozen reference/protocol hashes and disjoint positive/negative/NA/U validation; AI agreement is insufficient.',
}
def main():
 assert socket.gethostname().lower()=='hestia'
 old=list(csv.DictReader((PROFILE/'EVIDENCE_GATES.csv').open()));updated=[]
 for r in old:
  prefix=r['gate_id'][:3]
  updated.append(dict(gate_id=r['gate_id'],previous_status=r['status'],status_after_review=r['status'],change='UNCHANGED',new_evidence='Eleven provisional AI reviews; ten numerical case windows; three authorized sheets/24 panels; no independent physical references',evidence_refs='AI_REFERENCE_REVIEWS.csv; EVIDENCE_LEDGER.csv; AUTHORIZED_VISUAL_EVIDENCE.json',why_status_does_not_progress='Visual context and additional review do not supply missing calibration, load-bearing, phase or independent-reference validity; no AI-consensus rule',minimum_additional_evidence=MINIMUM[prefix],empirical_admission_enabled=False))
 csvwrite(HERE/'UPDATED_EVIDENCE_GATES.csv',updated)
 save(HERE/'READINESS_STATUS.json',dict(gates=updated,status_promotions=0,status_demotions=0,read_only_measurements_ready=True,geometric_computations_ready_for_declared_inputs=True,conditional_indicators_ready_for_diagnostic_use=True,empirical_support_witness_ready=False,empirical_fall_witness_ready=False,qualified_negative_certification_ready=False,empirical_admission_enabled=False,independent_physical_reference_cases=0,framework_registry_and_argument_graph_planning_ready=True))
 print('Gate review complete:12; promotions:0; empirical admission:false')
if __name__=='__main__':main()
