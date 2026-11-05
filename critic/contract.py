"""Shared vocabulary for the Critic contract.

Graph and evidence vocabularies are copied from the existing
evaluation/r1_v4/evidence_registry_gsn schemas (GSN 1.0.0, registry record
1.0.0). Outcome names come from evaluation/r1_v4/contracts.py. Nothing here
redefines those formats; the tests check that these copies stay in sync.
"""
import hashlib
import json

REQUEST_SCHEMA_VERSION = 'critic-request/0.2.0'
REPORT_SCHEMA_VERSION = 'critic-report/0.2.0'

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
FINDING_SOURCES = ('deterministic', 'evidence_grounded', 'llm_proposed')


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
