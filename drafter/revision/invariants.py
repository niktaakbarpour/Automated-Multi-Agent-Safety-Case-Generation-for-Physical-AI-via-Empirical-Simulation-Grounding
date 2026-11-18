"""Checks on a revised bundle that do not trust the code that produced it.

The diff is computed from the two bundles alone. Every entry must then be traced
to an accepted edit and must be a kind of change a revision is allowed to make.
After that the existing validators run on the revised request: the Critic input
checks, the shared GSN validator and the Drafter structural rules. Passing them
is structural acceptance only. None of them shows that a statement is true.
"""
from collections import Counter
from copy import deepcopy
from types import SimpleNamespace

from critic import contract as K
from drafter.argument_checks import graph_structure_issues
from evaluation.r1_v4.evidence_registry_gsn.gsn import Edge, Graph, Node
from . import contract as C, edits as E

# drafter.validation.validate_argument_bundle does not send larger graphs into the shared validator,
# whose cycle search is recursive and unbounded. The same bound is used here.
MAX_NODES, MAX_EDGES = 24, 80
FROZEN_CONTEXT = ('requirement_id', 'requirement_version', 'execution_id', 'benchmark', 'task_id',
                  'model_checkpoint', 'variant_id', 'r1_configuration_sha256', 'protected_objects',
                  'support_surfaces', 'monitored_interval', 'contract_versions')
WRITTEN_FIELDS = {'statement', 'origin', 'provenance'}
PROVENANCE_KEYS = {'role', 'prose_review', 'revision_schema', 'revision_id', 'round', 'critic_report_sha256',
                   'finding_ids', 'adapter', 'author', 'replaces_node_sha256'}


def _edge_key(edge):
    return (edge.get('source'), edge.get('target'), edge.get('type'))


def _kept_in_order(before, after):
    """True when the items that survive keep their order and every new item comes after them."""
    kept = [x for x in after if x in before]
    return kept == [x for x in before if x in after] and after[:len(kept)] == kept


def compare(original, revised):
    """Node-level diff of two argument bundles, computed from the bundles alone.

    Anything a revision is never allowed to touch shows up as an 'unauthorised_change' entry.
    """
    diff = []

    def entry(change, object_id=None, node_id=None, field=None, before=None, after=None):
        diff.append({'change': change, 'object_id': object_id, 'node_id': node_id, 'field': field,
                     'before': deepcopy(before), 'after': deepcopy(after),
                     'before_sha256': None if before is None else K.digest(before),
                     'after_sha256': None if after is None else K.digest(after), 'edit_indexes': []})

    for key in sorted(set(original) | set(revised)):
        if key not in ('graphs', 'execution_conclusion') and original.get(key) != revised.get(key):
            entry('unauthorised_change', field=key, before=original.get(key), after=revised.get(key))
    roster = [item.get('object_id') for item in original['graphs']]
    if [item.get('object_id') for item in revised['graphs']] != roster:
        entry('unauthorised_change', field='graphs')
        return diff
    for old, new in zip(original['graphs'], revised['graphs']):
        object_id = old['object_id']
        if set(old) != set(new) or set(old['graph']) != set(new['graph']):
            entry('unauthorised_change', object_id, field='graph')
            continue
        for key in sorted(set(old['graph']) - {'nodes', 'edges'}):
            if old['graph'][key] != new['graph'][key]:
                entry('unauthorised_change', object_id, field='graph.' + key,
                      before=old['graph'][key], after=new['graph'][key])
        before = {n['id']: n for n in old['graph']['nodes']}
        after = {n['id']: n for n in new['graph']['nodes']}
        if len(before) != len(old['graph']['nodes']) or len(after) != len(new['graph']['nodes']):
            entry('unauthorised_change', object_id, field='graph.nodes.duplicate_id')
            continue
        for node_id, node in before.items():
            if node_id not in after:
                entry('node_removed', object_id, node_id, before=node)
            elif after[node_id] != node:
                entry('node_replaced', object_id, node_id, before=node, after=after[node_id])
        for node_id, node in after.items():
            if node_id not in before:
                entry('node_added', object_id, node_id, after=node)
        if not _kept_in_order(list(before), list(after)):
            entry('unauthorised_change', object_id, field='graph.nodes.order')
        old_edges = [_edge_key(e) for e in old['graph']['edges']]
        new_edges = [_edge_key(e) for e in new['graph']['edges']]
        if (len(set(old_edges)) != len(old_edges) or len(set(new_edges)) != len(new_edges)
                or any(set(e) != {'source', 'target', 'type'} for e in new['graph']['edges'])):
            entry('unauthorised_change', object_id, field='graph.edges.shape')
            continue
        for edge in old['graph']['edges']:
            if _edge_key(edge) not in new_edges:
                entry('edge_removed', object_id, field='edge', before=edge)
        for edge in new['graph']['edges']:
            if _edge_key(edge) not in old_edges:
                entry('edge_added', object_id, field='edge', after=edge)
        if not _kept_in_order(old_edges, new_edges):
            entry('unauthorised_change', object_id, field='graph.edges.order')

    old, new = original['execution_conclusion'], revised['execution_conclusion']
    for key in sorted((set(old) | set(new)) - {'object_outcomes', 'claimed_outcome', 'statement'}):
        if old.get(key) != new.get(key):
            entry('unauthorised_change', field='execution_conclusion.' + key)
    for object_id in sorted(set(old['object_outcomes']) | set(new['object_outcomes'])):
        if old['object_outcomes'].get(object_id) != new['object_outcomes'].get(object_id):
            entry('object_outcome_changed', object_id, field='object_outcomes',
                  before=old['object_outcomes'].get(object_id), after=new['object_outcomes'].get(object_id))
    if old['claimed_outcome'] != new['claimed_outcome']:
        entry('execution_outcome_changed', field='claimed_outcome',
              before=old['claimed_outcome'], after=new['claimed_outcome'])
    if old['statement'] != new['statement']:
        entry('execution_statement_changed', field='statement', before=old['statement'], after=new['statement'])
    return diff


def attribute(diff, by):
    """Link each diff entry to the edits that caused it (see edits.apply). Unlinked entries stay empty."""
    for d in diff:
        if d['change'] in ('node_replaced', 'node_added', 'node_removed'):
            key = ('node', d['object_id'], d['node_id'])
        elif d['change'] in ('edge_added', 'edge_removed'):
            key = ('edge', d['object_id'], _edge_key(d['after'] or d['before']))
        elif d['change'] == 'object_outcome_changed':
            key = ('outcome', d['object_id'])
        elif d['change'] in ('execution_outcome_changed', 'execution_statement_changed'):
            key = ('execution',)
        else:
            key = None
        d['edit_indexes'] = list(by.get(key, []))
    return diff


def _written_node_issues(request, node, replaced, entry, edits, removed_digests):
    """A node this revision wrote must carry exactly the host's revision provenance."""
    where = f"{entry['object_id']}:{entry['node_id']}"
    stamp = node.get('provenance')
    if not isinstance(stamp, dict) or set(stamp) != PROVENANCE_KEYS:
        return ['written_node_provenance_shape:' + where]
    issues = []
    expected_ids = edits[entry['edit_indexes'][0]]['finding_ids'] if len(entry['edit_indexes']) == 1 else None
    if (stamp['role'] != E.EDIT_ROLE or stamp['prose_review'] != 'required'
            or stamp['revision_schema'] != C.RESULT_VERSION or stamp['revision_id'] != request['revision_id']
            or stamp['round'] != request['round']
            or stamp['critic_report_sha256'] != request['critic_report_sha256']
            or stamp['finding_ids'] != expected_ids or not stamp['finding_ids']
            or stamp['author'] not in ('adapter_text', 'host_template')):
        issues.append('written_node_provenance_binding:' + where)
    if replaced is not None and stamp['replaces_node_sha256'] != K.digest(replaced):
        issues.append('written_node_does_not_reference_the_node_it_replaces:' + where)
    if replaced is None and stamp['replaces_node_sha256'] not in (None, *removed_digests):
        issues.append('written_node_references_an_unknown_node:' + where)
    if node.get('origin') not in set(E.ORIGIN_BY_ADAPTER_KIND.values()):
        issues.append('written_node_origin:' + where)
    return issues


def diff_rule_issues(request, revised, diff, edits, info):
    """Every way the diff breaks the rules of what a revision may change."""
    critic_request = request['critic_request']
    issues = []
    added = {(d['object_id'], d['node_id']) for d in diff if d['change'] == 'node_added'}
    removed = {(d['object_id'], d['node_id']) for d in diff if d['change'] == 'node_removed'}
    removed_digests = [d['before_sha256'] for d in diff if d['change'] == 'node_removed']
    for d in diff:
        change, object_id = d['change'], d['object_id']
        where = f"{change}:{object_id}:{d['node_id'] or d['field']}"
        if change == 'unauthorised_change':
            issues.append(f"unauthorised_change:{object_id}:{d['field']}")
            continue
        if not d['edit_indexes'] or any(not edits[i]['finding_ids'] or not edits[i]['justification'].strip()
                                        for i in d['edit_indexes']):
            issues.append('change_without_finding_and_justification:' + where)
            continue
        before, after = d['before'], d['after']
        if change == 'node_replaced':
            touched = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
            if not touched <= WRITTEN_FIELDS:
                issues.append('protected_node_field_changed:' + where + ':'
                              + ','.join(sorted(touched - WRITTEN_FIELDS)))
            if before['type'] == 'solution':
                issues.append('solution_node_modified:' + where)
            if before['statement'] == after.get('statement'):
                issues.append('replaced_node_statement_unchanged:' + where)
            issues.extend(_written_node_issues(request, after, before, d, edits, removed_digests))
        elif change == 'node_added':
            graph = E.graph_of(revised, object_id)
            parents = [e['source'] for e in graph['edges']
                       if e['target'] == d['node_id'] and e['type'] == 'supported_by']
            parent = E.node_of(revised, object_id, parents[0]) if len(parents) == 1 else None
            if (after.get('type') != 'unresolved_claim' or after.get('physical_claim') is not True
                    or after.get('validation_status') != 'unresolved' or after.get('evidence_id') is not None):
                issues.append('only_an_unresolved_claim_may_be_added:' + where)
            if parent is None or after.get('scope') != parent['scope']:
                issues.append('added_node_scope_must_equal_its_single_parent:' + where)
            issues.extend(_written_node_issues(request, after, None, d, edits, removed_digests))
        elif change == 'node_removed':
            if before['type'] != 'solution':
                issues.append('only_a_solution_may_be_removed:' + where)
        elif change == 'edge_added':
            if after['type'] != 'supported_by' or (object_id, after['target']) not in added:
                issues.append('edge_added_outside_a_new_unresolved_claim:' + where)
        elif change == 'edge_removed':
            if (object_id, before['source']) not in removed and (object_id, before['target']) not in removed:
                issues.append('edge_removed_without_its_solution:' + where)
        elif change == 'object_outcome_changed':
            if (object_id not in critic_request['evaluation_context']['protected_objects']
                    or after not in E.allowed_outcomes(info, object_id)[0]):
                issues.append('outcome_not_backed_by_an_admitted_checker_assessment:' + where)
    conclusion = revised['execution_conclusion']
    if any(d['change'].startswith(('object_outcome', 'execution_')) for d in diff):
        if conclusion['claimed_outcome'] != E.execution_outcome(critic_request, revised):
            issues.append('execution_outcome_is_not_the_r1_aggregation')
        if conclusion['statement'] != E.conclusion_statement(critic_request, revised):
            issues.append('execution_statement_is_not_host_text')
    return sorted(set(issues))


def frozen_issues(original, revised):
    """Everything in the Critic request except the bundle and the request ID must be untouched."""
    issues = ['frozen_field_changed:' + key for key in sorted(set(original) | set(revised))
              if key not in ('argument_bundle', 'request_id') and original.get(key) != revised.get(key)]
    old, new = original['evaluation_context'], revised.get('evaluation_context')
    new = new if isinstance(new, dict) else {}
    issues += ['frozen_context_changed:' + key for key in FROZEN_CONTEXT if old.get(key) != new.get(key)]
    try:
        if K.digest(new.get('r1_configuration')) != old['r1_configuration_sha256']:
            issues.append('r1_configuration_digest_mismatch')
    except (ValueError, TypeError, OverflowError, RecursionError):
        issues.append('r1_configuration_digest_mismatch')
    return issues


def gsn_issues(critic_request, bundle):
    """Run the shared gsn.Graph.validate on every graph. Returns (issues, graphs not run).

    The registry view holds the request's own records, read-only. They were already checked by the
    Critic input checks; the shared Record.parse is not used because it refuses the synthetic source
    paths of labelled test fixtures.
    """
    records = tuple(SimpleNamespace(**r) for r in critic_request['evidence_package']['records'])
    registry = SimpleNamespace(records=lambda: records)
    issues, skipped = [], []
    for item in bundle['graphs']:
        graph = item['graph']
        if len(graph['nodes']) > MAX_NODES or len(graph['edges']) > MAX_EDGES:
            skipped.append(item['object_id'])
            continue
        try:
            Graph(tuple(Node(**n) for n in graph['nodes']), tuple(Edge(**e) for e in graph['edges']),
                  graph['schema_version']).validate(registry)
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
            issues.append(f"{item['object_id']}:{type(error).__name__}:{error}")
    return issues, skipped


def structure_issues(original, revised):
    """Drafter structural issues the revision introduced. Issues the original already had are not new."""
    issues = []
    for old, new in zip(original['graphs'], revised['graphs']):
        try:
            before = set(graph_structure_issues(old['graph'], old['object_id']))
            issues += [i for i in graph_structure_issues(new['graph'], new['object_id']) if i not in before]
        except (KeyError, TypeError, AttributeError) as error:
            issues.append(f"{old['object_id']}:{type(error).__name__}")
    return issues


def rule_issues(findings_before, findings_after, info_after, cited):
    """(input issues, new rule findings, cited rule findings that did not clear).

    Findings are matched by check, category, object and node; counts matter, because one object can
    carry the same kind of finding twice.
    """
    invalid = [f"{f['check_id']}:{f['object_id']}:{f['node_id']}" for f in findings_after
               if f['phase'] == 'validation'] if not info_after['input_valid'] else []
    before = Counter(C.fingerprint(f) for f in findings_before)
    after = Counter(C.fingerprint(f) for f in findings_after)
    new = sorted(':'.join(map(str, fp)) for fp in after if after[fp] > before[fp])
    wanted = Counter(C.fingerprint(f) for f in cited)
    stuck = sorted(':'.join(map(str, fp)) for fp in wanted if after[fp] > before[fp] - wanted[fp])
    return invalid, new, stuck
