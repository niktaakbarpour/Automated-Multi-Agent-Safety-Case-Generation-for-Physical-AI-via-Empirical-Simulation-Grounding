"""Decoder-compatible plan constraints and separate authoritative text checks.

The server schema is a generation aid, not a substitute for shared GSN validation.
In particular, declared-node relationships and evidence scope are checked in Python.
"""
from copy import deepcopy
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent


def build_plan_schema(request):
    """Restrict identifiers without the incompatible text regex/uniqueItems pair.

    XGrammar 0.1.25 treats a string pattern as a complete-string grammar. Therefore
    human text deliberately has no regex. Identifier regexes are anchored and use
    explicit repetition; they never use a substring-search expression.
    """
    schema = json.loads((HERE / 'schemas' / 'graph_plan.schema.json').read_text())
    roster = request['requirement_configuration']['protected_objects']
    graphs = schema['properties']['graphs']
    graphs['minItems'] = graphs['maxItems'] = len(roster)
    graph = graphs['items']['properties']
    graph['object_id'] = {'enum': deepcopy(roster)}
    # An evidence identity such as ev:<hash> is not a graph endpoint. The declared
    # node existence and exact per-object namespace are still host-side checks.
    namespace = '|'.join(re.escape(value) for value in roster)
    schema['$defs']['node_id'] = {
        'type': 'string',
        'pattern': '^(?:' + namespace + '):[A-Za-z0-9_.:-]{1,128}$',
    }
    for target in (graph, graph['nodes']['items']['properties'],
                   graph['edges']['items']['properties']):
        for key in ('root_id', 'id', 'source', 'target'):
            if key in target:
                target[key] = {'$ref': '#/$defs/node_id'}
    node = graph['nodes']['items']
    eligible = request['evidence_handling']['graph_eligible_evidence_ids']
    variants = []
    for kinds, physical in (
        (['goal', 'unresolved_claim'], True),
        (['strategy', 'context', 'assumption', 'justification', 'defeater'], False),
    ):
        variant = deepcopy(node)
        props = variant['properties']
        props['type'] = {'enum': kinds}
        props['physical_claim'] = {'const': physical}
        props['evidence_id'] = {'type': 'null'}
        variants.append(variant)
    if eligible:
        solution = deepcopy(node)
        props = solution['properties']
        props['type'] = {'enum': ['solution']}
        props['physical_claim'] = {'const': False}
        props['evidence_id'] = {'enum': deepcopy(eligible)}
        variants.append(solution)
    # Complete shapes, rather than conditionals interpreted inconsistently by
    # decoders, prevent null Solution citations and citations on reasoning nodes.
    # A missing eligible catalogue simply omits the Solution alternative.
    graph['nodes']['items'] = {'anyOf': variants}
    Draft202012Validator.check_schema(schema)
    return schema


def validate_plan_prose(plan):
    """Reject unusable prose and duplicates independently of decoder support.

    This is a usability check, not a claim that arbitrary language is factually
    correct. The output also carries explicit review status for model reasoning.
    Call after the plan schema has validated its shape.
    """
    from .argument_checks import prose_issues
    from .validation import ContractError

    issues = []
    issues.extend(prose_issues(plan['summary'], 'plan/summary'))
    for index, value in enumerate(plan['limitations']):
        issues.extend(prose_issues(value, f'plan/limitations/{index}'))
    if len(plan['limitations']) != len(set(plan['limitations'])):
        issues.append('plan_duplicate_limitations')
    for graph_index, graph in enumerate(plan['graphs']):
        for node_index, node in enumerate(graph['nodes']):
            issues.extend(prose_issues(node['statement'],
                                      f'plan/graphs/{graph_index}/nodes/{node_index}/statement'))
    if issues:
        raise ContractError(issues)


def serialized_graph_issues(graph, object_id, request):
    """Apply the same plan shape limits to standalone serialized graphs.

    This is a validation projection only; it never changes the supplied graph.
    The unparented physical root is also independently checked by shared rules.
    """
    full = build_plan_schema(request)
    schema = {**deepcopy(full['properties']['graphs']['items']), '$defs': full['$defs']}
    incoming = {edge['target'] for edge in graph['edges']}
    roots = [node['id'] for node in graph['nodes'] if node['id'] not in incoming
             and node['type'] == 'goal' and node['physical_claim']]
    value = {'object_id': object_id, 'root_id': roots[0] if len(roots) == 1 else None,
             'nodes': [{key: node[key] for key in ('id', 'type', 'statement', 'evidence_id', 'physical_claim')}
                       for node in graph['nodes']], 'edges': graph['edges']}
    return ['argument_plan_schema:' + object_id + ':' + '/'.join(map(str, error.absolute_path))
            for error in Draft202012Validator(schema).iter_errors(value)]
