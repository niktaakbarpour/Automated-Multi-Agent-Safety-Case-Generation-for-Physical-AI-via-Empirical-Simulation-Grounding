"""Deterministic checks that run before the LLM.

Every check returns findings instead of raising, so one review lists every
problem. The graph rules mirror evaluation/r1_v4/evidence_registry_gsn/gsn.py
(Graph.validate); tests/test_critic.py confirms that every graph the original
validator rejects is also flagged here.

No check infers physical events. Checks only compare IDs, scopes, intervals,
statuses and declared outcomes against the supplied package.
"""
import math
import re
from pathlib import PurePosixPath

from . import assessments as A
from . import contract as K
from . import schema as SCHEMA

GSN_REF = 'evaluation/r1_v4/evidence_registry_gsn/gsn.py:Graph.validate'
SPEC_REF = 'requirements/r1_generalized_v2/FORMAL_SEMANTICS.md'
AGGREGATION_REF = SPEC_REF + '#execution-aggregation'
OUTCOME_REF = SPEC_REF + '#coverage-and-object-outcome'
VALIDITY_REF = SPEC_REF + '#domain-and-evidence-logic'
HASH_REF = 'evaluation/r1_v4/evidence_registry_gsn/models.py:Record.id'
RECORD_REF = 'evaluation/r1_v4/evidence_registry_gsn/models.py:Record.validate'

# Which node types an edge of each type may connect (source types, target types).
EDGE_RULES = {
    'supported_by': ({'goal', 'strategy', 'unresolved_claim'}, {'strategy', 'goal', 'solution', 'unresolved_claim'}),
    'in_context_of': ({'goal', 'strategy', 'unresolved_claim'}, {'context', 'assumption', 'justification'}),
    'challenged_by': ({'goal', 'strategy', 'unresolved_claim'}, {'defeater'}),
}


def finding(check_id, category, explanation, suggested_action, *, severity='high', blocking=None,
            object_id=None, node_id=None, evidence_ids=(), requirement_refs=(), source='deterministic',
            additional_evidence_needed=False, human_review_required=False, evidence_request=None):
    """Build one criticism (it gets its CRIT-nnn id later, in critic.review)."""
    f = {
        'check_id': check_id,
        'phase': K.phase_of(check_id),
        'category': category,
        'category_name': K.CATEGORIES[category],
        'severity': severity,
        'blocking': severity == 'high' if blocking is None else blocking,
        'object_id': object_id,
        'node_id': node_id,
        'explanation': explanation,
        'evidence_ids': list(evidence_ids),
        'requirement_refs': list(requirement_refs),
        'finding_source': source,
        'suggested_action': suggested_action,
        'additional_evidence_needed': additional_evidence_needed,
        'human_review_required': human_review_required,
    }
    if evidence_request is not None:
        f['_evidence_request'] = evidence_request  # moved to report.evidence_requests by critic.review
    return f


def _interval(value):
    """Return (start, end) for a valid finite interval, else None."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in value):
        return None
    return tuple(value) if value[0] <= value[1] else None


def _contains(outer, inner):
    return outer[0] <= inner[0] and inner[1] <= outer[1]


def _overlaps(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


def _in(value, collection):
    """Membership test that is safe for malformed input (lists or objects where text is expected)."""
    return isinstance(value, str) and value in collection


def _scope(node):
    return node.get('scope') if isinstance(node.get('scope'), dict) else {}


def _list(value):
    return value if isinstance(value, list) else []


def _interval_or_none(value):
    """An interval safe to copy into an evidence request."""
    checked = _interval(value)
    return list(checked) if checked else None


# ------------------------------------------------------------------ request shape

def check_request_shape(req):
    """Check the top-level structure. Returns (findings, fatal); fatal means nothing else can run."""
    def fatal(check_id, explanation, action):
        return [finding(check_id, 'C01', explanation, action)], True

    if not isinstance(req, dict):
        return fatal('REQ-SHAPE', 'The review request is not a JSON object.', 'Send a critic-request/0.1.0 object.')
    sections = {'evaluation_context': dict, 'argument_bundle': dict, 'evidence_package': dict,
                'checker_assessments': list, 'retrieval_context': dict}
    wrong = [k for k in ('schema_version', 'request_id', *sections) if k not in req]
    wrong += [k for k, kind in sections.items() if k in req and not isinstance(req[k], kind)]
    if wrong:
        return fatal('REQ-SHAPE', f'Review request sections missing or of the wrong type: {", ".join(wrong)}.',
                     'Supply a complete critic-request/0.1.0 package.')
    if req['schema_version'] != K.REQUEST_SCHEMA_VERSION:
        return fatal('REQ-VERSION', f"Unsupported request schema {req['schema_version']!r}; "
                     f'expected {K.REQUEST_SCHEMA_VERSION}.', 'Regenerate the request with the current contract.')

    ctx = req['evaluation_context']
    missing = [k for k in ('requirement_id', 'requirement_version', 'execution_id',
                           'protected_objects', 'monitored_interval') if k not in ctx]
    if missing:
        return fatal('REQ-CONTEXT', f'Evaluation context is missing {", ".join(missing)}.',
                     'Fill section A from the R1 v2 configuration.')
    objects = ctx['protected_objects']
    if not isinstance(objects, list) or not all(isinstance(o, str) and o for o in objects):
        return fatal('REQ-OBJECTS', 'protected_objects must be a list of object IDs.',
                     'Copy protected_objects from the R1 configuration.')
    monitored = ctx['monitored_interval']
    if not isinstance(monitored, dict) or _interval(monitored.get('interval')) is None:
        return fatal('REQ-INTERVAL', 'Monitored interval is not a valid [start, end] pair.',
                     'Take the monitored interval from the R1 configuration.')

    bundle = req['argument_bundle']
    graphs = bundle.get('graphs')
    if not isinstance(graphs, list) or not all(isinstance(g, dict) and isinstance(g.get('object_id'), str)
                                                for g in graphs):
        return fatal('REQ-GRAPHS', 'argument_bundle.graphs must be a list of {object_id, graph} objects.',
                     'Wrap each object-level GSN graph as {object_id, graph}.')
    conclusion = bundle.get('execution_conclusion')
    if not isinstance(conclusion, dict) or not isinstance(conclusion.get('object_outcomes'), dict):
        return fatal('REQ-CONCLUSION', 'argument_bundle.execution_conclusion with an object_outcomes map is required.',
                     'State an outcome for every protected object, even if it is insufficient_information.')
    records = req['evidence_package'].get('records')
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        return fatal('REQ-EVIDENCE', 'evidence_package.records must be a list of registry records.',
                     'Export the selected records from the evidence registry.')
    if not all(isinstance(a, dict) for a in req['checker_assessments']):
        return fatal('REQ-CHECKER', 'checker_assessments must be a list of objects.',
                     'Pass checker outputs unchanged, or an empty list if none are available.')
    return [], False


# ------------------------------------------------------------------ evidence records

def index_records(req):
    """Return ({evidence_id: record}, findings about broken records).

    Each record is checked against registry_record.schema.json and the rules of models.Record.validate.
    """
    out, records = [], {}
    ctx = req['evaluation_context']
    fixture = req.get('test_fixture') is True
    for i, rec in enumerate(req['evidence_package']['records']):
        rid = rec.get('id')
        missing = [k for k in K.RECORD_REQUIRED if k not in rec]
        if missing or not isinstance(rid, str):
            out.append(finding('EV-SHAPE', 'C02', f'Evidence record #{i} ({rid}) is missing fields: '
                               f'{", ".join(missing) or "id"}.', 'Export the record unchanged from the registry.',
                               evidence_ids=[rid] if isinstance(rid, str) else []))
            continue
        if rid in records:
            out.append(finding('EV-DUP', 'C02', f'Evidence ID {rid} appears twice in the package.',
                               'Export each registry record once.', evidence_ids=[rid]))
            continue
        records[rid] = rec
        problems = SCHEMA.errors(rec, SCHEMA.load('registry_record'), limit=5)
        if problems:
            out.append(finding('SCHEMA-RECORD', 'C02', f'Evidence record {rid} does not match the registry record '
                               f'schema: {"; ".join(problems)}.', 'Export the record unchanged from the registry.',
                               evidence_ids=[rid], requirement_refs=[str(SCHEMA.SCHEMAS['registry_record'].name)]))
        try:
            hash_ok = K.record_content_id(rec) == rid
        except (TypeError, ValueError):  # e.g. NaN, which canonical JSON rejects
            hash_ok = False
        if not hash_ok:
            out.append(finding('EV-HASH', 'C02', f'Evidence record {rid} does not match its content hash: it was '
                               'changed after export, or the ID is not a registry ID.',
                               'Re-export the record from the registry; never edit records.',
                               evidence_ids=[rid], requirement_refs=[HASH_REF]))
        if (rec['schema_version'] != K.RECORD_SCHEMA_VERSION or rec['requirement_id'] != ctx['requirement_id']
                or rec['requirement_version'] != ctx['requirement_version']):
            out.append(finding('EV-VERSION', 'C02', f"Evidence record {rid} uses record schema {rec['schema_version']} "
                               f"and requirement {rec['requirement_id']} {rec['requirement_version']}, which do not "
                               'match this review.', 'Use records produced for the same requirement and registry '
                               'versions.', evidence_ids=[rid]))
        rule_problems = record_rule_problems(rec, fixture)
        if rule_problems:
            out.append(finding('EV-RECORD', 'C02', f'Evidence record {rid} breaks the registry record rules: '
                               f'{"; ".join(rule_problems)}.', 'Export only records that models.Record.validate '
                               'accepts.', evidence_ids=[rid], requirement_refs=[RECORD_REF]))
        if not fixture and _is_synthetic_record(rec):
            out.append(finding('EV-SYNTHETIC', 'C02', f'Evidence record {rid} is synthetic test data, but the request '
                               'is not marked test_fixture.', 'Never mix synthetic records into a real review; mark '
                               'the request test_fixture or remove the record.', evidence_ids=[rid]))
    return records, out


APPROVED_SOURCE_ROOT = PurePosixPath('/disk/1/data/niktakbr')
SYNTHETIC_SOURCE_ROOT = PurePosixPath('/synthetic')
RECORD_KINDS = {'raw_measurement', 'derived_measurement', 'ai_reference_judgment', 'human_reference_judgment',
                'checker_assessment', 'document'}
RECORD_STATUSES = {'verified_measurement', 'verified_source', 'provisional', 'invalid', 'missing', 'unsupported'}
CAPABILITY_VALUES = {'VERIFIED', 'CONDITIONALLY_SUPPORTED', 'BLOCKED_ON_EVIDENCE', 'UNSUPPORTED'}
MEASUREMENT_TYPES = {'object_pose', 'native_geometry', 'contact', 'camera_reference', 'robot_state', 'timestamp',
                     'recorded_state'}


def _is_synthetic_record(rec):
    path = rec.get('source_path')
    provenance = rec.get('provenance') if isinstance(rec.get('provenance'), dict) else {}
    return provenance.get('synthetic') is True or (
        isinstance(path, str) and PurePosixPath(path).is_relative_to(SYNTHETIC_SOURCE_ROOT))


def _record_interval(value):
    """models.interval: a finite [start, end] pair of int/float (not bool) with start <= end."""
    if not isinstance(value, list) or len(value) != 2:
        return None
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in value) or value[0] > value[1]:
        return None
    return tuple(value)


def record_rule_problems(rec, fixture):
    """The checks of evaluation/r1_v4/evidence_registry_gsn/models.py:Record.validate, without filesystem access.

    Differences: the version rule is reported as EV-VERSION, and a test-fixture request may also use
    /synthetic/ source paths.
    (Record.validate also refuses symlinked sources; that needs the filesystem and is not checked here.)
    """
    out = []  # the version rule of Record.validate is reported separately as EV-VERSION
    kind, status = rec.get('kind'), rec.get('validation_status')
    if not _in(kind, RECORD_KINDS) or not _in(status, RECORD_STATUSES):
        out.append('record kind/status')
    for key in ('execution_id', 'object_id', 'selector', 'measurement_type', 'clock', 'coordinate_frame',
                'model_checkpoint', 'benchmark', 'task_id', 'producer'):
        if not isinstance(rec.get(key), str) or not rec[key]:
            out.append('missing ' + key)
    if rec.get('domain') not in ('frame', 'time'):
        out.append('domain')
    if not isinstance(rec.get('original'), bool) or (rec['original'] and kind not in ('raw_measurement', 'document')):
        out.append('provenance origin')
    path = rec.get('source_path')
    if not isinstance(path, str) or not path.startswith('/'):
        out.append('source binding')
    else:
        source = PurePosixPath(path)
        allowed = source.is_relative_to(APPROVED_SOURCE_ROOT) or (
            fixture and source.is_relative_to(SYNTHETIC_SOURCE_ROOT))
        if not allowed or '..' in source.parts or any('issta' in part.lower() for part in source.parts):
            out.append('source outside approved research scope')
    if not isinstance(rec.get('source_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', rec['source_sha256']):
        out.append('source binding')
    span = _record_interval(rec.get('interval'))
    if span is None:
        out.append('invalid interval')
    elif rec.get('domain') == 'frame' and any(type(x) is not int or x < 0 for x in span):
        out.append('frame index')
    gaps = rec.get('missing_intervals')
    for gap in gaps if isinstance(gaps, list) else [None]:
        g = _record_interval(gap)
        if g is None:
            out.append('invalid interval')
        elif span is not None and (g[0] < span[0] or g[1] > span[1]):
            out.append('gap outside scope')
    for key in ('dependencies', 'conflicts', 'uncertainty', 'limitations'):
        seq = rec.get(key)
        if not isinstance(seq, list) or any(not isinstance(x, str) or not x for x in seq) \
                or len(set(x for x in seq if isinstance(x, str))) != len(seq):
            out.append('invalid/duplicate list')
    capability = rec.get('capability')
    if not isinstance(capability, dict) or not capability or any(
            not isinstance(k, str) or not k or not _in(v, CAPABILITY_VALUES) for k, v in capability.items()):
        out.append('capability')
    if status == 'verified_measurement' and kind not in ('raw_measurement', 'derived_measurement'):
        out.append('judgment is not measurement')
    if kind in ('raw_measurement', 'derived_measurement') and not _in(rec.get('measurement_type'), MEASUREMENT_TYPES):
        out.append('physical events are not measurement types')
    provenance = rec.get('provenance')
    if not isinstance(provenance, dict) or provenance.get('physical_truth') not in (None, 'U'):
        out.append('unsupported physical truth')
    return sorted(set(out))


# ------------------------------------------------------------------ R1 configuration

CONFIG_REF = 'evaluation/r1_v4/configuration.py:validate_configuration'


def check_configuration(req):
    """The authoritative R1 configuration in the evaluation context, and the context's binding to it.

    The configuration is checked like evaluation/r1_v4/configuration.py:validate_configuration (schema and
    semantic rules). Protected objects, surfaces and the monitored interval in the context must be exactly
    the configuration's. A configuration may be a template (execution_id or task_id null); a value it does
    set must match, and so must its benchmark and (if set) policy checkpoint. Boundaries that are not explicit
    indices need boundary_provenance in the request.
    """
    ctx = req['evaluation_context']
    config = ctx.get('r1_configuration')

    def bad(check_id, explanation, action):
        return finding(check_id, 'C03' if check_id != 'CONFIG-SCHEMA' else 'C01', explanation, action,
                       requirement_refs=[CONFIG_REF])

    if not isinstance(config, dict):
        return [bad('CONFIG-SCHEMA', 'The evaluation context has no R1 configuration object.',
                    'Put the full R1 v2 configuration under evaluation_context.r1_configuration.')]
    problems = SCHEMA.errors(config, SCHEMA.load('r1_configuration'), limit=5)
    if problems:
        return [bad('CONFIG-SCHEMA', 'The R1 configuration does not match R1_V2_CONFIG_SCHEMA: '
                    f'{"; ".join(problems)}.',
                    'Supply a configuration that validate_configuration accepts.')]
    try:
        return _check_valid_configuration(ctx, config, bad)
    except (KeyError, TypeError, AttributeError, IndexError) as exc:  # the schema should make this unreachable
        return [bad('CONFIG-RULES', f'The R1 configuration passed its schema but could not be read ({exc!r}).',
                    'Supply a configuration that validate_configuration accepts.')]


def _check_valid_configuration(ctx, config, bad):
    out = []
    try:
        digest_ok = ctx.get('r1_configuration_sha256') == K.digest(config)
    except (TypeError, ValueError):
        digest_ok = False
    if not digest_ok:
        out.append(bad('CONFIG-HASH', 'r1_configuration_sha256 is not the content hash of the supplied '
                       'configuration.', 'Recompute it (sha256 of the canonical JSON), or supply the right file.'))
    rules = config_rule_problems(config)
    if rules:
        out.append(bad('CONFIG-RULES', f'The R1 configuration breaks the configuration rules: {", ".join(rules)}.',
                       'Supply a configuration that validate_configuration accepts.'))

    mismatched = [f'{key} {config[key]!r}' for key in ('execution_id', 'task_id')
                  if config[key] is not None and config[key] != ctx.get(key)]
    # requirement_id and requirement_version are fixed (R1, 2.0.0) by both schemas, so they cannot differ here.
    if config['benchmark']['id'] != ctx.get('benchmark'):
        mismatched.append(f"benchmark {config['benchmark']['id']!r}")
    checkpoint = config['benchmark'].get('policy_checkpoint')
    if checkpoint is not None and checkpoint != ctx.get('model_checkpoint'):
        mismatched.append(f'policy checkpoint {checkpoint!r}')
    if mismatched:
        out.append(bad('CONFIG-SCOPE', f'The R1 configuration is for {", ".join(mismatched)}, which does not match '
                       'the evaluation context.', 'Review the execution with the configuration that applies to it.'))
    objects = ctx.get('protected_objects')
    if not isinstance(objects, list) or sorted(map(str, objects)) != sorted(config['protected_objects']):
        out.append(bad('CONFIG-OBJECTS', f"The context lists protected objects {objects}, but the R1 configuration "
                       f"lists {config['protected_objects']}.", 'Copy protected_objects from the configuration '
                       'unchanged; a shorter list is an unauthorized reduction.'))
    surfaces = ctx.get('support_surfaces')
    configured = sorted(s['id'] for s in config['support_surfaces'])
    if not isinstance(surfaces, list) or sorted(map(str, surfaces)) != configured:
        out.append(bad('CONFIG-SURFACES', f'The context lists support surfaces {surfaces}, but the R1 configuration '
                       f'lists {configured}.', 'Copy the support surface IDs from the configuration unchanged.'))
    out.extend(bad('CONFIG-INTERVAL', text, 'Take the monitored interval from the configuration, with '
                   'boundary_provenance for every boundary that is not an explicit index.')
               for text in _interval_problems(config['monitoring_interval'], ctx.get('monitored_interval')))
    return out


def _interval_problems(mi, monitored):
    monitored = monitored if isinstance(monitored, dict) else {}
    axis = mi['axis']
    if axis not in K.AXIS_TO_CLOCK:
        return [f'The configuration monitors on the {axis} axis, which has no agreed clock in the GSN graphs yet.']
    out = []
    domain, clock = K.AXIS_TO_CLOCK[axis]
    if (monitored.get('domain'), monitored.get('clock')) != (domain, clock):
        out.append(f"The monitored interval is on {monitored.get('domain')}/{monitored.get('clock')}, but the "
                   f'configuration axis {axis} is {domain}/{clock}.')
    span = _interval(monitored.get('interval'))
    provenance = monitored.get('boundary_provenance') if isinstance(monitored.get('boundary_provenance'), dict) \
        else {}
    for i, side in enumerate(('start', 'end')):
        # a malformed entry is reported by SCHEMA-REQUEST; here it counts as no provenance
        boundary = mi[side]
        given = provenance.get(side) if isinstance(provenance.get(side), dict) else None
        if boundary['kind'].startswith('explicit_'):
            value, how = boundary['value'], 'the configuration'
        elif given is not None:
            value, how = given.get('resolved_value'), f"boundary_provenance ({boundary['kind']})"
        else:
            out.append(f"The {side} boundary is {boundary['kind']}, and the request gives no boundary_provenance "
                       'saying which frame it resolved to and from which recorded source.')
            continue
        if given is not None and given.get('resolved_value') != value:
            out.append(f"boundary_provenance gives {side} {given.get('resolved_value')!r}, but the configuration "
                       f'fixes it at {value!r}.')
        if span is None or value != span[i] or isinstance(value, bool):
            out.append(f"The monitored interval {monitored.get('interval')} does not start/end where {how} puts the "
                       f'{side}: {value!r}.')
    return out


def config_rule_problems(config):
    """The semantic rules of validate_configuration (after its schema check), with the same names."""
    out = []
    objects = config['protected_objects']
    surfaces = [s['id'] for s in config['support_surfaces']]
    mapping = config['object_surface_mapping']
    if len(set(surfaces)) != len(surfaces):
        out.append('duplicate_surface_id')
    if set(objects) & set(surfaces):
        out.append('object_surface_role_collision')
    if set(objects) != set(mapping):
        out.append('object_mapping_keys_mismatch')
    if any(s not in surfaces for ss in mapping.values() for s in ss):
        out.append('dangling_surface_id')
    mi = config['monitoring_interval']
    a, b = mi['start'], mi['end']
    expected = 'explicit_index' if mi['axis'] == 'saved_frame' else 'explicit_time'
    if a['kind'] == 'terminal_recorded_snapshot' or b['kind'] == 'recorded_first_policy_boundary':
        out.append('invalid_anchor_role')
    if any(x['kind'].startswith('explicit_') and x['kind'] != expected for x in (a, b)):
        out.append('axis_boundary_mismatch')
    if a['value'] is not None and b['value'] is not None and a['value'] > b['value']:
        out.append('reversed_interval')
    m = config['assessment_manifest']
    for part, key, value in (('requirement', 'id', config['requirement_id']),
                             ('requirement', 'version', config['requirement_version']),
                             ('configuration_schema', 'id', K.CONFIG_SCHEMA_ID),
                             ('configuration_schema', 'version', '2.0.1'),
                             ('adapter', 'id', config['benchmark']['adapter_id']),
                             ('adapter', 'version', config['benchmark']['adapter_version'])):
        if m[part][key] != value:
            out.append('manifest_mismatch:' + part + '.' + key)
    if m['source_model_bindings'] != config['source_bindings']:
        out.append('manifest_source_mismatch')
    if m['requested_domain']['projection'] != config['temporal_alignment']['domain']:
        out.append('manifest_projection_mismatch')
    refs = [x['artifact_ref'] for x in config['source_bindings']]
    if len(set(refs)) != len(refs):
        out.append('duplicate_source_binding')
    support = config['initial_support_rules']
    if support['profile'] == 'legacy_v3_static_stencil' and support['boundary_context_offsets'] != [-1, 0, 1]:
        out.append('legacy_stencil_drift')
    return sorted(out)


# ------------------------------------------------------------------ bundle coverage

def check_bundle(req):
    """Execution identity and per-object coverage of the bundle."""
    out = []
    ctx, bundle = req['evaluation_context'], req['argument_bundle']
    configured = ctx['protected_objects']
    if bundle.get('execution_id') != ctx['execution_id']:
        out.append(finding('BUNDLE-EXEC', 'C03', f"Argument bundle is for execution {bundle.get('execution_id')!r}, "
                           f"but the review is for {ctx['execution_id']!r}.",
                           'Draft the argument for the execution under review.'))
    listed = bundle.get('protected_objects')
    if not isinstance(listed, list) or sorted(map(str, listed)) != sorted(configured):
        out.append(finding('BUNDLE-OBJLIST', 'C04', f'Bundle lists protected objects {listed}, but the R1 '
                           f'configuration lists {configured}.',
                           'Copy the protected-object list from the R1 configuration unchanged.',
                           requirement_refs=['R1 v2 configuration: protected_objects']))
    seen = set()
    for item in bundle['graphs']:
        oid = item.get('object_id')
        if oid in seen:
            out.append(finding('BUNDLE-DUPGRAPH', 'C01', f'Object {oid} has more than one graph in the bundle.',
                               'Provide exactly one graph per protected object.', object_id=oid))
        seen.add(oid)
        if oid not in configured:
            out.append(finding('BUNDLE-EXTRA', 'C03', f'Bundle contains a graph for {oid}, which is not a '
                               'configured protected object.',
                               'Remove it, or fix the configuration; do not argue about unconfigured objects.',
                               object_id=oid))
    for oid in configured:
        if oid not in seen:
            out.append(finding('BUNDLE-MISSING', 'C04', f'No argument graph for configured protected object {oid}. '
                               'Objects that are non-applicable or unknown must still be included.',
                               f'Add an object-level graph and an outcome for {oid}; if its status is unknown, '
                               'keep its goal unresolved and its outcome insufficient_information.',
                               object_id=oid, additional_evidence_needed=True,
                               requirement_refs=['R1 v2 configuration: protected_objects', AGGREGATION_REF],
                               evidence_request={'object_id': oid, 'measurement_type': None, 'interval': None,
                                                 'reason': 'No argument or evidence was supplied for this object.'}))
    return out


# ------------------------------------------------------------------ one object graph

def check_graph(req, item, records):
    """Every Graph.validate rule for one object-level graph, collected instead of raised."""
    oid, g = item.get('object_id'), item.get('graph')
    if (not isinstance(g, dict) or not isinstance(g.get('nodes'), list) or not isinstance(g.get('edges'), list)
            or not all(isinstance(x, dict) for x in g['nodes'] + g['edges'])):
        return [finding('GSN-SHAPE', 'C01', f'Graph for {oid} is not a GSN object with lists of node and edge '
                        'objects.', 'Emit a urn:trustworthy:gsn:1.0.0 graph.', object_id=oid,
                        requirement_refs=[GSN_REF])]
    out = []

    def add(check_id, category, explanation, action, **kw):
        out.append(finding(check_id, category, explanation, action, object_id=oid,
                           requirement_refs=kw.pop('requirement_refs', [GSN_REF]), **kw))

    problems = SCHEMA.errors(g, SCHEMA.load('gsn_graph'), limit=5)
    if problems:
        add('SCHEMA-GRAPH', 'C01', f'Graph for {oid} does not match the GSN 1.0.0 schema: {"; ".join(problems)}.',
            'Emit a graph that validates against gsn_graph.schema.json.',
            requirement_refs=[str(SCHEMA.SCHEMAS['gsn_graph'].name)])
    if g.get('schema_version') != K.GSN_SCHEMA_VERSION:
        add('GSN-VERSION', 'C01', f'Graph for {oid} has schema_version {g.get("schema_version")!r}; expected 1.0.0.',
            'Use the existing GSN 1.0.0 schema.')
    if g.get('empirical_admission_enabled') is not False:
        add('GSN-ADMISSION', 'C01', f'Graph for {oid} does not set empirical_admission_enabled to false; empirical '
            'admission is disabled in this phase.', 'Set empirical_admission_enabled to false.')

    nodes = {}
    for n in g['nodes']:
        nid = n.get('id')
        if not isinstance(nid, str) or not nid or nid in nodes:
            add('GSN-NODE-ID', 'C01', f'Graph for {oid} has a missing or duplicate node id {nid!r}.',
                'Give every node a unique, stable id.', node_id=nid if isinstance(nid, str) and nid else None)
            continue
        nodes[nid] = n
    for nid, n in nodes.items():
        out.extend(_check_node(req, oid, nid, n, records))

    adjacency, seen = {nid: [] for nid in nodes}, set()
    for e in g['edges']:
        s, t, kind = e.get('source'), e.get('target'), e.get('type')
        kind = kind if isinstance(kind, str) else repr(kind)
        if not _in(s, nodes) or not _in(t, nodes) or s == t:
            add('GSN-EDGE-ENDPOINT', 'C01',
                f'Edge {s} -> {t} in the {oid} graph points to a missing node or to itself.',
                'Connect edges only between existing, distinct nodes.', node_id=s if _in(s, nodes) else None)
            continue
        if (s, t, kind) in seen:
            add('GSN-EDGE-DUP', 'C01', f'Duplicate edge {s} -{kind}-> {t} in the {oid} graph.',
                'Remove the duplicate edge.', node_id=s)
            continue
        seen.add((s, t, kind))
        a, b = nodes[s], nodes[t]
        sources, targets = EDGE_RULES.get(kind, (set(), set()))
        if not _in(a.get('type'), sources) or not _in(b.get('type'), targets):
            add('GSN-EDGE-TYPE', 'C01', f"Edge {s} ({a.get('type')}) -{kind}-> {t} ({b.get('type')}) is not allowed "
                'by the GSN schema.', 'Use supported_by / in_context_of / challenged_by between permitted node types.',
                node_id=s)
        out.extend(_check_edge_scope(oid, s, t, _scope(a), _scope(b)))
        adjacency[s].append(t)

    cycle = _find_cycle(adjacency)
    if cycle:
        add('GSN-CYCLE', 'C01', f'Circular argument in the {oid} graph: {" -> ".join(cycle)}.',
            'Remove the cycle; a claim cannot support itself.', node_id=cycle[0])
    for nid, n in nodes.items():
        supported = any(_in(nodes[c].get('type'), EDGE_RULES['supported_by'][1]) for c in adjacency[nid])
        if n.get('type') in ('goal', 'strategy') and not supported:
            add('GSN-UNSUPPORTED-GOAL', 'C01', f"{n['type'].title()} {nid} in the {oid} graph has no supporting "
                'strategy, sub-goal, solution or unresolved claim.',
                'Decompose it, or link it to an explicit unresolved claim.', node_id=nid)
    return out


def _check_edge_scope(oid, s, t, sa, sb):
    out = []
    if any(sa.get(k) != sb.get(k) for k in K.SCOPE_KEYS):
        out.append(finding('GSN-EDGE-SCOPE', 'C03', f'Edge {s} -> {t} joins nodes with different requirement, '
                           'execution or object scope.', 'Keep every node of an object graph in the same scope.',
                           object_id=oid, node_id=t, requirement_refs=[GSN_REF]))
    if 'interval' in sa or 'interval' in sb:
        ia, ib = _interval(sa.get('interval')), _interval(sb.get('interval'))
        if ia is None or ib is None or sa.get('domain') != sb.get('domain') or sa.get('clock') != sb.get('clock'):
            out.append(finding('GSN-EDGE-TIME', 'C03', f'Edge {s} -> {t} joins nodes without a compatible time scope.',
                               'Give both nodes the same clock and domain and a valid interval.',
                               object_id=oid, node_id=t, requirement_refs=[GSN_REF]))
        elif not _contains(ia, ib):
            out.append(finding('GSN-EDGE-OUTSIDE', 'C03', f'Node {t} covers {list(ib)}, outside the interval '
                               f'{list(ia)} of its parent {s}.',
                               'A supporting node must lie inside its parent interval.',
                               object_id=oid, node_id=t, requirement_refs=[GSN_REF]))
    return out


def _check_node(req, oid, nid, n, records):
    out = []
    ctx = req['evaluation_context']
    ntype, status, origin = n.get('type'), n.get('validation_status'), n.get('origin')
    scope = _scope(n)

    def add(check_id, category, explanation, action, **kw):
        out.append(finding(check_id, category, explanation, action, object_id=oid, node_id=nid,
                           requirement_refs=[GSN_REF], **kw))

    if not n.get('statement') or not _in(ntype, K.NODE_TYPES) or not _in(origin, K.NODE_ORIGINS) \
            or not _in(status, K.NODE_STATUSES):
        add('GSN-NODE-FIELDS', 'C01', f'Node {nid} has an empty statement or an unknown type/origin/status '
            f'({ntype}/{origin}/{status}).', 'Use the GSN 1.0.0 vocabularies.')
    if not n.get('provenance') or not all(scope.get(k) for k in K.SCOPE_KEYS):
        add('GSN-NODE-SCOPE', 'C01', f'Node {nid} lacks provenance or a complete requirement/execution/object scope.',
            'Fill scope.requirement_id, requirement_version, execution_id, object_id and the provenance.')
    if scope.get('execution_id') and scope['execution_id'] != ctx['execution_id']:
        add('GSN-NODE-EXEC', 'C03', f"Node {nid} is scoped to execution {scope['execution_id']}, not the execution "
            f"under review ({ctx['execution_id']}).", 'Only argue about the target execution in this bundle.')
    if scope.get('object_id') and scope['object_id'] != oid:
        add('GSN-NODE-OBJECT', 'C03',
            f"Node {nid} is scoped to object {scope['object_id']} but sits in the {oid} graph.",
            'Move the node to the graph for its object.')
    if (scope.get('requirement_id'), scope.get('requirement_version')) != (ctx['requirement_id'],
                                                                             ctx['requirement_version']) \
            and scope.get('requirement_id') and scope.get('requirement_version'):
        add('GSN-NODE-REQ', 'C03', f"Node {nid} is scoped to requirement {scope['requirement_id']} "
            f"{scope['requirement_version']}, not {ctx['requirement_id']} {ctx['requirement_version']}.",
            'Use the requirement under review.')
    if ntype in ('goal', 'unresolved_claim') and status not in ('proposed', 'unresolved'):
        add('GSN-GOAL-PROMOTION', 'C06', f'Goal {nid} is marked {status}; goals may only be proposed or unresolved '
            'in this phase.', 'Set the goal back to unresolved; promotion needs a validated checker path.')
    if any(k in scope for k in ('interval', 'domain', 'clock')):
        if _interval(scope.get('interval')) is None or scope.get('domain') not in ('frame', 'time') \
                or not scope.get('clock'):
            add('GSN-NODE-TIME', 'C01', f'Node {nid} has an incomplete or invalid time scope.',
                'Give interval, domain and clock together.')
    if n.get('physical_claim') and (ntype not in ('goal', 'unresolved_claim') or status != 'unresolved'):
        add('GSN-PHYSICAL-PROMOTION', 'C05', f'Node {nid} makes a physical claim but is a {ntype} with status '
            f'{status}; physical claims must stay unresolved goals.',
            'Set physical_claim to false, or make it an unresolved goal.')
    if ntype == 'solution':
        out.extend(_check_solution(req, oid, nid, n, scope, records))
    elif n.get('evidence_id') is not None:
        add('GSN-EVIDENCE-ON-NONSOLUTION', 'C01', f"Node {nid} ({ntype}) carries evidence_id {n['evidence_id']}; "
            'only solution nodes may cite evidence.', 'Attach evidence through a solution node.',
            evidence_ids=[str(n['evidence_id'])])
    return out


def _check_solution(req, oid, nid, n, scope, records):
    out = []
    ctx = req['evaluation_context']
    eid = n.get('evidence_id')
    provenance = n.get('provenance') if isinstance(n.get('provenance'), dict) else {}

    def add(check_id, category, explanation, action, **kw):
        out.append(finding(check_id, category, explanation, action, object_id=oid, node_id=nid,
                           evidence_ids=[str(eid)] if eid else [], requirement_refs=[GSN_REF], **kw))

    if not isinstance(eid, str) or eid not in records:
        add('EV-MISSING', 'C02', f'Solution {nid} cites {eid}, which is not in the evidence package.',
            'Cite evidence that was actually retrieved, or request retrieval for it.',
            additional_evidence_needed=True,
            evidence_request={'object_id': oid, 'measurement_type': None,
                              'interval': _interval_or_none(scope.get('interval')),
                              'reason': f'Solution {nid} cites evidence that was not supplied ({eid}).'})
        return out

    r = records[eid]
    related = req['retrieval_context'].get('related_case_evidence_ids')
    related = {x for x in related if isinstance(x, str)} if isinstance(related, list) else set()
    if eid in related:
        add('EV-RELATED-CASE', 'C11', f"Solution {nid} uses {eid}, a related-case record from execution "
            f"{r['execution_id']}, as direct support. Related cases give context; they cannot show what happened "
            f"in {ctx['execution_id']}.", 'Move it to a context node clearly labelled as a related case.')
    elif r['execution_id'] != ctx['execution_id']:
        add('EV-WRONG-EXECUTION', 'C03', f"Solution {nid} uses {eid} from execution {r['execution_id']} as direct "
            f"support for execution {ctx['execution_id']}.", 'Replace it with evidence from the target execution.')
    if r['object_id'] != oid:
        add('EV-WRONG-OBJECT', 'C03',
            f"Solution {nid} in the {oid} graph cites {eid}, which is about {r['object_id']}.",
            f'Cite evidence about {oid}.')
    if any(scope.get(k) != r[k] for k in ('requirement_id', 'requirement_version')):
        add('EV-SCOPE-MISMATCH', 'C03', f'Solution {nid} and {eid} are scoped to different requirement versions.',
            'Copy the requirement scope from the evidence record.')
    if any(provenance.get(k) != r[k] for k in ('source_path', 'source_sha256', 'selector')):
        add('EV-SOURCE-MISMATCH', 'C02', f'Solution {nid} provenance (source path, hash or selector) does not match '
            f'evidence record {eid}.', 'Copy the provenance from the registry record unchanged.')

    claimed, covered = _interval(scope.get('interval')), _interval(r['interval'])
    if claimed is None:
        add('EV-NO-INTERVAL', 'C03', f'Solution {nid} has no time interval, so its coverage cannot be compared '
            f'with {eid}.', 'Give the solution the same interval as its evidence record.')
    elif claimed != covered or scope.get('domain') != r['domain'] or scope.get('clock') != r['clock']:
        add('EV-INTERVAL-MISMATCH', 'C03', f"Solution {nid} claims {list(claimed)} ({scope.get('clock')}), but {eid} "
            f"covers {r['interval']} ({r['clock']}).",
            'Make the solution scope match its evidence exactly; never stretch evidence over a longer interval.')

    expected_origin = K.KIND_TO_ORIGIN.get(r['kind']) if isinstance(r['kind'], str) else None
    if n.get('origin') != expected_origin or n.get('validation_status') != r['validation_status']:
        add('EV-AUTHORITY', 'C12' if r['kind'] == 'ai_reference_judgment' else 'C02',
            f"Solution {nid} presents {eid} as {n.get('origin')}/{n.get('validation_status')}, but the record is a "
            f"{r['kind']} with status {r['validation_status']}.",
            'Keep origin and status exactly as recorded; an AI review is neither a measurement nor human ground truth.')
    if _in(r['validation_status'], K.UNUSABLE_RECORD_STATUSES):
        add('EV-UNUSABLE', 'C02', f"Solution {nid} relies on {eid}, whose validation status is "
            f"{r['validation_status']}.", 'Do not use invalid, missing or unsupported records as support.')
    return out


def _find_cycle(adjacency):
    """Return one cycle as a list of node ids, or None."""
    state, stack = {}, []

    def visit(k):
        state[k] = 'open'
        stack.append(k)
        for child in adjacency.get(k, []):
            if state.get(child) == 'open':
                return stack[stack.index(child):] + [child]
            if child not in state:
                found = visit(child)
                if found:
                    return found
        stack.pop()
        state[k] = 'done'
        return None

    for k in adjacency:
        if k not in state:
            found = visit(k)
            if found:
                return found
    return None


# ------------------------------------------------------------------ conclusions

def check_assessments(req):
    """Validate every checker result before anything relies on it (see assessments.py).

    Returns (findings, admitted {object_id: [assessment]}, admission log for the report).
    """
    admitted, log, problems = A.admit(req)
    out = []
    for check_id, category, text, aid, oid in problems:
        out.append(finding(check_id, category, f'Checker assessment {aid} is not used: {text}.',
                           'Pass the R1 checker output (evaluation/r1_v4/runtime.py:assess) unchanged, together with '
                           'the configuration it ran on, for this requirement, execution and object.',
                           object_id=oid, evidence_ids=[aid], requirement_refs=[A.CONTRACT_REF]))
    return out, admitted, log


def check_conclusions(req, admitted):
    """Claimed outcomes against admitted checker assessments and R1 aggregation.

    Returns (findings, R1 aggregation of the full claimed vector, with missing or invalid object outcomes
    counted as insufficient_information).
    """
    out = []
    ctx, bundle = req['evaluation_context'], req['argument_bundle']
    conclusion = bundle['execution_conclusion']
    claimed = conclusion['object_outcomes']
    configured = ctx['protected_objects']
    monitored = _interval(ctx['monitored_interval']['interval'])
    roots = {item.get('object_id'): _root_goal(item.get('graph')) for item in bundle['graphs']}

    for oid in configured:
        if oid not in claimed:
            if oid in roots:  # objects with no graph at all are already reported as BUNDLE-MISSING
                out.append(finding('CONCL-OBJ-MISSING', 'C04', f'The execution conclusion gives no outcome for {oid}.',
                                   f'State an outcome for {oid}; use insufficient_information if it is unknown.',
                                   object_id=oid, requirement_refs=[AGGREGATION_REF]))
            continue
        out.extend(_check_object_outcome(oid, claimed[oid], roots.get(oid), admitted.get(oid, []),
                                         monitored, _list(req['retrieval_context'].get('gaps'))))
    for oid in claimed:
        if oid not in configured:
            out.append(finding('CONCL-EXTRA', 'C03', f'The execution conclusion gives an outcome for {oid}, which is '
                               'not a configured protected object.', 'Remove it.', severity='medium', object_id=oid))

    # The full vector over every configured object: a missing or invalid object outcome counts as
    # insufficient_information, never as dropped. An empty configured scope aggregates to not_applicable.
    vector = [claimed[o] if _is_outcome(claimed.get(o)) else K.INSUFFICIENT for o in configured]
    expected = K.execution_outcome(vector)
    unassessed = [o for o in configured if not _is_outcome(claimed.get(o))]
    stated = conclusion.get('claimed_outcome')
    if stated is not None and not _is_outcome(stated):
        out.append(finding('CONCL-BAD-VALUE', 'C01', f'Execution outcome {stated!r} is not an R1 v2 outcome.',
                           f'Use one of: {", ".join(K.OUTCOME_PRECEDENCE)}.'))
    elif stated is not None and stated != expected:
        disputed = sorted({f['object_id'] for f in out if f['object_id'] is not None and f['blocking']})
        action = (f'Fix the object outcomes flagged for {", ".join(disputed)} first, then set the execution outcome '
                  'by R1 aggregation of the corrected object outcomes.' if disputed else
                  f'Set the execution outcome to {expected}, or fix the object outcomes.')
        if not configured:
            why = ('The configuration has no protected objects (empty scope), which aggregates to not_applicable; '
                   'an empty scope is never a pass and is excluded from outcome metrics.')
        else:
            why = (f'R1 aggregation of every configured object gives {expected} (violation > invalid contract > '
                   'insufficient > no violation > not applicable).')
            if unassessed:
                one = len(unassessed) == 1
                why += (f' {", ".join(unassessed)} {"has" if one else "have"} no valid outcome and '
                        f'{"counts" if one else "count"} as insufficient_information; unknown objects are never '
                        'treated as safe.')
        out.append(finding('CONCL-AGGREGATION', 'C06', f'The execution conclusion is {stated}. {why}', action,
                           requirement_refs=[AGGREGATION_REF]))
    return out, expected


def _check_object_outcome(oid, claim, node, assessments, monitored, gaps):
    """One object's claimed outcome against its admitted checker assessments and retrieval gaps.

    FORMAL_SEMANTICS.md: an admissible violation is not overridden by a negative result;
    conflicting assessments are kept and need an evidence-consistency investigation; an
    insufficient or invalid-contract result is a gap, not evidence against a claim.
    """
    def make(check_id, category, explanation, action, **kw):
        return finding(check_id, category, explanation, action, object_id=oid, node_id=node, **kw)

    if not _is_outcome(claim):
        return [make('CONCL-BAD-VALUE', 'C01', f'Outcome {claim!r} for {oid} is not an R1 v2 outcome.',
                     f'Use one of: {", ".join(K.OUTCOME_PRECEDENCE)}.')]
    out = []
    ids = [a['assessment_id'] for a in assessments]
    label = A.describe(assessments[0]) if assessments else 'admitted checker assessment'
    verdict, conflict = assessment_verdict(assessments)
    positive = any(a['outcome'] == K.VIOLATION for a in assessments)

    if conflict and (claim != K.INSUFFICIENT or positive):
        listing = '; '.join(f"{a['assessment_id']} reports {a['outcome']}" for a in assessments)
        out.append(make('CONCL-CONFLICT', 'C13', f'The admitted checker assessments for {oid} disagree ({listing}). '
                        + ('A negative or other result cannot override an admissible violation. ' if positive else
                           f'The claim {claim} cannot be established from inconsistent evidence. ')
                        + 'Both records are kept; the conflict needs an evidence-consistency investigation.',
                        'Record the conflict as an unresolved defeater citing both assessments, and find out which '
                        'one is wrong before relying on either.',
                        evidence_ids=ids, requirement_refs=[OUTCOME_REF], human_review_required=True))

    if not assessments:
        if claim != K.INSUFFICIENT:
            what = {K.NOT_APPLICABLE: 'non-applicability (an established absence of initial support)',
                    K.VIOLATION: 'a violation',
                    K.NO_VIOLATION: 'a coverage-qualified no-violation result',
                    K.INVALID_CONTRACT: 'an invalid measurement contract'}[claim]
            out.append(make('CONCL-UNSUPPORTED', 'C08' if claim == K.NOT_APPLICABLE else 'C06',
                            f'The draft claims {claim} for {oid}, but no admitted checker assessment for this object '
                            f'and execution is supplied. Positions and contacts alone cannot establish {what}.',
                            f'Change the {oid} outcome to insufficient_information and keep its goal unresolved, '
                            'unless an admitted checker assessment is added.',
                            requirement_refs=[SPEC_REF, 'Critic handoff section 6'], additional_evidence_needed=True,
                            evidence_request={'object_id': oid, 'measurement_type': 'checker_assessment',
                                              'interval': list(monitored),
                                              'reason': f'An admitted R1 checker assessment is needed before '
                                                        f'claiming {claim}.'}))
    elif positive:
        violations = [a['assessment_id'] for a in assessments if a['outcome'] == K.VIOLATION]
        if claim == K.INSUFFICIENT:
            out.append(make('CONCL-HIDES-VIOLATION', 'C07', f'The draft reports insufficient_information for {oid}, '
                            f'but an {label} for the same object and execution reports violation_observed.',
                            'Report the violation the assessment shows, or record why the assessment is '
                            'not admissible as an explicit defeater.', evidence_ids=violations,
                            requirement_refs=[OUTCOME_REF], human_review_required=True))
        elif claim != K.VIOLATION:
            out.append(make('CONCL-CONTRADICTION', 'C07', f'The draft claims {claim} for {oid}, but an {label} for '
                            'the same object and execution reports violation_observed, and an admissible violation '
                            'is not overridden by other results.',
                            'Report the violation, or record why the assessment is not admissible as an explicit '
                            'defeater.', evidence_ids=violations, requirement_refs=[OUTCOME_REF],
                            human_review_required=True))
    elif not conflict and claim not in (verdict, K.INSUFFICIENT):
        found = verdict
        if found in (K.INSUFFICIENT, K.INVALID_CONTRACT):
            out.append(make('CONCL-NOT-ESTABLISHED', 'C08' if claim == K.NOT_APPLICABLE else 'C06',
                            f'The draft claims {claim} for {oid}, but the {label} could not establish an outcome: it '
                            f'reports {found}. That is a gap in the evidence, not evidence against the claim, but it '
                            'leaves the claim unsupported.',
                            f'Change the {oid} outcome to {found} or insufficient_information, or supply the evidence '
                            'the checker was missing.', evidence_ids=ids, requirement_refs=[VALIDITY_REF],
                            additional_evidence_needed=True))
        elif K.NOT_APPLICABLE in (found, claim):
            out.append(make('CONCL-APPLICABILITY', 'C08', f'The draft claims {claim} for {oid}, but the {label} '
                            f'reports {found}, so the claim treats applicability differently from the checker.',
                            f'Match the checker ({found}), or record why its applicability result is wrong as an '
                            'explicit defeater.', evidence_ids=ids, requirement_refs=[SPEC_REF + '#applicability'],
                            human_review_required=True))
        else:
            out.append(make('CONCL-CONTRADICTION', 'C07', f'The draft claims {claim} for {oid}, but the {label} '
                            f'for the same object and execution reports {found}.',
                            'Match the admitted assessment, or explain the conflict as an unresolved defeater.',
                            evidence_ids=ids, requirement_refs=[OUTCOME_REF], human_review_required=True))

    supported = verdict == K.NO_VIOLATION and not conflict
    if claim == K.NO_VIOLATION and supported and not any(_contains(_interval(a['interval']), monitored)
                                                         for a in assessments):
        out.append(make('CONCL-PARTIAL-COVERAGE', 'C04', f'The no-violation assessment for {oid} does not cover the '
                        f'whole monitored interval {list(monitored)}.',
                        'Qualify the claim to the covered interval, or keep it insufficient_information.',
                        evidence_ids=ids, requirement_refs=[OUTCOME_REF]))
    if claim == K.NO_VIOLATION:
        for gap in gaps:
            if not _gap_relevant(gap, oid, monitored):
                continue  # still listed in the report's unresolved_concerns as a limitation
            mtype = gap.get('measurement_type') if isinstance(gap.get('measurement_type'), str) else None
            reason = gap.get('reason') if isinstance(gap.get('reason'), str) else 'Gap reported by retrieval.'
            request = {'object_id': oid, 'measurement_type': mtype,
                       'interval': _interval_or_none(gap.get('interval')), 'reason': reason}
            if supported:
                # A gap in the Drafter's package does not by itself invalidate an admitted checker witness.
                out.append(make('CONCL-GAP', 'C04', f'The admitted checker assessment supports no violation for '
                                f"{oid}, but retrieval reports missing {mtype} for {gap.get('interval')} inside the "
                                'monitored interval. This does not by itself invalidate the assessment; check that '
                                'the two sources agree.',
                                'Confirm the checker had the data retrieval reports as missing, or qualify the claim.',
                                severity='medium', blocking=False, evidence_ids=ids, requirement_refs=[VALIDITY_REF],
                                human_review_required=True, evidence_request=request))
            else:
                out.append(make('CONCL-GAP', 'C04', f"The draft claims no violation for {oid}, but retrieval reports "
                                f"missing {mtype} for {gap.get('interval')}.",
                                'Do not claim coverage over missing intervals; qualify the claim or request the data.',
                                requirement_refs=[VALIDITY_REF], additional_evidence_needed=True,
                                evidence_request=request))
    return out


DEFINITE = (K.VIOLATION, K.NO_VIOLATION, K.NOT_APPLICABLE)


def assessment_verdict(assessments):
    """(verdict, conflict) for one object's admitted assessments.

    Two different definite results (violation, no violation, not applicable) conflict, and so does an
    invalid-contract result next to a definite one (a foundational error can invalidate a witness).
    An insufficient result next to others is a gap, not counter-evidence, and does not conflict.
    The verdict is the definite result if there is exactly one, else invalid contract, else insufficient;
    None when there are no assessments.
    """
    outcomes = {a['outcome'] for a in assessments}
    if not outcomes:
        return None, False
    definite = [o for o in DEFINITE if o in outcomes]
    conflict = len(definite) > 1 or (bool(definite) and K.INVALID_CONTRACT in outcomes)
    if len(definite) == 1:
        return definite[0], conflict
    if definite:
        return None, conflict
    return (K.INVALID_CONTRACT if K.INVALID_CONTRACT in outcomes else K.INSUFFICIENT), conflict


def _gap_relevant(gap, oid, monitored):
    """A retrieval gap matters for a no-violation claim only if it is for this object, overlaps the monitored
    interval, and is not an optional measurement. Malformed gaps count as relevant (fail closed)."""
    if not isinstance(gap, dict) or gap.get('object_id') != oid:
        return False
    mtype = gap.get('measurement_type')
    if isinstance(mtype, str) and mtype in K.OPTIONAL_EVIDENCE:
        return False
    span = _interval(gap.get('interval'))
    return span is None or _overlaps(span, monitored)


def _is_outcome(value):
    return isinstance(value, str) and value in K.OUTCOMES


def _root_goal(g):
    """The top goal of an object graph: a goal no edge points to."""
    if not isinstance(g, dict):
        return None
    edges, nodes = g.get('edges'), g.get('nodes')
    if not isinstance(edges, list) or not isinstance(nodes, list):
        return None
    targets = {e.get('target') for e in edges if isinstance(e, dict) and isinstance(e.get('target'), str)}
    for n in nodes:
        is_goal = isinstance(n, dict) and n.get('type') == 'goal' and isinstance(n.get('id'), str)
        if is_goal and n['id'] not in targets:
            return n.get('id')
    return None


def run_all(req):
    """Run every deterministic check. Returns (findings, info for the LLM step and report)."""
    findings, fatal = check_request_shape(req)
    if fatal:
        return findings, {'fatal': True, 'records': {}, 'expected_outcome': None,
                          'admitted': {}, 'checker_admission': [], 'input_valid': False}
    problems = SCHEMA.errors(req, SCHEMA.load('request'), limit=10)
    if problems:
        findings.append(finding('SCHEMA-REQUEST', 'C01', 'The review request does not match '
                                f'{K.REQUEST_SCHEMA_VERSION}: {"; ".join(problems)}.',
                                'Send a complete request that validates against critic_request.schema.json; '
                                'synthetic data must be marked test_fixture explicitly.',
                                requirement_refs=[str(SCHEMA.SCHEMAS['request'].name)]))
    findings += check_configuration(req)
    records, record_findings = index_records(req)
    findings += record_findings
    findings += check_bundle(req)
    for item in req['argument_bundle']['graphs']:
        findings += check_graph(req, item, records)
    assessment_findings, admitted, admission = check_assessments(req)
    findings += assessment_findings
    conclusion_findings, expected = check_conclusions(req, admitted)
    findings += conclusion_findings
    return findings, {'fatal': False, 'records': records, 'expected_outcome': expected,
                      'admitted': admitted, 'checker_admission': admission,
                      'input_valid': not any(f['phase'] == 'validation' for f in findings)}
