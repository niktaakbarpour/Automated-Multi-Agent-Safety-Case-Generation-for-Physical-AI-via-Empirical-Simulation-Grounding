"""The closed set of edits a revision may make, who may ask for each, and how the host applies them.

An adapter only proposes. Every edit names the findings it answers, the host
checks that those findings allow that kind of edit on that target, and the host
alone writes nodes, provenance, the execution outcome and its statement. An
adapter cannot supply provenance, a node type, an evidence ID or a Solution.
"""
from copy import deepcopy
import re

from critic import checks, contract as K
from critic.llm import RULE_ONLY_CATEGORIES
from drafter.argument_checks import authoritative_conclusion, prose_issues
from . import contract as C

OP_FIELDS = {
    'replace_statement': ('object_id', 'node_id', 'statement'),
    'add_unresolved_claim': ('object_id', 'parent_node_id', 'statement'),
    'remove_solution': ('object_id', 'node_id'),
    'set_object_outcome': ('object_id', 'outcome'),
    'recompute_execution_outcome': (),
}
COMMON_FIELDS = ('op', 'finding_ids', 'justification')
DECLINE_REASONS = ('no_justified_edit', 'insufficient_evidence')
# Categories a model may raise (critic.llm): wording and reasoning. Only these allow a rewrite.
WORDING_CATEGORIES = frozenset(K.CATEGORIES) - frozenset(RULE_ONLY_CATEGORIES)
# Rule findings about one object's claimed outcome (critic.checks.check_conclusions).
OUTCOME_CHECKS = ('CONCL-UNSUPPORTED', 'CONCL-NOT-ESTABLISHED', 'CONCL-CONTRADICTION', 'CONCL-HIDES-VIOLATION',
                  'CONCL-APPLICABILITY', 'CONCL-PARTIAL-COVERAGE', 'CONCL-GAP', 'CONCL-OBLIGATION-MISSING',
                  'CONCL-OBJ-MISSING')
SUPPORTING_TYPES = ('strategy', 'goal', 'solution', 'unresolved_claim')
# A lexical screen, not a semantic check: new text may not contain assurance wording, even negated.
ASSURANCE = re.compile(r'\b(?:guarantee\w*|certif\w*|proves?|proved|proven|proof|safe|safely)\b', re.I)
ORIGIN_BY_ADAPTER_KIND = {'deterministic': 'unresolved_conclusion', 'scripted': 'llm_proposal',
                          'model': 'llm_proposal'}
EDIT_ROLE = 'revision_edit_not_verified_physical_evidence'
# Host texts say only what is true for every bundle they can be written into.
MIXED_CONCLUSION = ('The execution outcome is {outcome} by R1 aggregation of the claimed object outcomes. This '
                    'statement only reports that aggregation. It is not a physical finding and does not show '
                    'that any claimed outcome is supported.')
ORPHAN_CLAIM = ('The evidence link removed from {parent} left it without recorded support, so this claim '
                'remains unresolved.')


def allowed_outcomes(info, object_id):
    """(allowed outcomes, checker verdict, conflict) for one object.

    A revision never writes more than a freshly admitted checker says. An admitted violation cannot be
    replaced by anything else, conflicting assessments allow only insufficient_information, and with no
    admitted assessment nothing else can be claimed.
    """
    admitted = info['admitted'].get(object_id, [])
    verdict, conflict = checks.assessment_verdict(admitted)
    if any(a['outcome'] == K.VIOLATION for a in admitted):
        return [K.VIOLATION], verdict, conflict
    if conflict or verdict is None:
        return [K.INSUFFICIENT], verdict, conflict
    return sorted({verdict, K.INSUFFICIENT}), verdict, conflict


def permitted_ops(row):
    """Edit kinds one classified finding allows. An empty list means no edit is defined for it."""
    target = row['target']
    if row['status'] == C.ACTIONABLE_LINK_REPAIR:
        return ['remove_solution']
    if row['status'] != C.ACTIONABLE or target is None:
        return []
    if row['finding_source'] == 'deterministic':
        if row['check_id'] == 'GSN-UNSUPPORTED-GOAL' and target['kind'] == 'node':
            return ['add_unresolved_claim']
        if row['check_id'] in OUTCOME_CHECKS and target['object_id'] is not None:
            return ['set_object_outcome']
        if row['check_id'] == 'CONCL-AGGREGATION' and target['kind'] == 'execution':
            return ['recompute_execution_outcome']
        if row['check_id'] == C.ABSOLUTE_CLAIM_CHECK and target['kind'] == 'node' and row['node_type'] != 'solution':
            return ['replace_statement']
        if row['check_id'] == C.ABSOLUTE_CLAIM_CHECK and target['kind'] == 'execution':
            # The host rewrites the execution statement whenever it recomputes the outcome.
            return ['recompute_execution_outcome']
        return []
    if target['kind'] == 'node' and row['node_type'] != 'solution' and row['category'] in WORDING_CATEGORIES:
        return ['replace_statement']
    return []


def graph_of(bundle, object_id):
    for item in bundle['graphs']:
        if item['object_id'] == object_id:
            return item['graph']
    return None


def node_of(bundle, object_id, node_id):
    graph = graph_of(bundle, object_id)
    for node in graph['nodes'] if graph is not None else ():
        if node['id'] == node_id:
            return node
    return None


def finding_context(request, classification, info):
    """One entry per actionable finding: everything an adapter needs, and what the host will allow."""
    bundle = request['critic_request']['argument_bundle']
    criticisms = {c['criticism_id']: c for c in request['critic_report']['criticisms']}
    out = []
    for row in classification['findings']:
        if row['status'] not in C.ACTIONABLE_STATUSES:
            continue
        target = row['target']
        entry = {'criticism': deepcopy(criticisms[row['criticism_id']]), 'status': row['status'],
                 'target': deepcopy(target), 'node': None, 'allowed_ops': permitted_ops(row),
                 'allowed_outcomes': None, 'checker_verdict': None, 'checker_conflict': None,
                 'current_outcome': None}
        if target['kind'] == 'node':
            entry['node'] = deepcopy(node_of(bundle, target['object_id'], target['node_id']))
        if 'set_object_outcome' in entry['allowed_ops']:
            allowed, verdict, conflict = allowed_outcomes(info, target['object_id'])
            entry.update(allowed_outcomes=allowed, checker_verdict=verdict, checker_conflict=conflict,
                         current_outcome=bundle['execution_conclusion']['object_outcomes'].get(
                             target['object_id']))
        out.append(entry)
    return out


def proposal_issues(proposal):
    """Shape problems of an adapter answer as a whole."""
    if not isinstance(proposal, dict) or set(proposal) != {'edits', 'declined'}:
        return ['proposal_must_have_exactly_edits_and_declined']
    if not isinstance(proposal['edits'], list) or not isinstance(proposal['declined'], list):
        return ['proposal_edits_and_declined_must_be_lists']
    issues = []
    for index, item in enumerate(proposal['declined']):
        if (not isinstance(item, dict) or set(item) != {'criticism_id', 'reason', 'note'}
                or not isinstance(item['criticism_id'], str) or item['reason'] not in DECLINE_REASONS
                or not isinstance(item['note'], str)):
            issues.append(f'declined_entry_malformed:{index}')
    return issues


def _text_issues(text, current):
    issues = []
    if prose_issues(text, 'edit'):
        issues.append('statement_unusable_prose')
    elif ASSURANCE.search(text):
        issues.append('statement_contains_assurance_wording')
    if current is not None and ' '.join(text.split()) == ' '.join(current.split()):
        issues.append('statement_unchanged')
    return issues


def edit_issues(edit, findings, bundle, taken):
    """Every reason the host refuses one proposed edit.

    findings: {criticism_id: finding_context entry}. taken: {'findings': set, 'targets': set}, filled as
    edits are accepted so that no finding and no target is used twice in a round.
    """
    if not isinstance(edit, dict) or not isinstance(edit.get('op'), str) or edit['op'] not in OP_FIELDS:
        return ['unknown_op']
    op = edit['op']
    if set(edit) != set(COMMON_FIELDS + OP_FIELDS[op]):
        return ['fields_must_be_exactly:' + ','.join(COMMON_FIELDS + OP_FIELDS[op])]
    ids = edit['finding_ids']
    if (not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids)
            or len(ids) != len(set(ids))):
        return ['finding_ids_must_be_a_non_empty_list_of_distinct_ids']
    if not isinstance(edit['justification'], str) or len(edit['justification'].strip()) < 8:
        return ['justification_required']
    for field in OP_FIELDS[op]:
        if not isinstance(edit[field], str) or not edit[field]:
            return ['field_must_be_a_non_empty_string:' + field]
    issues = []
    for i in ids:
        if i not in findings:
            issues.append('finding_not_actionable:' + i)
        elif op not in findings[i]['allowed_ops']:
            issues.append('finding_does_not_allow_this_edit:' + i)
        elif i in taken['findings']:
            issues.append('finding_already_used_by_another_edit:' + i)
    if issues:
        return issues

    object_id = edit.get('object_id')
    node_id = edit.get('node_id', edit.get('parent_node_id'))
    for i in ids:
        target = findings[i]['target']
        if op == 'recompute_execution_outcome':
            continue
        if target['object_id'] != object_id:
            issues.append('edit_object_differs_from_finding_target:' + i)
        elif op != 'set_object_outcome' and (target['kind'] != 'node' or target['node_id'] != node_id):
            issues.append('edit_node_differs_from_finding_target:' + i)
    if issues:
        return issues

    key = (op if op in ('set_object_outcome', 'recompute_execution_outcome') else 'node', object_id, node_id)
    if key in taken['targets']:
        return ['target_already_edited_in_this_round']
    if op in ('replace_statement', 'add_unresolved_claim', 'remove_solution'):
        node = node_of(bundle, object_id, node_id)
        if node is None:
            return ['target_node_missing']
        if op == 'remove_solution' and node['type'] != 'solution':
            issues.append('only_a_solution_can_be_removed')
        if op == 'replace_statement':
            if node['type'] == 'solution':
                issues.append('a_solution_statement_cannot_be_rewritten')
            issues.extend(_text_issues(edit['statement'], node['statement']))
        if op == 'add_unresolved_claim':
            if node['type'] not in ('goal', 'strategy'):
                issues.append('parent_must_be_a_goal_or_strategy')
            issues.extend(_text_issues(edit['statement'], None))
    if op == 'set_object_outcome':
        allowed = None
        for i in ids:
            options = set(findings[i]['allowed_outcomes'] or ())
            allowed = options if allowed is None else allowed & options
        if edit['outcome'] not in allowed:
            issues.append('outcome_not_backed_by_an_admitted_checker_assessment')
        elif edit['outcome'] == bundle['execution_conclusion']['object_outcomes'].get(object_id):
            issues.append('outcome_unchanged')
    if not issues:
        taken['findings'].update(ids)
        taken['targets'].add(key)
    return issues


def provenance(request, adapter, finding_ids, replaced, author):
    """Provenance of a node this revision wrote. The original node stays in the diff and by digest."""
    return {'role': EDIT_ROLE, 'prose_review': 'required', 'revision_schema': C.RESULT_VERSION,
            'revision_id': request['revision_id'], 'round': request['round'],
            'critic_report_sha256': request['critic_report_sha256'], 'finding_ids': list(finding_ids),
            'adapter': adapter['name'] + '/' + adapter['version'], 'author': author,
            'replaces_node_sha256': None if replaced is None else K.digest(replaced)}


def _new_node_id(graph, object_id, round_number):
    ids = {n['id'] for n in graph['nodes']}
    prefix = object_id + ':' if ids and all(i.startswith(object_id + ':') for i in ids) else ''
    number = 1
    while f'{prefix}R{round_number}U{number}' in ids:
        number += 1
    return f'{prefix}R{round_number}U{number}'


def _unresolved_claim(graph, object_id, parent, statement, origin, stamp, request):
    node = {'id': _new_node_id(graph, object_id, request['round']), 'type': 'unresolved_claim',
            'statement': statement, 'scope': deepcopy(parent['scope']), 'provenance': stamp,
            'validation_status': 'unresolved', 'origin': origin, 'evidence_id': None, 'physical_claim': True}
    graph['nodes'].append(node)
    graph['edges'].append({'source': parent['id'], 'target': node['id'], 'type': 'supported_by'})
    return node


def execution_outcome(critic_request, bundle):
    """R1 aggregation over every configured object, in configured order. A missing or invalid object
    outcome counts as insufficient_information, as in critic.checks.check_conclusions."""
    claimed = bundle['execution_conclusion']['object_outcomes']
    return K.execution_outcome([
        claimed[o] if isinstance(claimed.get(o), str) and claimed[o] in K.OUTCOMES else K.INSUFFICIENT
        for o in critic_request['evaluation_context']['protected_objects']])


def conclusion_statement(critic_request, bundle):
    """Host text for the execution conclusion after an outcome changed. Never adapter text."""
    claimed = bundle['execution_conclusion']['object_outcomes']
    roster = critic_request['evaluation_context']['protected_objects']
    if all(claimed.get(o) == K.INSUFFICIENT for o in roster):
        return authoritative_conclusion()
    return MIXED_CONCLUSION.format(outcome=execution_outcome(critic_request, bundle))


def apply(request, edits, adapter):
    """Apply already-accepted edits to a copy of the bundle. Returns (bundle, attribution).

    attribution maps what changed to the index of the edit that caused it, so that every diff entry can
    be traced to its findings. The input request is never modified.
    """
    critic_request = request['critic_request']
    bundle = deepcopy(critic_request['argument_bundle'])
    origin = ORIGIN_BY_ADAPTER_KIND[adapter['kind']]
    by, outcome_edits = {}, []
    for index, edit in enumerate(edits):
        op, object_id, ids = edit['op'], edit.get('object_id'), edit['finding_ids']
        if op == 'replace_statement':
            node = node_of(bundle, object_id, edit['node_id'])
            before = deepcopy(node)
            node.update(statement=edit['statement'], origin=origin,
                        provenance=provenance(request, adapter, ids, before, 'adapter_text'))
            by[('node', object_id, node['id'])] = [index]
        elif op == 'add_unresolved_claim':
            graph = graph_of(bundle, object_id)
            parent = node_of(bundle, object_id, edit['parent_node_id'])
            node = _unresolved_claim(graph, object_id, parent, edit['statement'], origin,
                                     provenance(request, adapter, ids, None, 'adapter_text'), request)
            by[('node', object_id, node['id'])] = [index]
            by[('edge', object_id, (parent['id'], node['id'], 'supported_by'))] = [index]
        elif op == 'remove_solution':
            graph = graph_of(bundle, object_id)
            removed = node_of(bundle, object_id, edit['node_id'])
            parents = [e['source'] for e in graph['edges']
                       if e['target'] == removed['id'] and e['type'] == 'supported_by']
            for e in graph['edges']:
                if removed['id'] in (e['source'], e['target']):
                    by[('edge', object_id, (e['source'], e['target'], e['type']))] = [index]
            graph['edges'] = [e for e in graph['edges'] if removed['id'] not in (e['source'], e['target'])]
            graph['nodes'] = [n for n in graph['nodes'] if n['id'] != removed['id']]
            by[('node', object_id, removed['id'])] = [index]
            types = {n['id']: n['type'] for n in graph['nodes']}
            for parent_id in dict.fromkeys(parents):
                supported = any(e['source'] == parent_id and e['type'] == 'supported_by'
                                and types[e['target']] in SUPPORTING_TYPES for e in graph['edges'])
                if types[parent_id] in ('goal', 'strategy') and not supported:
                    parent = node_of(bundle, object_id, parent_id)
                    node = _unresolved_claim(
                        graph, object_id, parent, ORPHAN_CLAIM.format(parent=parent_id), 'unresolved_conclusion',
                        provenance(request, adapter, ids, removed, 'host_template'), request)
                    by[('node', object_id, node['id'])] = [index]
                    by[('edge', object_id, (parent_id, node['id'], 'supported_by'))] = [index]
        elif op == 'set_object_outcome':
            bundle['execution_conclusion']['object_outcomes'][object_id] = edit['outcome']
            by[('outcome', object_id)] = [index]
            outcome_edits.append(index)
        elif op == 'recompute_execution_outcome':
            outcome_edits.append(index)
    if outcome_edits:
        conclusion = bundle['execution_conclusion']
        conclusion['claimed_outcome'] = execution_outcome(critic_request, bundle)
        conclusion['statement'] = conclusion_statement(critic_request, bundle)
        by[('execution',)] = outcome_edits
    return bundle, by
