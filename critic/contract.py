"""Shared vocabulary for the Critic contract.

Graph and evidence vocabularies are copied from the existing
evaluation/r1_v4/evidence_registry_gsn schemas (GSN 1.0.0, registry record
1.0.0). Outcome names come from evaluation/r1_v4/contracts.py. Nothing here
redefines those formats; the tests check that these copies stay in sync.
"""
import hashlib
import json
import math

REQUEST_SCHEMA_VERSION = 'critic-request/0.3.0'
REPORT_SCHEMA_VERSION = 'critic-report/0.4.0'

# --- existing GSN 1.0.0 vocabulary (gsn.py / gsn_graph.schema.json) ---
GSN_SCHEMA_VERSION = '1.0.0'
NODE_TYPES = {'goal', 'strategy', 'context', 'assumption', 'justification',
              'solution', 'defeater', 'unresolved_claim'}
NODE_ORIGINS = {'llm_proposal', 'retrieved_observation', 'checker_assessment',
                'ai_reference_judgment', 'human_reference_judgment',
                'normative_document', 'unresolved_conclusion'}
NODE_STATUSES = {'proposed', 'unresolved', 'verified_source',
                 'verified_measurement', 'provisional', 'checker_qualified'}
EDGE_TYPES = {'supported_by', 'in_context_of', 'challenged_by'}
SCOPE_KEYS = ('requirement_id', 'requirement_version', 'execution_id', 'object_id')
# record.kind -> the only node origin a solution citing that record may use
KIND_TO_ORIGIN = {
    'raw_measurement': 'retrieved_observation',
    'derived_measurement': 'retrieved_observation',
    'ai_reference_judgment': 'ai_reference_judgment',
    'human_reference_judgment': 'human_reference_judgment',
    'checker_assessment': 'checker_assessment',
    'document': 'normative_document',
}

# --- existing registry record 1.0.0 vocabulary ---
RECORD_SCHEMA_VERSION = '1.0.0'
RECORD_REQUIRED = ('benchmark', 'capability', 'clock', 'conflicts', 'coordinate_frame',
                   'dependencies', 'domain', 'execution_id', 'id', 'interval', 'kind',
                   'limitations', 'measurement_type', 'missing_intervals',
                   'model_checkpoint', 'object_id', 'original', 'producer', 'provenance',
                   'requirement_id', 'requirement_version', 'schema_version', 'selector',
                   'source_path', 'source_sha256', 'task_id', 'uncertainty',
                   'validation_status')
UNUSABLE_RECORD_STATUSES = {'invalid', 'missing', 'unsupported'}

# --- R1 v2 outcomes (evaluation/r1_v4/contracts.py) ---
VIOLATION = 'violation_observed'
NO_VIOLATION = 'no_violation_observed_within_validated_coverage'
NOT_APPLICABLE = 'not_applicable'
INSUFFICIENT = 'insufficient_information'
INVALID_CONTRACT = 'invalid_measurement_contract'
OUTCOMES = {VIOLATION, NO_VIOLATION, NOT_APPLICABLE, INSUFFICIENT, INVALID_CONTRACT}
# FORMAL_SEMANTICS.md "Execution aggregation": V > IC > U > N > NA
OUTCOME_PRECEDENCE = (VIOLATION, INVALID_CONTRACT, INSUFFICIENT, NO_VIOLATION, NOT_APPLICABLE)
# Every outcome except insufficient_information needs an admitted checker assessment behind it
# (admission rules: critic/assessments.py).
NEEDS_CHECKER = OUTCOMES - {INSUFFICIENT}
# Evidence the R1 v2 configuration marks optional (R1_V2_CONFIG_SCHEMA.json, evidence_requirements:
# 'optional_or_derived_with_uncertainty', 'optional_unless_task_conditioned_claim'). A retrieval gap in
# one of these never undermines a no-violation claim on its own.
OPTIONAL_EVIDENCE = {'velocity', 'task_instruction'}

# The R1 configuration's saved_frame axis is the GSN graphs' frame domain on the saved_frame_index clock
# (evaluation/r1_v4/evidence_registry_gsn/demo/GRAPH.json). simulator_time has no agreed GSN clock yet.
AXIS_TO_CLOCK = {'saved_frame': ('frame', 'saved_frame_index')}
CONFIG_SCHEMA_ID = 'urn:trustworthy:r1:generalized:configuration:2.0.1'

# --- Phase 5 structured retrieval release (evaluation/r1_v4/rag_evidence_database/final_phase5_release) ---
# Pinned from its config.py and retrieval_remediation/config.py; the tests check these copies, and
# retrieval.py refuses every bundle if the release's schema files no longer match their hashes.
PHASE5_VERSION = 'phase5-structured-1.0.0'
PHASE5_DATABASE_SHA256 = 'f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8'
PHASE5_QUERY_SCHEMA_SHA256 = '3c1d109fca5fd80206c0c2f3b2640e015e4aa4d83b6993f623cac4aadc9c9313'
PHASE5_BUNDLE_SCHEMA_SHA256 = '912461e96fa69efebee2a87197e96e8b6b2b844a58a801a1186a20e7297201c5'
PHASE5_CITATION_VERSION = '1'
PHASE5_COMPLETE = 'COMPLETE WITHIN VERIFIED CONTRACT'
PHASE5_STATUSES = (PHASE5_COMPLETE, 'PARTIAL', 'UNAVAILABLE', 'UNSUPPORTED', 'INVALID SCOPE', 'UNVERIFIED PLAN')
# Statuses of a request the release did not evaluate (refused, integrity failure, failed independent validation).
PHASE5_NOT_EVALUATED = ('INVALID SCOPE', 'UNSUPPORTED', 'UNAVAILABLE', 'UNVERIFIED PLAN')
# StructuredRetriever.response attaches these to every bundle; a consumer must keep them.
PHASE5_LIMITATIONS = (
    'Completeness covers mandatory explicit obligations only, never safety-claim sufficiency',
    'Saved-index/recorded-label association is not sensor synchronization',
    'Metadata/geometry/counts do not establish support/contact/falling',
    'Historical binary identity and physical calibration remain unattested',
)
PHASE5_CHANNELS = {
    'raw.robot0_gripper_qpos': 'raw_observation/robot0_gripper_qpos/value',
    'raw.robot0_gripper_qvel': 'raw_observation/robot0_gripper_qvel/value',
    'raw.robot0_joint_pos': 'raw_observation/robot0_joint_pos/value',
    'raw.robot0_joint_vel': 'raw_observation/robot0_joint_vel/value',
    'raw.simulator_actuator_force': 'simulator/actuator_force/value',
    'simulator.ncon': 'simulator/ncon/value',
}
PHASE5_REGISTRY = {**PHASE5_CHANNELS,
                   'source_provenance': 'source_identity',
                   'execution_metadata': 'recorded_execution_metadata',
                   'geometry_identity': 'native_object_identity',
                   'main_table_identity': 'verified_symbolic_alias',
                   'recorded_time': 'recorded_clock_labels',
                   'action_metadata': 'policy_action_metadata',
                   'inference_metadata': 'inference_call_metadata',
                   'camera_references': 'saved_image_references',
                   'contact_references': 'recorded_contact_references'}
PHASE5_TEMPORAL = set(PHASE5_CHANNELS) | {'recorded_time', 'action_metadata', 'inference_metadata',
                                          'camera_references', 'contact_references'}

# --- criticism categories (Critic handoff, section 8) ---
CATEGORIES = {
    'C01': 'Structural argument defect',
    'C02': 'Invalid evidence reference',
    'C03': 'Evidence-scope mismatch',
    'C04': 'Missing object or temporal coverage',
    'C05': 'Unsupported physical inference',
    'C06': 'Unsupported safety conclusion',
    'C07': 'Contradiction with validated evidence',
    'C08': 'Incorrect applicability',
    'C09': 'Ignored uncertainty',
    'C10': 'Invalid generalization',
    'C11': 'Misuse of related executions',
    'C12': 'Unsupported guarantee or certification',
    'C13': 'Unresolved objection or assumption',
}
SEVERITIES = ('high', 'medium', 'low')

# Findings about input the team's own validators would reject (schemas, Graph.validate, Record.validate,
# the request contract, checker input) put the review in the 'validation' phase: the input is invalid,
# the LLM is not called and the report is a rejection, not a completed critique. The two exceptions are
# argument defects Graph.validate accepts. Everything else (conclusions, LLM) is the 'review' phase.
VALIDATION_PREFIXES = ('REQ-', 'SCHEMA-', 'CONFIG-', 'EV-', 'BUNDLE-', 'GSN-', 'CHK-', 'RET-')
REVIEW_EXCEPTIONS = {'GSN-UNSUPPORTED-GOAL', 'EV-UNUSABLE'}
REVIEW_STATUSES = ('completed', 'completed_llm_failed', 'rejected_invalid_input', 'internal_error')


def phase_of(check_id):
    if check_id.startswith(VALIDATION_PREFIXES) and check_id not in REVIEW_EXCEPTIONS:
        return 'validation'
    return 'review'

FINDING_SOURCES = ('deterministic', 'evidence_grounded', 'llm_proposed')


def finite_number(value):
    """A JSON number usable as one: int or float (not bool), finite, and within the range of a double.

    An integer too large for a double (e.g. 10**1000) is valid JSON and Python reads it, but math.isfinite
    raises OverflowError on it and other tools cannot represent it; the team's models.interval crashes on it.
    The Critic treats it as not a usable number (audit R2-04)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def canonical(value):
    """Same canonical JSON as evaluation/r1_v4/provenance.py."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def record_content_id(record):
    """Recompute a registry evidence ID: 'ev:' + sha256 of the record without its id."""
    body = {k: v for k, v in record.items() if k != 'id'}
    return 'ev:' + digest(body)


def execution_outcome(object_outcomes):
    """R1 v2 execution aggregation over per-object outcomes (precedence V > IC > U > N > NA)."""
    values = list(object_outcomes)
    if not values:
        return NOT_APPLICABLE  # empty scope; reported separately, never a pass
    for outcome in OUTCOME_PRECEDENCE:
        if outcome in values:
            return outcome
    return NOT_APPLICABLE
