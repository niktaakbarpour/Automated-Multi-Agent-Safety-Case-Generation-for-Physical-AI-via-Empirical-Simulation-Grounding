"""Pure deterministic aggregation of assessed outcomes, never raw evidence."""
from collections import Counter
from .contracts import Applicability as A, Outcome as O


def aggregate(objects):
    rows = tuple(sorted(objects, key=lambda r: r.object_id))
    if len({r.object_id for r in rows}) != len(rows):
        raise ValueError('duplicate_assessment')
    counts = Counter(r.outcome.value for r in rows)
    acounts = Counter(r.applicability.value for r in rows)
    for r in rows:
        if (r.outcome in (O.V, O.N) and r.applicability != A.APPLICABLE or
                r.outcome == O.N and r.coverage.missing or
                r.outcome == O.NA and r.applicability != A.NA):
            raise ValueError('inconsistent_assessment_vector')
    outcome = next((o for o in (O.V, O.IC, O.U, O.N, O.NA) if counts[o.value]), O.NA)
    summary = ('empty_scope' if not rows else 'applicable_present' if acounts[A.APPLICABLE.value]
               else 'indeterminate' if acounts[A.UNKNOWN.value] or acounts[A.IC.value] else 'not_applicable')
    return {'execution_outcome': outcome.value, 'applicability_summary': summary,
            'outcome_counts': {o.value: counts[o.value] for o in O},
            'applicability_counts': {a.value: acounts[a.value] for a in A},
            'evidence_complete': bool(rows) and all(r.complete for r in rows),
            'empty_scope': not rows, 'eligible_safety_units': sum(r.applicability == A.APPLICABLE for r in rows),
            'empirical_metrics': None}
