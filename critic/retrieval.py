"""Phase 5 structured evidence: when the Critic uses a bundle, and what it may use it for.

A review request may carry `structured_evidence`: each entry is the exact structured request sent to the
Phase 5 release (evaluation/r1_v4/rag_evidence_database/final_phase5_release, phase5-structured-1.0.0)
and the exact bundle it returned. Following the release's DOWNSTREAM_HANDOFF.md, admit() checks that each
pair is what the release produces for this review before anything uses it:

- the bundle matches the release's EVIDENCE_BUNDLE_SCHEMA.json and the Critic's consumer schema
  (schemas/phase5_bundle_consumer.schema.json), and the release files match their pinned hashes;
- it is for this review's execution, task and variant, and every item is too;
- its query ID is the hash of the request it came with, and every group is that request's obligation;
- missing_obligations, conditional_assumptions and the completeness status follow from the groups and
  the independent validation exactly as api.py derives them, so no missing obligation or assumption was
  dropped and no status was upgraded;
- a request the release would refuse returned no evidence;
- every evidence-citation ID is the hash of its citation_basis, and that basis describes this item under
  this obligation and the pinned database.

What an admitted bundle can do: it can only add concerns. A missing mandatory obligation inside the
monitored interval undermines a no-violation claim (checks._check_object_outcome); every non-complete
status, missing obligation and conditional assumption is reported as it is. It never supports a claim
and is never a checker assessment or a physical event: COMPLETE WITHIN VERIFIED CONTRACT covers the
request's explicit mandatory obligations only, not complete R1 observations or claim sufficiency.

The Critic recomputes hashes but cannot open the database or the sources, so a bundle is checked for
consistency, not authenticated (EVIDENCE_CITATION_CONTRACT.md).

GSN 1.0.0 solution nodes keep citing registry records, as Graph.validate requires. link() reports which
bundle items back a solution: those whose original_evidence_ids include the solution's registry record.
That crosswalk is checked first (audit R2-06): an original ID that names a record in the evidence package
must be one the release itself would list for that item (retrieval_remediation/bundle.py: Retriever.retrieve
selects them by execution, measurement type, object and frame window, per family), or the bundle is
refused (RET-CROSSWALK). An original ID that is not in the package cannot be checked and links nothing.
"""
import hashlib

from . import contract as K
from . import schema as SCHEMA

CONTRACT_REF = 'evaluation/r1_v4/rag_evidence_database/final_phase5_release/SUPPORTED_INTERFACE_CONTRACT.md'
HANDOFF_REF = 'evaluation/r1_v4/rag_evidence_database/final_phase5_release/DOWNSTREAM_HANDOFF.md'
CITATION_PREFIX = 'evidence-citation:'
# ID prefixes of Phase 5 items and citations; none of them is a registry record a GSN solution can cite.
PHASE5_ID_PREFIXES = (CITATION_PREFIX, 'channel:', 'source-ref:')
# Flags the release sets to false on every item value: an observation is never a physical event.
PHYSICAL_FLAGS = ('physical_support_inferred', 'physical_contact_or_support_inferred', 'synchronized_physical_instant',
                  'same_physical_instant')
CHANNEL_ORIGIN = 'direct_recording'
REFERENCE_ORIGINS = ('recorded_metadata_or_existing_derived_identity', 'existing_derived_symbolic_identity')
_PINS = (('phase5_query', K.PHASE5_QUERY_SCHEMA_SHA256), ('phase5_bundle', K.PHASE5_BUNDLE_SCHEMA_SHA256))

# Which registry records the release lists in an item's original_evidence_ids (retrieval_remediation/bundle.py,
# Retriever.retrieve): family -> (measurement_type, object rule, frame window rule). 'object' means the record's
# object must be the obligation's object; 'object_if_named' only when the obligation names one. Every other
# family lists none (channel items list themselves).
CROSSWALK = {
    'geometry_identity': ('object_identity', 'object', False),
    'execution_metadata': ('execution_metadata', None, False),
    'contact_references': ('contact', 'object_if_named', True),
    'camera_references': ('camera_reference', 'object_if_named', True),
}


def release_problems():
    """Release schema files that do not match their pinned hashes (empty when all match)."""
    out = []
    for name, pinned in _PINS:
        path = SCHEMA.SCHEMAS[name]
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            actual = 'unreadable'
        if actual != pinned:
            out.append(f'{path.name} ({actual[:12]}, pinned {pinned[:12]})')
    return out


def admit(req, records=None):
    """Check every structured_evidence entry. records: the request's registry records by ID, for the crosswalk.

    Returns (problems [(check_id, category, text, query_id)], admitted bundles for the review,
    rows for the report's structured_retrieval list).
    """
    entries = req.get('structured_evidence', [])
    if not isinstance(entries, list):
        return [('RET-SHAPE', 'C02', 'structured_evidence is not a list', None)], [], []
    release = release_problems() if entries else []
    problems, admitted, rows = [], [], []
    for index, entry in enumerate(entries):
        found, view = _check_entry(entry, req['evaluation_context'], records or {})
        if release:
            found.insert(0, ('RET-RELEASE', 'C02', 'the Phase 5 release files changed since the Critic pinned them: '
                             + ', '.join(release)))
        qid = view['query_id'] if view else None
        problems += [(check_id, category, f'structured_evidence[{index}]: {text}', qid)
                     for check_id, category, text in found]
        accepted = view is not None and not found
        if accepted:
            view['index'] = index
            admitted.append(view)
        rows.append(_row(index, entry, view, accepted))
    return problems, admitted, rows


def link(req, admitted, rows):
    """Record in each report row the solution nodes backed by one of its items (see module docstring)."""
    backing = {}
    for view in admitted:
        for item in view['items']:
            for original in item['original_evidence_ids']:
                backing.setdefault(original, []).append((view['index'], item['citation_id']))
    by_index = {row['index']: row for row in rows}
    for graph_item in req['argument_bundle']['graphs']:
        graph = graph_item.get('graph') if isinstance(graph_item.get('graph'), dict) else {}
        nodes = graph.get('nodes') if isinstance(graph.get('nodes'), list) else []
        for n in nodes:
            if not isinstance(n, dict) or n.get('type') != 'solution' or not isinstance(n.get('evidence_id'), str):
                continue
            for index, citation in backing.get(n['evidence_id'], []):
                by_index[index]['linked_solutions'].append({
                    'object_id': graph_item['object_id'],
                    'node_id': n.get('id') if isinstance(n.get('id'), str) else None,
                    'evidence_id': n['evidence_id'], 'citation_id': citation})


# ------------------------------------------------------------------ one entry

def _check_entry(entry, ctx, records):
    """Return (problems [(check_id, category, text)], view or None)."""
    if not isinstance(entry, dict) or not isinstance(entry.get('request'), dict) \
            or not isinstance(entry.get('bundle'), dict):
        return [('RET-SHAPE', 'C02', 'the entry is not a {request, bundle} pair of objects')], None
    q, b = entry['request'], entry['bundle']
    schema_errors = SCHEMA.errors(b, SCHEMA.load('phase5_bundle'), limit=3)
    schema_errors += SCHEMA.errors(b, SCHEMA.load('phase5_consumer'), limit=3)
    if schema_errors:
        return [('RET-BUNDLE-SCHEMA', 'C02', 'the bundle is not a phase5-structured-1.0.0 bundle as the release '
                 'builds it: ' + '; '.join(schema_errors[:3]))], None

    out = []

    def bad(check_id, category, text):
        out.append((check_id, category, text))

    status, iv = b['completeness_status'], b['independent_validation']
    groups = b['groups']
    items = [i for g in groups for i in g['items']]

    # The request: one the release would refuse must come back without evidence.
    refusal = request_refusal(q)
    if refusal and iv['passed']:
        bad('RET-QUERY', 'C02', f'the release refuses this request ({refusal}), but the bundle reports it as '
            f'evaluated ({status})')
    from .phase5_request import returned_window_refusal
    budget = returned_window_refusal(q, b)
    if budget:
        bad('RET-QUERY', 'C02', f'the returned windows violate the public retrieval limit: {budget[1]}')

    # Scope: this review's execution, task and variant, for the bundle, the request and every item.
    scope = {k: ctx.get(k) for k in ('execution_id', 'task_id', 'variant_id')}
    resolved = {k: b['resolved_scope'][k] for k in scope}
    obligations = q.get('obligations', [])
    asked = [q] + [o for o in obligations if isinstance(o, dict)] if isinstance(obligations, list) else [q]
    if resolved != scope:
        bad('RET-SCOPE', 'C03', f'the bundle is for {_describe(resolved)}, but this review is for '
            f'{_describe(scope)}; another execution, task or variant is never a substitute')
    elif any(q.get(k) != scope[k] for k in scope) or any(k in x and x[k] != scope[k] for x in asked for k in scope):
        bad('RET-SCOPE', 'C03', f'the request must state this review\'s scope ({_describe(scope)}) explicitly, and '
            'it or one of its obligations does not')

    # Identity: the bundle answers exactly this request.
    if b['query_id'] != 'query:' + _digest(q):
        bad('RET-QUERY-ID', 'C02', f"query_id {b['query_id']} is not the hash of the supplied request, so the "
            'request or the bundle was changed after retrieval')
    if not _same(b['requested_obligations'], obligations):
        bad('RET-QUERY-ID', 'C02', "requested_obligations differ from the request's obligations")
    out += _check_groups(groups, obligations, iv)

    # Items: scope, time window, integrity and citations.
    by_id = {o.get('id'): o for o in obligations if isinstance(o, dict) and isinstance(o.get('id'), str)} \
        if isinstance(obligations, list) else {}
    for g in groups:
        o = by_id.get(g['obligation_id'], {})
        for item in g['items']:
            out += _check_item(item, g, o, resolved, iv['passed'])
            out += _check_crosswalk(item, g, o, records)
        if g['family'] in K.PHASE5_CHANNELS and g['items'] and iv['passed']:
            expected = conditional_properties(g, o)
            if expected is None or not _same(g.get('conditional_assumptions', []), expected):
                bad('RET-CONDITIONAL', 'C09', f"group {g['obligation_id']}: conditional_assumptions do not list "
                    'exactly the required properties its evidence marks CONDITIONAL')
        window = _frames(o.get('selector'))
        if g['family'] in K.PHASE5_CHANNELS and g['status'] == 'AVAILABLE' and window is not None:
            observed = {s['saved_frame_index'] for i in g['items'] for s in i.get('samples', [])}
            if observed != set(range(window[0], window[1] + 1)):
                bad('RET-ITEM', 'C04', f"group {g['obligation_id']} is AVAILABLE, but its samples do not cover the "
                    f'requested frames {list(window)}')

    if not _same(b['assurance_status']['requested'], q.get('assurance')):
        bad('RET-STATUS', 'C02', "assurance_status.requested is not the request's assurance")
    if b['limitations'] != list(K.PHASE5_LIMITATIONS):
        bad('RET-LIMITATIONS', 'C02', "the release's limitations were changed or dropped")

    out += _check_status(b, groups, items, status, iv)
    view = _view(b, q, groups, iv) if not out else {'query_id': b['query_id']}
    return out, view


def _check_crosswalk(item, g, o, records):
    """original_evidence_ids that name a registry record in the package must be ones the release would list."""
    out = []
    rule = CROSSWALK.get(item['family'])
    for rid in item['original_evidence_ids']:
        rec = records.get(rid)
        if rec is None:
            continue  # not in the package: cannot be checked, and links nothing
        name = f"group {g['obligation_id']} item {item['id']}"
        if rule is None:
            out.append(('RET-CROSSWALK', 'C03', f"{name} lists registry record {rid} as its original evidence, but the "
                        f"release lists none for a {item['family']} item"))
            continue
        kind, object_rule, windowed = rule
        wanted = o.get('object_id') if object_rule == 'object' or (object_rule and 'object_id' in o) else None
        window = _frames(o.get('selector')) if windowed else None
        interval = rec.get('interval')
        wrong = []
        if rec.get('execution_id') != item['execution_id']:
            wrong.append(f"execution {rec.get('execution_id')}")
        if rec.get('measurement_type') != kind:
            wrong.append(f"measurement type {rec.get('measurement_type')} (the release lists {kind} records)")
        if (object_rule == 'object' and not isinstance(wanted, str)) \
                or (wanted is not None and rec.get('object_id') != wanted):
            wrong.append(f"object {rec.get('object_id')} (the obligation is for {wanted})")
        if windowed and (window is None or not (isinstance(interval, list) and len(interval) == 2
                                                and all(K.finite_number(x) for x in interval)
                                                and interval[0] <= window[1] and interval[1] >= window[0])):
            wrong.append(f'interval {interval} outside the requested frames {list(window) if window else None}')
        if wrong:
            out.append(('RET-CROSSWALK', 'C03', f"{name} lists registry record {rid} as its original evidence, but "
                        f"the release would not: that record has {'; '.join(wrong)}. Its link to a GSN solution "
                        'would be false'))
    return out


def conditional_properties(g, o):
    """The conditional assumptions api.py:StructuredRetriever.raw lists for a channel group with evidence, or
    None if a property it requires is not described by the evidence."""
    required = set(o.get('required_properties', [])) if _strings(o.get('required_properties', [])) else set()
    if o.get('interpretation', 'recorded') == 'verified_physical':
        required |= {'component_order', 'units', 'coordinate_frame'}
    described = g['items'][0].get('interpretation_properties')
    if not isinstance(described, dict) or not all(isinstance(described.get(p), dict) for p in required):
        return None
    out = {p for p in required if described[p].get('status') == 'CONDITIONAL'}
    if any(s.get('selected_unit_status') == 'CONDITIONAL' for i in g['items'] for s in i.get('samples', [])):
        out.add('si_component_units')
    return sorted(out)


def request_refusal(q):
    """Database-independent refusal rules from the frozen public prepare method itself."""
    from .phase5_request import refusal
    result = refusal(q)
    return f'{result[0]}: {result[1]}' if result else None


def _check_groups(groups, obligations, iv):
    """Groups are the request's obligations, in order, as api.py emits them. For a request it did not
    evaluate, StructuredRetriever.response lists one group per object obligation with a string id, and
    none when the request has more than 16 obligations."""
    out = []
    listed = [o for o in obligations if isinstance(o, dict) and isinstance(o.get('id'), str)] \
        if isinstance(obligations, list) and (iv['passed'] or len(obligations) <= 16) else []
    if [g['obligation_id'] for g in groups] != [o['id'] for o in listed]:
        out.append(('RET-OBLIGATIONS', 'C02', 'the groups are not the obligations of the request (one is missing, '
                    'added or reordered)'))
        return out
    for g, o in zip(groups, listed):
        if g['request_digest'] != _digest(o):
            out.append(('RET-OBLIGATIONS', 'C02', f"group {g['obligation_id']}: request_digest is not the hash of "
                        'its obligation'))
        if g['family'] != o.get('family', 'unknown') or g['mandatory'] != o.get('mandatory', True):
            out.append(('RET-OBLIGATIONS', 'C02', f"group {g['obligation_id']}: family or mandatory flag differs "
                        'from its obligation'))
        if iv['passed'] and g.get('requested_interpretation') != o.get('interpretation', 'recorded'):
            out.append(('RET-OBLIGATIONS', 'C02', f"group {g['obligation_id']}: requested_interpretation differs "
                        'from its obligation'))
    return out


def _check_item(item, g, o, scope, evaluated):
    out = []
    name = f"group {g['obligation_id']} item {item['id']}"
    if item['family'] != g['family']:
        out.append(('RET-ITEM', 'C03', f'{name} is a {item["family"]} item in a {g["family"]} group'))
    if any(item[k] != scope[k] for k in ('execution_id', 'task_id', 'variant_id')):
        out.append(('RET-ITEM', 'C03', f'{name} is for {_describe(item)}, not the bundle scope {_describe(scope)}'))
    if item['family'] in K.PHASE5_CHANNELS:
        # api.py:StructuredRetriever.raw: the item is the original channel record itself.
        if not item['id'].startswith('channel:') or item['original_evidence_ids'] != [item['id']]:
            out.append(('RET-ITEM', 'C02', f'{name} is a channel item, so it must be its own original channel record'))
    elif item['id'] != 'source-ref:' + _digest([item['source_artifact'][k] for k in ('path', 'sha256', 'selector')]):
        # retrieval_remediation/bundle.py:Retriever.item: the ID is the hash of the source reference.
        out.append(('RET-ITEM', 'C02', f'{name}: the ID is not the hash of its source path, hash and selector'))
    if item['origin'] not in ((CHANNEL_ORIGIN,) if item['family'] in K.PHASE5_CHANNELS else REFERENCE_ORIGINS):
        out.append(('RET-ITEM', 'C05', f"{name} has origin {item['origin']!r}, which the release never gives "
                    f"{'a channel' if item['family'] in K.PHASE5_CHANNELS else 'a recorded-metadata'} item"))
    value = item.get('value')
    if isinstance(value, dict) and 'object_id' in value and 'object_id' in o \
            and value['object_id'] != o['object_id']:
        out.append(('RET-ITEM', 'C03', f'{name}: returned object identity differs from the obligation'))
    flags = [f for f in PHYSICAL_FLAGS if isinstance(value, dict) and value.get(f) is not False and f in value]
    if flags:
        out.append(('RET-ITEM', 'C05', f'{name} turns a recorded observation into a physical event '
                    f'({", ".join(flags)} is not false)'))
    if item['family'] in K.PHASE5_CHANNELS:
        out += _check_channel_semantics(item, name)
        if 'record_id' in o and o['record_id'] != item['id']:
            out.append(('RET-ITEM', 'C03', f'{name}: requested original record identity differs from the item'))
        if 'source_sha256' in o and o['source_sha256'] != item['source_artifact']['sha256']:
            out.append(('RET-ITEM', 'C03', f'{name}: requested source hash differs from the item'))
    if evaluated and any(s.get('source_status') != 'verified_source' for s in item.get('samples', [])):
        out.append(('RET-ITEM', 'C02', f'{name} has samples that are not source-verified in a bundle that passed '
                    'independent validation'))
    if evaluated and item['integrity_status'] != 'verified_source':
        out.append(('RET-ITEM', 'C02', f"{name} has integrity status {item['integrity_status']!r} in a bundle "
                    'that passed independent validation'))
    window = _frames(o.get('selector'))
    if window is not None:
        indices = [s['saved_frame_index'] for s in item.get('samples', [])]
        value = item.get('value')
        if isinstance(value, dict) and _is_int(value.get('saved_frame_index')):
            indices.append(value['saved_frame_index'])
        outside = sorted({i for i in indices if not window[0] <= i <= window[1]})
        if outside:
            out.append(('RET-ITEM', 'C03', f'{name} has frames {outside} outside the requested window {list(window)}'))

    basis = item['citation_basis']
    expected = expected_basis(item, o)
    if not _same(basis, expected):
        differ = sorted(k for k in expected if not _same(basis.get(k), expected[k]))
        out.append(('RET-CITATION', 'C02', f'{name}: citation_basis does not describe this item under its obligation '
                    f'and the pinned database ({", ".join(differ)})'))
    if item['citation_id'] != CITATION_PREFIX + _digest(basis):
        out.append(('RET-CITATION', 'C02', f"{name}: {item['citation_id']} is not the hash of its citation_basis"))
    return out


def _check_channel_semantics(item, name):
    """Units and frame of a channel item and its samples are the ones its interpretation properties state
    (completeness.py checks them against the database; here only that they agree with each other)."""
    props = item.get('interpretation_properties')
    units, frame = (props.get('units'), props.get('coordinate_frame')) if isinstance(props, dict) else (None, None)
    consistent = isinstance(units, dict) and isinstance(frame, dict) and _same(item.get('units'), units) \
        and _same(item.get('coordinate_frame'), frame) \
        and all(s.get('value_units') == units.get('value') and s.get('coordinate_frame') == frame.get('value')
                for s in item.get('samples', []))
    if consistent:
        return []
    return [('RET-ITEM', 'C02', f'{name}: units or coordinate frame differ from its interpretation properties')]


def expected_basis(item, o):
    """The citation basis api.py:StructuredRetriever.retrieve builds for this item and obligation."""
    selectors = [s['source_selector'] for s in item.get('samples', [])] or [item['source_artifact']['selector']]
    properties = o.get('required_properties', [])
    return {'citation_version': K.PHASE5_CITATION_VERSION, 'database_sha256': K.PHASE5_DATABASE_SHA256,
            'record_id': item['id'], 'source_sha256': item['source_artifact']['sha256'],
            'execution_id': item['execution_id'], 'task_id': item['task_id'], 'variant_id': item['variant_id'],
            'selectors': selectors, 'component': o.get('component'), 'units': o.get('units'),
            'interpretation': o.get('interpretation', 'recorded'),
            'required_properties': sorted(properties) if _strings(properties) else properties}


def _check_status(b, groups, items, status, iv):
    """missing_obligations, conditional_assumptions and the status follow from the groups (api.py)."""
    out = []

    def bad(check_id, text):
        out.append((check_id, 'C02', text))

    missing = [{'obligation_id': g['obligation_id'], 'mandatory': g['mandatory'], 'status': g['status'],
                'reason': g['reason']} for g in groups if g['status'] != 'AVAILABLE']
    if not _same(b['missing_obligations'], missing):
        bad('RET-MISSING', 'missing_obligations is not the list of groups that are not AVAILABLE (an entry was '
            'dropped, added or changed)')
    conditional = [{'obligation_id': g['obligation_id'], 'properties': g['conditional_assumptions']}
                   for g in groups if g.get('conditional_assumptions')]
    if not _same(b['conditional_assumptions'], conditional):
        bad('RET-CONDITIONAL', 'conditional_assumptions is not the list of the groups\' conditional properties')

    complete = status == K.PHASE5_COMPLETE
    verified = bool(items) and all(i['integrity_status'] == 'verified_source' for i in items)
    if b['assurance_status']['satisfied'] != complete:
        bad('RET-STATUS', f"assurance_status.satisfied is {b['assurance_status']['satisfied']} for status {status}")
    if b['assurance_status']['returned_values_verified'] != verified:
        bad('RET-STATUS', 'assurance_status.returned_values_verified does not match the integrity of the items')
    if not iv['passed']:
        if status not in K.PHASE5_NOT_EVALUATED or items or any(g['status'] != status for g in groups):
            bad('RET-STATUS', f'the bundle did not pass independent validation, so it must return no evidence and '
                f'report every obligation as {status}, which must be one of {", ".join(K.PHASE5_NOT_EVALUATED)}')
        return out

    if iv['errors']:
        bad('RET-STATUS', 'independent_validation passed with errors')
    fulfilled = iv['obligations']
    if [(x['obligation_id'], x['mandatory']) for x in fulfilled] != [(g['obligation_id'], g['mandatory'])
                                                                      for g in groups]:
        bad('RET-STATUS', 'independent_validation does not cover exactly the groups')
        return out
    mandatory_ok = bool(fulfilled) and all(x['satisfied'] for x in fulfilled if x['mandatory'])
    if iv['mandatory_fulfilled'] != mandatory_ok:
        bad('RET-STATUS', 'independent_validation.mandatory_fulfilled does not follow from its obligations')
    if any(x['satisfied'] and not (g['status'] == 'AVAILABLE' and g['items']) for x, g in zip(fulfilled, groups)):
        bad('RET-STATUS', 'an obligation is marked satisfied although its group is not AVAILABLE with evidence')
    mandatory = [g for g in groups if g['mandatory']]
    expected = (K.PHASE5_COMPLETE if iv['mandatory_fulfilled'] else 'PARTIAL' if items else
                'UNSUPPORTED' if any(g['status'] == 'UNSUPPORTED' for g in mandatory) else 'UNAVAILABLE')
    if status != expected:
        bad('RET-STATUS', f'status {status} does not follow from the groups and the independent validation '
            f'({expected})')
    if any(g['status'] not in ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE', 'UNSUPPORTED') for g in groups):
        bad('RET-STATUS', 'an evaluated group has a request-level status')
    return out


# ------------------------------------------------------------------ what the review uses

def _view(b, q, groups, iv):
    """An admitted bundle, reduced to what the review and the report use. Nothing here is a claim."""
    by_id = {o['id']: o for o in q.get('obligations', []) if isinstance(o, dict) and isinstance(o.get('id'), str)} \
        if isinstance(q.get('obligations'), list) else {}
    satisfied = {x['obligation_id']: x['satisfied'] for x in iv.get('obligations', [])} if iv['passed'] else {}
    missing = []
    for g in groups:
        # A group counts as missing if the release says so, or if independent validation did not accept it.
        if g['status'] == 'AVAILABLE' and satisfied.get(g['obligation_id'], False):
            continue
        o = by_id.get(g['obligation_id'], {})
        missing.append({'obligation_id': g['obligation_id'], 'family': g['family'], 'mandatory': g['mandatory'],
                        'status': g['status'] if g['status'] != 'AVAILABLE' else 'NOT INDEPENDENTLY FULFILLED',
                        'reason': g['reason'],
                        'object_id': o.get('object_id') if isinstance(o.get('object_id'), str) else None,
                        'selector': o.get('selector') if isinstance(o.get('selector'), dict) else None})
    return {'index': None, 'query_id': b['query_id'], 'status': b['completeness_status'], 'reason': b['reason'],
            'missing': missing, 'conditional': b['conditional_assumptions'],
            'items': [i for g in groups for i in g['items']]}


def _row(index, entry, view, accepted):
    """The report's account of one entry. Rejected entries keep only what could be read safely."""
    b = entry.get('bundle') if isinstance(entry, dict) else None
    q = entry.get('request') if isinstance(entry, dict) else None
    row = {'index': index, 'accepted': accepted, 'query_id': view['query_id'] if view else None,
           'request_sha256': _digest(q) if isinstance(q, dict) else None,
           'bundle_sha256': _digest(b) if isinstance(b, dict) else None,
           'completeness_status': None, 'reason': None, 'citations': [], 'missing_obligations': [],
           'conditional_assumptions': [], 'assurance_status': None, 'limitations': [], 'linked_solutions': []}
    if accepted:
        row.update({
            'completeness_status': b['completeness_status'], 'reason': b['reason'],
            'citations': [{'citation_id': i['citation_id'], 'family': i['family'], 'record_id': i['id'],
                           'original_evidence_ids': list(i['original_evidence_ids']),
                           'integrity_status': i['integrity_status'], 'origin': i['origin']} for i in view['items']],
            'missing_obligations': [{k: m[k] for k in ('obligation_id', 'family', 'mandatory', 'status', 'reason',
                                                       'object_id')} for m in view['missing']],
            'conditional_assumptions': b['conditional_assumptions'],
            'assurance_status': b['assurance_status'], 'limitations': b['limitations']})
    return row


def frames_of(missing):
    """The saved-frame window of a missing obligation, or None (no selector, or simulator labels)."""
    return _frames(missing['selector'])


def _frames(selector):
    if isinstance(selector, dict) and selector.get('kind') == 'frames':
        start, end = selector.get('start'), selector.get('end')
        if _is_int(start) and _is_int(end) and start <= end:
            return start, end
    return None


# ------------------------------------------------------------------ helpers

def _digest(value):
    try:
        return K.digest(value)
    except (TypeError, ValueError):
        return 'not-json'


def _same(a, b):
    """JSON equality with types kept apart (true is not 1), as in the canonical form."""
    try:
        return K.canonical(a) == K.canonical(b)
    except (TypeError, ValueError):
        return False


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _strings(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _describe(scope):
    return ', '.join(f'{k} {scope.get(k)!r}' for k in ('execution_id', 'task_id', 'variant_id'))
