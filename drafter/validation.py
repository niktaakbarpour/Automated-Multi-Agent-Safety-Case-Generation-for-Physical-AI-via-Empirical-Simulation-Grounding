"""Validate the fixture input contract without inference or input-directed I/O.

Contract validity, current source-byte verification, and physical sufficiency are
separate. This foundation accepts archived registry fixtures only.
"""
from pathlib import Path
import hashlib

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from evaluation.r1_v4.configuration import validate_configuration
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.evidence_registry_gsn.gsn import Graph, Node, Edge
from evaluation.r1_v4.evidence_registry_gsn.registry import dependency_issues
from evaluation.r1_v4.provenance import canonical, digest, strict_loads

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
REPOSITORY = 'https://github.com/niktaakbarpour/Automated-Multi-Agent-Safety-Case-Generation-for-Physical-AI-via-Empirical-Simulation-Grounding'
BASE_REVISION = '0cda4f32824d02c3c81a148db9998d88cde96b2c'
BASE_CONFIGURATION = 'requirements/r1_generalized_v2/EXAMPLE_CONFIGS/A_LIBERO_FIVE_OBJECTS.json'
BASE_EXPORT = 'evaluation/r1_v4/evidence_registry_gsn/demo/REGISTRY_EXPORT.json'
SOURCE_BLOBS = {BASE_CONFIGURATION: 'b7bac77ac3d926eb5759646acc38674b7c752cd0',
                BASE_EXPORT: 'f6fecbb8d63cee36b2a0ff1c04fe874ea3647f13'}
AUTHORITATIVE_SCHEMAS = {
    '../../requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json': 'requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json',
    '../../evaluation/r1_v4/evidence_registry_gsn/registry_record.schema.json': 'evaluation/r1_v4/evidence_registry_gsn/registry_record.schema.json',
    '../../evaluation/r1_v4/evidence_registry_gsn/gsn_graph.schema.json': 'evaluation/r1_v4/evidence_registry_gsn/gsn_graph.schema.json',
    'draft_argument.schema.json': 'drafter/schemas/draft_argument.schema.json',
}


class ContractError(ValueError):
    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__('; '.join(self.issues))


def read_json(path):
    return strict_loads(Path(path).read_text(encoding='utf-8'))


def schema_validator(name, fragment=None):
    """Resolve only shipped schemas; never follow a request-supplied URL/path."""
    schema = read_json(HERE / 'schemas' / name)
    resources = {relative: read_json(ROOT / path)
                 for relative, path in AUTHORITATIVE_SCHEMAS.items()}
    replacements = {relative: content['$id'] for relative, content in resources.items()}

    def bind(value):
        if isinstance(value, dict):
            result = {k: bind(v) for k, v in value.items()}
            ref = result.get('$ref')
            if ref and not ref.startswith('#'):
                path, separator, pointer = ref.partition('#')
                if path not in replacements:
                    raise ContractError(['unknown_schema_reference:' + ref])
                result['$ref'] = replacements[path] + (separator + pointer if separator else '')
            return result
        if isinstance(value, list):
            return [bind(v) for v in value]
        return value

    bound = bind(schema)
    registry = Registry()
    for content in resources.values():
        registry = registry.with_resource(content['$id'], Resource.from_contents(bind(content)))
    registry = registry.with_resource(bound['$id'], Resource.from_contents(bound))
    Draft202012Validator.check_schema(bound)
    selected = {'$ref': bound['$id'] + fragment} if fragment else bound
    return Draft202012Validator(selected, registry=registry)


def schema_issues(value, name, fragment=None):
    try:
        canonical(value)
    except (ValueError, TypeError) as error:
        return ['invalid_json:' + str(error)]
    return sorted('schema:' + '/'.join(map(str, e.absolute_path)) + ':' + e.message
                  for e in schema_validator(name, fragment).iter_errors(value))


def graph_eligible_ids(request):
    """Metadata eligibility only; this does not admit a physical witness."""
    target, scope = request['target_execution'], request['monitoring_scope']
    start, end = scope['interval']
    objects = request['requirement_configuration']['protected_objects']
    return sorted(record['id'] for record in request['evidence_package']['records']
                  if record['kind'] in ('raw_measurement', 'derived_measurement')
                  and record['object_id'] in objects
                  and record['execution_id'] == target['execution_id']
                  and record['domain'] == scope['domain'] and record['clock'] == scope['clock']
                  and start <= record['interval'][0] <= record['interval'][1] <= end
                  and record['validation_status'] not in ('invalid', 'missing', 'unsupported'))


def known_saved_frame_gaps(objects, records, eligible, window):
    """Missing metadata cells only, without claiming physical coverage."""
    gaps = []
    for object_id in objects:
        cursor = window[0]
        intervals = sorted(set(tuple(r.interval) for key, r in records.items()
                               if key in eligible and r.object_id == object_id))
        for left, right in intervals:
            if cursor < left:
                gaps.append((object_id, cursor, left - 1))
            cursor = max(cursor, right + 1)
        if cursor <= window[1]:
            gaps.append((object_id, cursor, window[1]))
    return sorted(gaps)


def validate_request(request):
    issues = schema_issues(request, 'draft_request.schema.json')
    if issues:
        raise ContractError(issues)
    config, target = request['requirement_configuration'], request['target_execution']
    scope, export = request['monitoring_scope'], request['evidence_package']
    issues.extend(validate_configuration(config))
    if digest(config) != request['requirement_configuration_sha256']:
        issues.append('configuration_digest_mismatch')
    if digest(export) != request['evidence_package_sha256']:
        issues.append('evidence_digest_mismatch')
    start, end = scope['interval']
    if start > end or (scope['domain'] == 'frame' and any(type(v) is not int or v < 0 for v in (start, end))):
        issues.append('invalid_monitoring_interval')
    if config['execution_id'] != target['execution_id'] or config['task_id'] != target['task_id']:
        issues.append('configuration_execution_or_task_mismatch')
    if config['benchmark']['id'] != target['benchmark'] or config['benchmark']['policy_checkpoint'] != target['model_checkpoint']:
        issues.append('configuration_benchmark_or_checkpoint_mismatch')
    if target['variant_id'] is not None:
        issues.append('archived_variant_identity_unavailable')
    if (config['monitoring_interval']['axis'], scope['domain'], scope['clock']) != ('saved_frame', 'frame', 'saved_frame_index'):
        issues.append('unsupported_fixture_clock_or_axis')
    bounds = config['monitoring_interval']
    if bounds['start']['kind'] != 'explicit_index' or bounds['end']['kind'] != 'explicit_index' or [bounds['start']['value'], bounds['end']['value']] != scope['interval']:
        issues.append('configuration_boundary_mismatch')

    # Reproduce the new illustrative configuration from the unchanged shipped one.
    provenance = request['input_provenance']
    if provenance['repository'] != REPOSITORY or provenance['revision'] != BASE_REVISION:
        issues.append('unsupported_source_revision')
    derivation = provenance['configuration_derivation']
    if derivation['base_path'] != BASE_CONFIGURATION:
        issues.append('unsupported_configuration_source')
    else:
        base = read_json(ROOT / BASE_CONFIGURATION)
        if digest(base) != derivation['base_canonical_sha256']:
            issues.append('configuration_base_digest_mismatch')
        expected_changes = {
            '/benchmark/id': target['benchmark'],
            '/benchmark/policy_checkpoint': target['model_checkpoint'],
            '/execution_id': target['execution_id'],
            '/monitoring_interval/end/kind': 'explicit_index',
            '/monitoring_interval/end/value': end,
        }
        seen = set()
        for change in derivation['changes']:
            pointer = change['pointer']
            if pointer not in expected_changes or pointer in seen:
                issues.append('unsupported_or_duplicate_configuration_change:' + pointer)
                continue
            seen.add(pointer)
            parent = base
            parts = pointer.lstrip('/').split('/')
            for part in parts[:-1]:
                parent = parent[part]
            if parent[parts[-1]] != change['before'] or change['after'] != expected_changes[pointer]:
                issues.append('configuration_change_binding:' + pointer)
            parent[parts[-1]] = change['after']
        if seen != set(expected_changes) or base != config:
            issues.append('configuration_derivation_mismatch')

    # Immutable metadata lineage, never a claim that /disk source bytes were replayed.
    expected_sources = {BASE_CONFIGURATION, BASE_EXPORT}
    source_paths = [s['path'] for s in provenance['source_artifacts']]
    if set(source_paths) != expected_sources or len(source_paths) != len(expected_sources):
        issues.append('source_artifact_inventory_mismatch')
    for artifact in provenance['source_artifacts']:
        if artifact['path'] not in expected_sources:
            continue
        content = (ROOT / artifact['path']).read_bytes()
        sha1 = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if sha1 != SOURCE_BLOBS[artifact['path']]:
            issues.append('pinned_source_changed:' + artifact['path'])
        if (sha1, hashlib.sha256(content).hexdigest(), digest(strict_loads(content.decode()))) != (artifact['git_blob_sha1'], artifact['bytes_sha256'], artifact['canonical_sha256']):
            issues.append('source_artifact_binding:' + artifact['path'])
    if export != read_json(ROOT / BASE_EXPORT):
        issues.append('archived_export_changed')
    records = {}
    for index, value in enumerate(export['records']):
        try:
            record = Record.parse(value)
            if record.id in records:
                issues.append('duplicate_record:' + record.id)
            records[record.id] = record
            if (record.execution_id, record.benchmark, record.task_id, record.model_checkpoint) != (target['execution_id'], target['benchmark'], target['task_id'], target['model_checkpoint']):
                issues.append('record_target_scope:' + record.id)
            if record.object_id not in config['protected_objects']:
                issues.append('record_object_scope:' + record.id)
        except (ValueError, TypeError, KeyError) as error:
            issues.append('record:' + str(index) + ':' + str(error))
    if records:
        for key, errors in dependency_issues(records).items():
            issues.extend('record_dependency:' + key + ':' + error for error in errors)
    eligible = graph_eligible_ids(request)
    ids = set(records)
    handling = request['evidence_handling']
    if sorted(handling['graph_eligible_evidence_ids']) != eligible or set(handling['context_only_evidence_ids']) != ids - set(eligible):
        issues.append('evidence_partition_mismatch')
    retrieval = request['retrieval_context']
    if retrieval['requested_objects'] != config['protected_objects'] or retrieval['requested_interval'] != scope['interval']:
        issues.append('retrieval_scope_mismatch')
    observed = {r.object_id for key, r in records.items() if key in eligible}
    missing = set(config['protected_objects']) - observed
    if set(retrieval['missing_objects']) != missing:
        issues.append('missing_object_inventory_mismatch')
    supplied_gaps = []
    for gap in retrieval['gaps']:
        if gap['object_id'] not in config['protected_objects'] or not start <= gap['interval'][0] <= gap['interval'][1] <= end:
            issues.append('gap_scope_mismatch')
        if any(type(value) is not int for value in gap['interval']):
            issues.append('saved_frame_gap_requires_integer_endpoints')
        supplied_gaps.append((gap['object_id'], *gap['interval']))
    if sorted(supplied_gaps) != known_saved_frame_gaps(config['protected_objects'], records, set(eligible), scope['interval']):
        issues.append('known_gap_inventory_mismatch')
    if issues:
        raise ContractError(sorted(set(issues)))
    return {'contract_status': 'valid_fixture', 'configuration_schema': 'valid',
            'registry_metadata_contract': 'valid', 'records': len(records),
            'graph_eligible_records': len(eligible), 'source_replay': 'not_performed',
            'physical_sufficiency': 'not_evaluated', 'empirical_admission_enabled': False,
            'safety_claim_verified': False, 'model_called': False}


def validate_argument(argument, request):
    """Check a result's contract; this neither generates nor critiques prose."""
    validate_request(request)
    issues = schema_issues(argument, 'draft_argument.schema.json')
    if issues:
        raise ContractError(issues)
    for field, expected in (
        ('request_id', request['request_id']), ('request_sha256', digest(request)),
        ('requirement_configuration_sha256', request['requirement_configuration_sha256']),
        ('evidence_package_sha256', request['evidence_package_sha256']),
    ):
        if argument[field] != expected:
            issues.append('argument_input_binding:' + field)
    if argument['generation_status'] != 'accepted':
        if issues:
            raise ContractError(issues)
        return {'contract_status': 'valid_failure_contract', 'physical_sufficiency': 'not_evaluated',
                'safety_claim_verified': False, 'model_called': False}
    if issues:
        raise ContractError(issues)
    validate_argument_bundle(argument['argument_bundle'], request)
    return {'contract_status': 'valid_output_contract', 'physical_sufficiency': 'not_evaluated',
            'safety_claim_verified': False, 'model_called': False}


def validate_argument_bundle(bundle, request):
    """Shared graph checks for live drafts and explicitly labelled mock demos."""
    validate_request(request)
    issues = schema_issues(bundle, 'draft_argument.schema.json', '#/$defs/argument_bundle')
    if issues:
        raise ContractError(issues)
    config = request['requirement_configuration']
    roster, scope = config['protected_objects'], request['monitoring_scope']
    if bundle['execution_id'] != request['target_execution']['execution_id'] or bundle['protected_objects'] != roster:
        issues.append('argument_execution_or_roster_mismatch')
    wrapped_objects = [item['object_id'] for item in bundle['graphs']]
    if len(wrapped_objects) != len(set(wrapped_objects)) or set(wrapped_objects) != set(roster):
        issues.append('argument_graph_roster_mismatch')
    if set(bundle['execution_conclusion']['object_outcomes']) != set(roster):
        issues.append('argument_outcome_roster_mismatch')
    records = tuple(Record.parse(value) for value in request['evidence_package']['records'])

    class ExportView:
        def records(self):
            return records

    eligible = set(request['evidence_handling']['graph_eligible_evidence_ids'])
    for item in bundle['graphs']:
        object_id, value = item['object_id'], item['graph']
        try:
            graph = Graph(tuple(Node(**n) for n in value['nodes']),
                          tuple(Edge(**e) for e in value['edges']), value['schema_version'])
            graph.validate(ExportView())
            if not any(n.physical_claim and n.type in ('goal', 'unresolved_claim')
                       and n.validation_status == 'unresolved' for n in graph.nodes):
                issues.append('missing_unresolved_physical_claim:' + object_id)
            for node in graph.nodes:
                expected_scope = (config['requirement_id'], config['requirement_version'],
                                  request['target_execution']['execution_id'], object_id)
                if tuple(node.scope.get(k) for k in ('requirement_id', 'requirement_version', 'execution_id', 'object_id')) != expected_scope:
                    issues.append('argument_node_scope:' + node.id)
                if 'interval' not in node.scope or node.scope.get('domain') != scope['domain'] or node.scope.get('clock') != scope['clock']:
                    issues.append('argument_node_temporal_scope:' + node.id)
                elif not scope['interval'][0] <= node.scope['interval'][0] <= node.scope['interval'][1] <= scope['interval'][1]:
                    issues.append('argument_node_outside_window:' + node.id)
                elif scope['domain'] == 'frame' and any(type(v) is not int or v < 0 for v in node.scope['interval']):
                    issues.append('argument_frame_indices_require_integers:' + node.id)
                if node.type == 'solution' and node.evidence_id not in eligible:
                    issues.append('argument_ineligible_solution:' + node.id)
        except (ValueError, TypeError, KeyError) as error:
            issues.append('graph:' + object_id + ':' + str(error))
    if issues:
        raise ContractError(sorted(set(issues)))
    return {'contract_status': 'valid_argument_bundle', 'physical_sufficiency': 'not_evaluated',
            'safety_claim_verified': False, 'model_called': False}
