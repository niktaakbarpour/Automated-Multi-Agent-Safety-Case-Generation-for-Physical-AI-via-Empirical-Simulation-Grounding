"""Drafter-wide structural rules and clearly separated host/model prose.

These rules are additional to the shared GSN validator. They do not establish
the truth of free-form model reasoning: all such prose requires explicit review.
"""
import re


REVIEW_LIMITATION = (
    'Graph and reference checks do not verify the scientific correctness '
    'of proposed reasoning. Review the statements before submission.'
)
REVIEW_WARNING = (
    'Unvalidated model prose: human review required. It may contradict the '
    'unresolved structured outcome and does not establish physical safety.'
)
CONCLUSION = 'R1 remains unresolved for all protected objects in the declared window.'


def authoritative_summary(request):
    """Only trusted structure supplies the displayed outcome summary."""
    count = len(request['requirement_configuration']['protected_objects'])
    return (f'R1 remains unresolved for all {count} protected objects in the '
            'declared monitoring window. The supplied evidence does not establish '
            'a verified physical safety outcome. Model reasoning requires review.')


def authoritative_conclusion():
    return CONCLUSION


def authoritative_limitations(request):
    """Caller caveats remain attributed input text, never host conclusions."""
    return list(dict.fromkeys([
        *['Input limitation (unverified text): ' + text for text in request['limitations']],
        REVIEW_LIMITATION, REVIEW_WARNING,
    ]))


def prose_issues(text, path):
    """Catch empty/degenerate prose, not semantic truth or consistency.

The observed single-character 'R' satisfies the old JSON schema. A usable
statement must contain more than a token or a repeated character. This check is
deliberately separate from the constrained decoder's string representation.
"""
    if not isinstance(text, str):
        return ['unusable_prose:' + path]
    normalized = ' '.join(text.split())
    if (len(normalized) < 8 or not re.search(r'[A-Za-z]{2,}', normalized)
            or len(set(normalized.casefold())) < 3):
        return ['unusable_prose:' + path]
    return []


def solution_statement(record):
    """Do not infer missing values or a physical outcome from a reference."""
    return (f"Registry {record['measurement_type']} metadata references "
            f"{record['object_id']} over {record['domain']} interval "
            f"{record['interval'][0]}-{record['interval'][1]} on {record['clock']}. "
            'Original attribution is retained; physical support and falling remain unresolved.')


def graph_structure_issues(value, object_id, *, root_id=None, prefix='argument'):
    """The same graph requirements apply before and after serialization.

``value`` may be a model plan graph or a serialized shared graph. Final shared
graphs do not store root_id, so their single unparented physical goal is inferred.
The shared GSN validator still handles edge typing, cycles and source semantics.
"""
    issues = []
    nodes, edges = value['nodes'], value['edges']
    ids = [node['id'] for node in nodes]
    if len(ids) != len(set(ids)) or any(not key.startswith(object_id + ':') for key in ids):
        issues.append(prefix + '_node_identity:' + object_id)
    by_id = {node['id']: node for node in nodes}
    adjacency = {key: [] for key in ids}
    incoming = set()
    for edge in edges:
        if edge['source'] not in adjacency or edge['target'] not in adjacency:
            issues.append(prefix + '_invalid_edge_endpoint:' + object_id)
            continue
        adjacency[edge['source']].append(edge['target'])
        incoming.add(edge['target'])
    candidates = [n['id'] for n in nodes if n['id'] not in incoming
                  and n['type'] == 'goal' and n['physical_claim']]
    requested_root = root_id if root_id is not None else value.get('root_id')
    if len(candidates) != 1 or (requested_root is not None and candidates != [requested_root]):
        issues.append(prefix + '_physical_root_required:' + object_id)
    else:
        reached, pending = set(), [candidates[0]]
        while pending:
            key = pending.pop()
            if key not in reached:
                reached.add(key)
                pending.extend(adjacency[key])
        if reached != set(ids):
            issues.append(prefix + '_disconnected_nodes:' + object_id)
    if not {'strategy', 'context'} <= {n['type'] for n in nodes}:
        issues.append(prefix + '_strategy_and_context_required:' + object_id)
    for node in nodes:
        if node['physical_claim'] != (node['type'] in ('goal', 'unresolved_claim')):
            issues.append(prefix + '_physical_claim_type:' + node['id'])
        if node['type'] == 'strategy' and not any(
                edge['source'] == node['id'] and edge['type'] == 'supported_by'
                and edge['target'] in by_id
                and by_id[edge['target']]['type'] in ('goal', 'unresolved_claim')
                for edge in edges):
            issues.append(prefix + '_strategy_needs_subclaim:' + node['id'])
        issues.extend(prose_issues(node['statement'], 'node:' + node['id']))
    return sorted(set(issues))


def model_review_issues(argument):
    """A structural acceptance never makes unchecked model prose authoritative."""
    review = argument.get('reasoning_review')
    if not isinstance(review, dict):
        return ['model_prose_review_required']
    issues = []
    if review.get('status') != 'required' or review.get('warning') != REVIEW_WARNING:
        issues.append('model_prose_review_required')
    issues.extend(prose_issues(review.get('summary'), 'model_summary'))
    limits = review.get('limitations')
    if not isinstance(limits, list) or not limits:
        issues.append('model_limitations_required')
    else:
        for index, text in enumerate(limits):
            issues.extend(prose_issues(text, 'model_limitation:' + str(index)))
        if len(limits) != len(set(limits)):
            issues.append('duplicate_model_limitations')
    return issues
