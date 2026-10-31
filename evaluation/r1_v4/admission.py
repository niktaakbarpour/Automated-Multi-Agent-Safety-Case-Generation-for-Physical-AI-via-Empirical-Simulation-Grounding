"""Admission of explicit synthetic assumptions and dependencies; no fall detector."""
from collections import defaultdict
import jsonschema
from .configuration import HERE, unsupported_for_object
from .contracts import (Evidence, Frame, Interval, Truth, Validity as V, Uncertainty,
                        Measurement, Geometry, Contact, Camera, Declaration, Admission, freeze)
from .provenance import load
from .manifest import MissingObservation


def parse_evidence(value):
    schema = load(HERE / 'evidence.schema.json')
    validator = jsonschema.Draft202012Validator(schema)
    # Envelope/header failures cannot safely be scoped. Payload failures can.
    validator.validate({**value, 'records': []})
    row_schema = schema['properties']['records']['items']
    header_schema = {k: v for k, v in row_schema.items() if k != 'allOf'}
    for raw in value['records']:
        jsonschema.Draft202012Validator(header_schema).validate(raw)
    records = []
    for r in value['records']:
        p, k = r['payload'], r['kind']
        try:
            jsonschema.Draft202012Validator(row_schema).validate(r)
            payload_invalid = False
        except jsonschema.ValidationError:
            payload_invalid = True
        if payload_invalid:
            payload = Declaration((('invalid_payload', True),))
        elif k in ('direct_measurement', 'derived_observation'):
            payload = Measurement(p['quantity'], tuple(p['values']), p['unit'])
        elif k == 'geometry':
            payload = Geometry(p['shape'], tuple(p['dimensions']), p['static'], p['horizontal'], p['complete'])
        elif k == 'contact':
            payload = Contact(tuple(tuple(pair) for pair in p['pairs']), p['complete'], None if p['forces'] is None else tuple(p['forces']))
        elif k == 'camera':
            payload = Camera(p['camera_id'], tuple(p['indices']), tuple(p['decoded']), tuple(p['inspected']))
        else:
            payload = Declaration(freeze(p))
        records.append(Evidence(r['id'], k, r['claim'], Truth(r['truth']), V.INVALID_LOCAL if payload_invalid else V(r['validity']),
            r['object_id'], r['execution_id'], tuple(sorted(r['surfaces'])), Interval(*r['interval']),
            tuple(sorted(r['cells'])), tuple(sorted(r['dependencies'])), r['source_ref'], r['producer'],
            Frame(**r['frame']), Uncertainty(r['uncertainty']['temporal'], tuple(r['uncertainty']['description'])), payload))
    if len({r.id for r in records}) != len(records):
        raise ValueError('duplicate_evidence_id')
    return tuple(sorted(records, key=lambda r: r.id))


def admit(config, evidence_input, records, registry, cells, interval, model):
    index = {r.id: r for r in records}
    raw = {r['id']: r for r in evidence_input['records']}
    cellmap = {c.id: c for c in cells}
    diagnostics, statuses, source_hashes = {}, {}, {}
    expected_surfaces = config['object_surface_mapping']
    frame = config['coordinate_frames']
    clock = config['temporal_alignment']['clock_ref']
    aliases = defaultdict(list)
    for obj, instance in model['objects'].items():
        aliases[instance].append(obj)
    colliding = {o for names in aliases.values() if len(names) > 1 for o in names}
    def reject(rid, reason, status=V.INVALID_CONTRACT):
        diagnostics.setdefault(rid, []).append(reason)
        # Foundational invalidity dominates uncertainty, never the reverse.
        rank = {V.VERIFIED: 0, V.MISSING: 1, V.INVALID_LOCAL: 2, V.CONTRADICTORY: 3, V.INVALID_CONTRACT: 4}
        if rank[status] > rank.get(statuses.get(rid), -1):
            statuses[rid] = status
    for r in records:
        statuses[r.id] = r.validity
        if r.validity != V.VERIFIED:
            diagnostics.setdefault(r.id, []).append('declared_' + r.validity.value)
        try:
            ledger = registry.resolve(r.source_ref)
            source_hashes[r.id] = registry.bindings[r.source_ref]
            if (ledger.get('synthetic') is not True or ledger.get('execution_id') != config['execution_id']
                    or ledger.get('records', {}).get(r.id) != raw[r.id]):
                reject(r.id, 'source_ledger_mismatch')
        except MissingObservation as e:
            reject(r.id, str(e), V.MISSING)
        except (ValueError, AttributeError) as e:
            reject(r.id, str(e))
        if r.execution_id != config['execution_id'] or r.object_id not in set(config['protected_objects']) | {'*'}:
            reject(r.id, 'execution_object_binding_mismatch')
        if r.object_id == '*' and (r.claim != 'observation' or r.surfaces):
            reject(r.id, 'invalid_global_observation_scope')
        if r.object_id != '*' and r.surfaces != tuple(sorted(expected_surfaces.get(r.object_id, []))):
            reject(r.id, 'surface_scope_mismatch')
        if r.object_id in colliding:
            reject(r.id, 'duplicate_resolved_alias')
        if (r.frame.id != frame['common_frame'] or r.frame.clock != clock or
                r.frame.length_unit != frame['length_unit'] or r.frame.time_unit != frame['time_unit']
                or r.frame.handedness != frame['canonical_handedness']):
            reject(r.id, 'frame_clock_contract_mismatch')
        if not interval.contains(r.interval):
            reject(r.id, 'boundary_censored_or_outside_interval', V.MISSING)
        u = r.uncertainty.temporal
        channel_phase = config['temporal_alignment']['camera_phase_uncertainty_s' if r.kind == 'camera' else 'state_phase_uncertainty_s']
        if u is None or u > 0 or channel_phase is None or channel_phase > 0:
            # This exact analytical profile implements no uncertain phase inference.
            reject(r.id, 'temporal_uncertainty_not_resolved', V.MISSING)
        if r.uncertainty.description:
            reject(r.id, 'unresolved_evidence_uncertainty', V.MISSING)
        if any(c not in cellmap or not r.interval.contains(cellmap[c].interval) for c in r.cells):
            reject(r.id, 'invalid_coverage_cell_binding')
        if r.claim in ('identity', 'presence', 'initial_support') and r.interval != Interval(interval.start, interval.start):
            reject(r.id, 'initial_boundary_not_t0', V.MISSING)
        if r.kind == 'declaration' and r.claim not in {'identity','presence','initial_support','support_link','violation','static_negative','scope_boundary','exclusion'}:
            reject(r.id, 'incompatible_claim_record_kind')
        if r.kind != 'declaration' and r.claim != 'observation' and not (r.kind == 'geometry' and r.claim == 'geometry'):
            reject(r.id, 'raw_observation_cannot_assert_claim')
        if isinstance(r.payload, Camera) and (not set(r.payload.inspected) <= set(r.payload.decoded) <= set(r.payload.indices)):
            reject(r.id, 'invalid_camera_inspection_domain')
        if isinstance(r.payload, Geometry) and (r.payload.shape != 'box' or not r.payload.complete or any(x <= 0 for x in r.payload.dimensions)):
            reject(r.id, 'unsupported_geometry_or_support_profile')
        if r.kind == 'declaration' and not r.payload.get('invalid_payload'):
            p = r.payload
            if r.claim == 'identity' and (r.truth != Truth.TRUE or model['objects'].get(r.object_id) != p.get('instance_id')):
                reject(r.id, 'incompatible_identity_foundation')
            if r.claim == 'presence':
                present = r.object_id in model['objects']
                if r.truth == Truth.FALSE and model['complete_roster'] is not True:
                    reject(r.id, 'absence_roster_incomplete', V.MISSING)
                if r.truth == Truth.TRUE and not present or r.truth == Truth.FALSE and (present or p.get('closed_roster') is not True):
                    reject(r.id, 'invalid_presence_certificate')
            if r.claim == 'initial_support':
                if r.truth == Truth.FALSE and p.get('all_support_excluded') is not True:
                    reject(r.id, 'support_absence_not_established', V.MISSING)
                if r.truth == Truth.TRUE:
                    chain = p.get('chain', ())
                    if len(chain) < 2 or chain[0] != r.object_id or chain[-1] not in r.surfaces or len(set(chain)) != len(chain):
                        reject(r.id, 'invalid_or_cyclic_support_chain', V.MISSING)
            if r.claim == 'violation':
                required = {'origin': 'T', 'loss': 'T', 'downward': 'T', 'handling_excluded': 'F'}
                if any(p.get(k) != v for k, v in required.items()) or r.truth != Truth.TRUE:
                    reject(r.id, 'fall_predicates_not_established', V.MISSING)
                onset, down = p.get('onset', ()), p.get('downward_interval', ())
                if len(onset) == len(down) == 2 and (onset[1] > down[0] or down[0] >= down[1]):
                    reject(r.id, 'fall_phase_order_or_single_frame_unresolved', V.MISSING)
                for key in ('onset', 'downward_interval'):
                    window = p.get(key, ())
                    if len(window) != 2 or not r.interval.contains(Interval(*window)):
                        reject(r.id, 'fall_phase_censored_or_unresolved', V.MISSING)
            if r.claim == 'static_negative' and (p.get('method') != 'exact_static_constraint' or r.truth != Truth.TRUE or not r.cells):
                reject(r.id, 'unsupported_negative_composition', V.MISSING)
            if r.claim == 'exclusion':
                reject(r.id, 'excluded_episode_is_not_negative_coverage', V.MISSING)
        if r.object_id != '*' and r.claim in ('geometry', 'initial_support', 'violation', 'static_negative'):
            for reason in unsupported_for_object(config, r.object_id):
                reject(r.id, reason)
            for root in r.surfaces:
                if model['surfaces'].get(root) != {'shape': 'box', 'static': True, 'horizontal': True, 'complete': True}:
                    reject(r.id, 'unsupported_or_unresolved_root:' + root)
        for dep in r.dependencies:
            if dep not in index:
                reject(r.id, 'missing_dependency:' + dep, V.MISSING)
            elif index[dep].object_id not in (r.object_id, '*'):
                reject(r.id, 'cross_object_dependency_scope')
    # DAG closure: cycle => unresolved, missing => U, invalid essential dependency => IC.
    closures, active = {}, set()
    def visit(rid):
        if rid in closures:
            return closures[rid]
        if rid in active:
            reject(rid, 'dependency_cycle', V.MISSING)
            return {rid}
        active.add(rid)
        result = {rid}
        for dep in index[rid].dependencies:
            if dep in index:
                result |= visit(dep)
        active.remove(rid)
        closures[rid] = result
        return result
    for r in records:
        visit(r.id)
    for r in records:
        for dep in sorted(closures[r.id] - {r.id}):
            if statuses[dep] != V.VERIFIED:
                reject(r.id, 'dependency_not_admitted:' + dep,
                       V.INVALID_CONTRACT if statuses[dep] == V.INVALID_CONTRACT else V.MISSING)
        closure_records = [index[d] for d in closures[r.id] - {r.id}]
        def has(claim, truth=Truth.TRUE):
            return any(d.claim == claim and d.truth == truth and statuses[d.id] == V.VERIFIED for d in closure_records)
        if r.claim in ('initial_support', 'violation', 'static_negative'):
            for claim in ('identity', 'presence', 'geometry'):
                if not has(claim):
                    reject(r.id, 'missing_required_claim:' + claim, V.MISSING)
        if r.claim in ('violation', 'static_negative') and not has('initial_support'):
            reject(r.id, 'missing_initial_support_dependency', V.MISSING)
        if r.claim == 'initial_support' and r.truth == Truth.TRUE:
            chain = r.payload.get('chain', ())
            for child, parent in zip(chain, chain[1:]):
                parents = {d.payload.get('parent') for d in closure_records if d.claim == 'support_link'
                           and statuses[d.id] == V.VERIFIED and d.truth == Truth.TRUE and d.payload.get('child') == child}
                if len(parents) > 1:
                    reject(r.id, 'multiple_parent_load_inference_deferred')
                if not any(d.claim == 'support_link' and statuses[d.id] == V.VERIFIED and d.truth == Truth.TRUE
                           and d.payload.get('child') == child and d.payload.get('parent') == parent for d in closure_records):
                    reject(r.id, 'uncertified_support_link:' + child + ':' + parent, V.MISSING)
    # Semantic rejection above must also propagate to descendants, independent of ID order.
    changed = True
    while changed:
        before = dict(statuses)
        for r in records:
            for dep in closures[r.id] - {r.id}:
                if statuses[dep] != V.VERIFIED:
                    reject(r.id, 'dependency_not_admitted:' + dep,
                           V.INVALID_CONTRACT if statuses[dep] == V.INVALID_CONTRACT else V.MISSING)
        changed = before != statuses
    # Explicit and discovered conflicts are retained; no resolution-by-majority.
    conflicts = []
    for pair in evidence_input['conflicts']:
        if pair['left'] not in index or pair['right'] not in index:
            raise ValueError('conflict_references_missing_record')
        conflicts.append((pair['left'], pair['right'], pair['reason']))
    valid = [r for r in records if statuses[r.id] == V.VERIFIED]
    for i, a in enumerate(valid):
        for b in valid[i+1:]:
            if a.object_id != b.object_id or not a.interval.overlaps(b.interval):
                continue
            opposite = a.claim == b.claim and {a.truth, b.truth} == {Truth.TRUE, Truth.FALSE}
            event_conflict = {a.claim, b.claim} == {'violation', 'static_negative'} and a.truth == b.truth == Truth.TRUE
            if opposite or event_conflict:
                conflicts.append((a.id, b.id, 'admissible_same_claim_or_event_contradiction'))
    for left, right, reason in conflicts:
        if statuses[left] == statuses[right] == V.VERIFIED:
            reject(left, 'unresolved_conflict:' + right + ':' + reason, V.CONTRADICTORY)
            reject(right, 'unresolved_conflict:' + left + ':' + reason, V.CONTRADICTORY)
    # Admission-valid conflicts now propagate through every transitive dependency.
    for r in records:
        for dep in closures[r.id] - {r.id}:
            if statuses[dep] != V.VERIFIED:
                reject(r.id, 'dependency_not_admitted:' + dep,
                       V.INVALID_CONTRACT if statuses[dep] == V.INVALID_CONTRACT else V.MISSING)
    admissions = {r.id: Admission(r.id, statuses[r.id], tuple(sorted(set(diagnostics.get(r.id, [])))),
                                tuple(sorted(closures[r.id])), source_hashes.get(r.id)) for r in records}
    return admissions, tuple(sorted(set(conflicts)))
