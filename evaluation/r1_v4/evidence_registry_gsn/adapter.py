"""Measurement availability adapter; no change to V4 admission."""
from evaluation.r1_v4.contracts import Evidence,Truth,Validity
from evaluation.r1_v4.provenance import primitive

PHYSICAL_GATES=('G03_geometry_empirical_admission','G07_static_coverage_composition','G09_contact_based_physical_evidence','G04_initial_support_applicability','G05_validated_falling_witness','G06_qualified_negative_certificate','G10_uncertainty_propagation','G11_temporal_empirical_admission','G12_independent_reference_validation')

def assessment(retrieval,gates):
 # Hard disabled independently of input flags; changing gate metadata cannot activate admission.
 missing=[g for g in PHYSICAL_GATES if gates.get(g)!='VERIFIED']
 return {'schema_version':'1.0.0','requirement_id':'R1','requirement_version':'2.0.0',
  'evidence_retrieved':bool(retrieval['matching_evidence_ids']),
  'measurement_records_valid':[r['id'] for r in retrieval['evidence'] if r['validation_status']=='verified_measurement'],
  'missing_evidence':retrieval['missing_evidence'],'uncertainty':retrieval['uncertainty'],
  'capability_statuses':dict(sorted(gates.items())),'missing_capability_gates':missing,'sufficient_for_physical_checking':False,
  'claim_status':'unresolved','safety_claim_supported':False,'physical_safety_conclusion':False,
  'empirical_admission_enabled':False,'restriction':'Measurement availability only; empirical admission disabled by this adapter contract.'}

def typed_observation(evidence):
 if not isinstance(evidence,Evidence) or evidence.kind!='direct_measurement' or evidence.claim!='observation' or evidence.truth!=Truth.UNKNOWN or evidence.validity!=Validity.VERIFIED:raise ValueError('only unknown-truth validated observations')
 return primitive(evidence)
