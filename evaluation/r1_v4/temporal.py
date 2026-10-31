"""Explicit saved-projection cells; no interpolation or dynamic composition."""
from .contracts import Cell, Interval, Coverage, Validity


def parse_domain(value, config):
    required = {'execution_id', 'axis', 'start', 'end', 'anchors', 'cells'}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError('invalid_domain_fields')
    if value['execution_id'] != config['execution_id'] or value['axis'] != config['monitoring_interval']['axis']:
        raise ValueError('domain_identity_axis_mismatch')
    cells = []
    for row in value['cells']:
        if set(row) != {'id', 'kind', 'start', 'end'} or row['kind'] not in ('snapshot', 'transition'):
            raise ValueError('invalid_cell')
        for key in ('start', 'end'):
            if type(row[key]) not in (int, float):
                raise ValueError('invalid_cell_coordinate')
        if row['start'] > row['end']:
            raise ValueError('reversed_cell')
        cells.append(Cell(row['id'], row['kind'], Interval(row['start'], row['end'])))
    if not cells or len({c.id for c in cells}) != len(cells):
        raise ValueError('empty_or_duplicate_domain_cells')
    snapshots = sorted((c for c in cells if c.kind == 'snapshot'), key=lambda c: c.interval.start)
    if not snapshots or any(c.interval.start != c.interval.end for c in snapshots):
        raise ValueError('invalid_snapshots')
    points = [c.interval.start for c in snapshots]
    if len(set(points)) != len(points):
        raise ValueError('duplicate_snapshot_coordinate')
    transitions = [(c.interval.start, c.interval.end) for c in cells if c.kind == 'transition']
    if sorted(transitions) != list(zip(points, points[1:])):
        raise ValueError('domain_requires_every_transition_cell')
    if value['axis'] == 'saved_frame' and (any(type(x) is not int or x < 0 for x in points) or any(b != a+1 for a, b in zip(points, points[1:]))):
        raise ValueError('noncontiguous_saved_frame_projection')
    if points[0] != value['start'] or points[-1] != value['end']:
        raise ValueError('domain_boundary_mismatch')
    for role in ('start', 'end'):
        boundary = config['monitoring_interval'][role]
        resolved = boundary['value'] if boundary['kind'].startswith('explicit_') else value['anchors'].get(boundary['kind'])
        if resolved is None or resolved != value[role]:
            raise ValueError('unresolved_or_mismatched_boundary:' + role)
    return tuple(sorted(cells, key=lambda c: c.id)), Interval(value['start'], value['end'])


def coverage_for(object_id, records, admissions, cells):
    requested = {c.id for c in cells}
    available, admitted, negative, deps = set(), set(), set(), set()
    groups = {}
    blocked, invalid = set(), set()
    for r in records:
        if r.object_id != object_id:
            continue
        a = admissions[r.id]
        available.update(r.cells)
        if r.claim == 'scope_boundary':
            blocked.update(c.id for c in cells if c.interval.end >= r.interval.start)
        if a.status != Validity.VERIFIED:
            if a.status in (Validity.INVALID_CONTRACT, Validity.INVALID_LOCAL):
                invalid.update(r.cells)
            if r.claim in ('static_negative', 'violation', 'scope_boundary'):
                blocked.update(r.cells)
            continue
        admitted.update(r.cells)
        if r.claim == 'scope_boundary':
            blocked.update(c.id for c in cells if c.interval.end >= r.interval.start)
        if r.claim == 'static_negative' and r.truth.value == 'T':
            negative.update(r.cells)
            deps.update(a.dependencies)
            groups.setdefault(r.producer, set()).add(r.source_ref)
    negative -= blocked
    return Coverage(tuple(sorted(requested)), tuple(sorted(available & requested)),
                    tuple(sorted(admitted & requested)), tuple(sorted(negative & requested)),
                    tuple(sorted(requested - negative)), tuple(sorted(deps)),
                    tuple((p, tuple(sorted(refs))) for p, refs in sorted(groups.items())), tuple(sorted(invalid & requested)),
                    tuple(sorted(requested - available)))
