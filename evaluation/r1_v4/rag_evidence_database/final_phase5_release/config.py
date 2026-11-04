from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.config import DATABASE,DATABASE_SHA,CHANNELS,FIELDS,FAMILIES,UNITS
HERE=Path(__file__).parent
REPO=HERE.parents[3]
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5l-working')
CATALOGUE=Path('/disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite')
CATALOGUE_SHA='ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e'
BASE_COMMIT='9de85693fae1323cc2ce12edf59268c8bd0e7c58'
BASE_MANIFEST_SHA='557a93d25d9b2bd4571af14cdfe414fd016ee95d7d1813cebf77b87144c55344'
VERSION='phase5-structured-1.0.0'
PROVENANCE_SCOPE='release-evidence-graph-v1'
GROUP_FIELDS=dict(source_provenance='source_identity',execution_metadata='recorded_execution_metadata',geometry_identity='native_object_identity',main_table_identity='verified_symbolic_alias',recorded_time='recorded_clock_labels',action_metadata='policy_action_metadata',inference_metadata='inference_call_metadata',camera_references='saved_image_references',contact_references='recorded_contact_references')
REGISTRY=dict(zip(CHANNELS,FIELDS))|GROUP_FIELDS
TEMPORAL_FAMILIES=set(CHANNELS)|{'recorded_time','action_metadata','inference_metadata','camera_references','contact_references'}
ASSURANCES=('verified_source_values','verified_physical_interpretation','provenance_complete','historical_producer_attestation')

QUERY_SCHEMA_SHA='3c1d109fca5fd80206c0c2f3b2640e015e4aa4d83b6993f623cac4aadc9c9313'
