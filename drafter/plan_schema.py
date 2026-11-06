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
    template = graphs.pop('items')
    records = {record['id']: record for record in request['evidence_package']['records']}
    eligible = set(request['evidence_handling']['graph_eligible_evidence_ids'])
    # Encode the existing ordered-roster contract before sampling. Tuple positions
    # are not a sorting instruction and never mutate a returned model response.
    graphs['prefixItems'] = []
    graphs['items'] = False
    for object_id in roster:
        graph_schema = deepcopy(template)
        graph = graph_schema['properties']
        graph['object_id'] = {'const': object_id}
        node_id = {'type': 'string',
                   'pattern': '^' + re.escape(object_id) + ':[A-Za-z0-9_.:-]{1,128}$'}
        for target in (graph, graph['nodes']['items']['properties'],
                       graph['edges']['items']['properties']):
            for key in ('root_id', 'id', 'source', 'target'):
                if key in target:
                    target[key] = deepcopy(node_id)
        node = graph['nodes']['items']
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
        object_evidence = sorted(key for key in eligible
                                 if key in records and records[key]['object_id'] == object_id)
        if object_evidence:
            solution = deepcopy(node)
            props = solution['properties']
            props['type'] = {'enum': ['solution']}
            props['physical_claim'] = {'const': False}
            props['evidence_id'] = {'enum': object_evidence}
            variants.append(solution)
        graph['nodes']['items'] = {'anyOf': variants}
        graphs['prefixItems'].append(graph_schema)
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
    position = request['requirement_configuration']['protected_objects'].index(object_id)
    schema = {**deepcopy(full['properties']['graphs']['prefixItems'][position]), '$defs': full['$defs']}
    incoming = {edge['target'] for edge in graph['edges']}
    roots = [node['id'] for node in graph['nodes'] if node['id'] not in incoming
             and node['type'] == 'goal' and node['physical_claim']]
    value = {'object_id': object_id, 'root_id': roots[0] if len(roots) == 1 else None,
             'nodes': [{key: node[key] for key in ('id', 'type', 'statement', 'evidence_id', 'physical_claim')}
                       for node in graph['nodes']], 'edges': graph['edges']}
    return ['argument_plan_schema:' + object_id + ':' + '/'.join(map(str, error.absolute_path))
            for error in Draft202012Validator(schema).iter_errors(value)]
