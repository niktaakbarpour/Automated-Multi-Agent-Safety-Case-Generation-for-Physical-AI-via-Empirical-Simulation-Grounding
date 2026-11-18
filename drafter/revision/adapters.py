"""Adapters propose edits. They never apply one.

An adapter is any object with `name`, `version`, `kind` and
`propose(context) -> {'edits': [...], 'declined': [...]}`. `context` is the
dictionary built by drafter.revision.engine.build_context; it is a private copy,
so an adapter cannot change the request. The host checks every proposed edit
(drafter.revision.edits.edit_issues) and then every invariant, so an adapter is
not trusted, whether it is a template, a scripted reply or a live model.

kind: 'deterministic' (host templates), 'scripted' (a fixed reply, for tests and
offline demonstrations) or 'model' (live inference, attached by the integrator).
"""
from copy import deepcopy

from critic import contract as K

# Template texts say only what holds whenever the template is used: they describe the argument, not
# the evidence or the execution.
GOAL_TEMPLATE = ('R1 remains unresolved for {object_id} across the declared monitoring window. This goal makes '
                 'no claim about the physical outcome for this object.')
UNSUPPORTED_TEMPLATE = ('No supporting argument is recorded under {node_id}, so this claim remains '
                        'unresolved.')
# Unsupported physical inference, unsupported safety conclusion, unsupported guarantee or certification.
OVERCLAIM_CATEGORIES = ('C05', 'C06', 'C12')
# The claimed outcome goes beyond the evidence: the cautious answer is insufficient_information.
CAUTIOUS_CHECKS = ('CONCL-UNSUPPORTED', 'CONCL-NOT-ESTABLISHED', 'CONCL-PARTIAL-COVERAGE', 'CONCL-GAP',
                   'CONCL-OBLIGATION-MISSING', 'CONCL-OBJ-MISSING')
# The claimed outcome disagrees with an admitted checker assessment: only that assessment can correct it.
FOLLOW_CHECKER_CHECKS = ('CONCL-CONTRADICTION', 'CONCL-HIDES-VIOLATION', 'CONCL-APPLICABILITY')


def describe(adapter):
    """{'name', 'version', 'kind'} of an adapter, or ValueError when it does not declare them."""
    info = {key: getattr(adapter, key, None) for key in ('name', 'version', 'kind')}
    if (not all(isinstance(v, str) and v for v in info.values())
            or info['kind'] not in ('deterministic', 'scripted', 'model') or not callable(
                getattr(adapter, 'propose', None))):
        raise ValueError('adapter must declare name, version, kind and propose(context)')
    return info


def _why(entries):
    return ' '.join(f"{e['criticism']['criticism_id']} ({e['criticism']['check_id']}, "
                    f"{e['criticism']['category']} {e['criticism']['category_name']}): "
                    f"{e['criticism']['explanation']}" for e in entries)


class DeterministicAdapter:
    """Template edits only, no model. It rewrites nothing it cannot justify from the finding itself.

    - an approved overclaim finding (C05, C06, C12) on a goal or unresolved claim: the statement is
      replaced by the unresolved wording
    - a goal or strategy without support: an explicit unresolved claim is added under it
    - a broken Solution citation (link repair): the Solution is removed
    - an object outcome beyond the evidence: insufficient_information
    - an object outcome that disagrees with an admitted checker assessment: that assessment's outcome
    - a wrong execution outcome: recomputed by R1 aggregation
    Everything else is declined and stays unresolved.
    """
    name, version, kind = 'deterministic-templates', '0.1.0', 'deterministic'

    def propose(self, context):
        edits, declined, groups = [], [], {}
        for entry in context['findings']:
            op = entry['allowed_ops'][0] if entry['allowed_ops'] else None
            target = entry['target']
            groups.setdefault((op, target['object_id'], target['node_id'] if op != 'set_object_outcome' else None),
                              []).append(entry)

        def decline(entries, reason, note):
            declined.extend({'criticism_id': e['criticism']['criticism_id'], 'reason': reason, 'note': note}
                            for e in entries)

        for (op, object_id, node_id), entries in groups.items():
            ids = [e['criticism']['criticism_id'] for e in entries]
            common = {'finding_ids': ids}
            if op is None:
                decline(entries, 'no_justified_edit', 'No edit is defined for this kind of finding.')
            elif op == 'remove_solution':
                edits.append({'op': op, 'object_id': object_id, 'node_id': node_id, **common,
                              'justification': _why(entries) + ' Edit: the Solution is removed because its '
                              'citation is invalid; no other record is put in its place.'})
            elif op == 'add_unresolved_claim':
                edits.append({'op': op, 'object_id': object_id, 'parent_node_id': node_id,
                              'statement': UNSUPPORTED_TEMPLATE.format(node_id=node_id), **common,
                              'justification': _why(entries) + ' Edit: an explicit unresolved claim is added; '
                              'no evidence is cited for it.'})
            elif op == 'recompute_execution_outcome':
                edits.append({'op': op, **common, 'justification': _why(entries) + ' Edit: the execution '
                              'outcome is recomputed by R1 aggregation of the object outcomes.'})
            elif op == 'set_object_outcome':
                self._outcome(entries, object_id, common, edits, decline)
            elif op == 'replace_statement':
                self._statement(entries, object_id, node_id, common, edits, decline)
        return {'edits': edits, 'declined': declined}

    @staticmethod
    def _outcome(entries, object_id, common, edits, decline):
        wanted = set()
        for e in entries:
            check = e['criticism']['check_id']
            if check in FOLLOW_CHECKER_CHECKS:
                wanted.add(None if e['checker_conflict'] else e['checker_verdict'])
            elif check in CAUTIOUS_CHECKS and e['criticism']['blocking']:
                wanted.add(K.INSUFFICIENT)
            else:
                wanted.add(None)
        value = next(iter(wanted)) if len(wanted) == 1 else None
        allowed = set.intersection(*(set(e['allowed_outcomes']) for e in entries))
        if value is None or value not in allowed or value == entries[0]['current_outcome']:
            decline(entries, 'insufficient_evidence', 'The admitted checker assessments do not settle which '
                    'outcome to write for this object, so the claimed outcome is left as it is.')
            return
        source = ('following the admitted checker assessment' if value != K.INSUFFICIENT
                  else 'because the cited finding shows the claimed outcome is not established')
        edits.append({'op': 'set_object_outcome', 'object_id': object_id, 'outcome': value, **common,
                      'justification': _why(entries) + f' Edit: the outcome becomes {value}, {source}.'})

    @staticmethod
    def _statement(entries, object_id, node_id, common, edits, decline):
        node = entries[0]['node']
        text = GOAL_TEMPLATE.format(object_id=object_id)
        if (node['type'] not in ('goal', 'unresolved_claim')
                or any(e['criticism']['category'] not in OVERCLAIM_CATEGORIES for e in entries)):
            decline(entries, 'no_justified_edit', 'No template can reword this node without adding content '
                    'the evidence does not support.')
        elif ' '.join(node['statement'].split()) == text:
            decline(entries, 'no_justified_edit', 'The node already carries the unresolved wording.')
        else:
            edits.append({'op': 'replace_statement', 'object_id': object_id, 'node_id': node_id,
                          'statement': text, **common,
                          'justification': _why(entries) + ' Edit: the statement is replaced by the unresolved '
                          'wording; the R1 requirement and the node scope are unchanged.'})


class ScriptedAdapter:
    """Returns a fixed proposal. For tests and offline demonstrations, never for results."""
    kind = 'scripted'

    def __init__(self, proposal, name='scripted', version='0'):
        self.proposal, self.name, self.version = proposal, name, version

    def propose(self, context):
        return deepcopy(self.proposal)
