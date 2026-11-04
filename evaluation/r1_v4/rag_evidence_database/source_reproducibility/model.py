"""Attestation categories never collapse present byte identity into historical execution proof."""
from evaluation.r1_v4.provenance import digest
from .config import CATEGORIES,PROVENANCE_SCOPE

SCOPE_DEFINITION=dict(id=PROVENANCE_SCOPE,meaning='Complete declared evidence/interpretation lineage and selected current critical decoder ABI artifacts for one execution; not historical producer/environment completeness',requires=('source_recording','variant_binding','interpretation_proofs','producer_record_content','critical_current_decoder_artifacts'),excludes=('unattested_historical_binaries','complete_transitive_environment','unrestored_video_resource_payloads','physical_clock_synchronization'))

def validate_claim(claim):
 if claim['category'] not in CATEGORIES:raise ValueError('unknown provenance category')
 if claim['historical_attestation'] not in ('RECORDED_DECLARATION_ONLY','NOT_ATTESTED','NOT_APPLICABLE'):raise ValueError('No historical-attestation verifier/root is available in this release')
 if claim['category']=='HISTORICAL_RECORD' and claim.get('source_origin')!='ORIGINAL_RECORD_ARTIFACT':raise ValueError('current artifacts cannot masquerade as historical records')
 if claim['category']=='RETROSPECTIVE_ARTIFACT' and claim['historical_attestation']=='RECORDED_DECLARATION_ONLY':raise ValueError('retrospective verification is not historical attestation')
 if claim.get('independently_verified_creation_date') is not None:raise ValueError('No trusted timestamp authority evidence is available')
 if not claim.get('basis') or not claim.get('limitations'):raise ValueError('explicit basis and limitations required')
 return claim

def claim(execution,property,value,category,source,selector,basis,assumptions=()):
 c=dict(execution_id=execution,property=property,value=value,category=category,source_origin='ORIGINAL_RECORD_ARTIFACT' if category=='HISTORICAL_RECORD' else 'CURRENT_VERIFICATION_OR_RECONSTRUCTION',source_artifact=source,source_selector=selector,integrity_status='SOURCE_RECORD_OR_ARTIFACT_HASH_BOUND',historical_attestation='RECORDED_DECLARATION_ONLY' if category=='HISTORICAL_RECORD' else 'NOT_ATTESTED',independently_verified_creation_date=None,basis=basis,assumptions=list(assumptions),limitations='Does not establish historical running binaries, clean checkout, container image, calibrated clocks or physical safety.')
 validate_claim(c);return dict(id='claim:'+digest(c),**c)
