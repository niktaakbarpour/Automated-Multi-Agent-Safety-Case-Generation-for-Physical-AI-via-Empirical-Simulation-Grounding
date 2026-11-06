"""Verify analytical checker results by replaying their hash-bound source input.

Result hashes establish consistency, not producer authenticity. Only the existing
synthetic analytical route is supported; this never enables empirical admission.
The authoritative checker owns admission, dependency and aggregation semantics.
"""
import copy

from . import contract as K


def problems(item):
    source = item.get('input_bundle')
    if not isinstance(source, dict) or set(source) != {'configuration', 'artifacts', 'evidence'}:
        return ['input_bundle must contain the original configuration, artifacts and evidence; '
                'a result alone cannot establish source or dependency admission']
    try:
        if K.canonical(source['configuration']) != K.canonical(item['configuration']):
            return ['input_bundle.configuration differs from the supplied checker configuration']
        if K.digest(source) != item['result']['provenance'].get('input_hash'):
            return ['input_bundle does not match the checker provenance.input_hash']
    except (ValueError, TypeError, OverflowError, RecursionError):
        return ['input_bundle must be finite canonical JSON']
    # No artifact paths are opened: runtime.assess resolves its explicit inline,
    # hash-bound analytical registry. Missing dependencies fail closed.
    try:
        from evaluation.r1_v4.runtime import assess
        expected = assess(copy.deepcopy(source))
    except (ImportError, OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        return [f'authoritative checker replay unavailable: {type(exc).__name__}: {exc}']
    if K.canonical(expected) == K.canonical(item['result']):
        return []
    fields = sorted(k for k in set(expected) | set(item['result'])
                    if K.canonical(expected.get(k)) != K.canonical(item['result'].get(k)))
    details = ['checker replay differs in ' + ', '.join(fields)]
    for row in expected.get('evidence_admission', []):
        if row['status'] != 'verified':
            details.append(f"{row['evidence_id']}: {row['status']}: " + ', '.join(row['reasons']))
    details.extend(expected.get('missing_requirements', []))
    return details
