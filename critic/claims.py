"""Narrow rule for unsupported absolute safety claims (M4 task A3).

R1 has five outcomes. The strongest negative one is
no_violation_observed_within_validated_coverage: a qualified result, limited to
the validated coverage of an admitted checker assessment. No R1 outcome, and no
supplied evidence, supports an unconditional guarantee that an object or the
robot "is safe". This rule flags statements that make such a guarantee and asks
for admitted evidence. It never declares a violation and never changes an
outcome.

It is a lexical rule over clauses, not a semantic classifier. It looks only for
three shapes:

- an assurance word (guaranteed, certified, proven, assured) together with a
  safety word (safe, safety, risk-free) in the same clause,
- an absolute safety phrase (completely safe, always safe, 100% safe, zero risk,
  risk-free, ...), and
- a plain assertion that something is or was safe ("was safe", "remained
  safe"). R1 has no "safe" outcome, and insufficient or unassessed evidence is
  never physical safety.

A clause with a negation before the match ("does not establish that it is
safe", "no guarantee of safety") is not flagged. Everything else, including an
empirical claim such as "it never fell", is left to the other checks and to the
model review. Because it is lexical, every finding asks for human review.
"""
import re

RULE_VERSION = 'absolute-safety-claim/1.0.0'
CHECK_ID = 'CLAIM-ABSOLUTE-SAFETY'
SPEC_REF = 'requirements/r1_generalized_v2/FORMAL_SEMANTICS.md#coverage-and-object-outcome'

# A consequence after a comma ("..., so it was safe") starts a new clause, so that an earlier cautious word
# cannot hide a later unqualified conclusion.
_CLAUSE = re.compile(r'[.;:!?\n]|\b(?:but|however|although|though|whereas|yet|while)\b'
                     r'|,\s*(?:and\s+)?(?:so|thus|hence|therefore|consequently)\b', re.I)
_ASSURANCE = (r'\b(?:guarantee[ds]?|guaranteeing|certified|certifies|certify|certification|proven|proves?|proved'
              r'|assured?)\b')
_SAFETY = r'\b(?:safe|safely|safety|risk[- ]free|hazard[- ]free|harmless)\b'
_ABSOLUTE = (r'\b(?:completely|fully|perfectly|absolutely|entirely|totally|always|unconditionally|inherently)\s+'
             r'(?:physically\s+)?(?:safe|safely)\b'
             r'|\b100\s*(?:%|percent)\s+safe\b|\b(?:zero|no)\s+risk\b|\brisk[- ]free\b|\bhazard[- ]free\b'
             r'|\b(?:is|was|were|are|be|been|being|remain(?:s|ed)?|stay(?:s|ed)?|kept)\s+'
             r'(?:(?:therefore|thus|hence|still|also|clearly|definitely|certainly|physically|fully)\s+)*'
             r'safe\b(?!\s+to\s+(?:say|assume))')
_NEGATION = re.compile(r"\b(?:not|no|never|cannot|neither|nor|without|unable|unresolved|unknown|insufficient|"
                       r"unestablished|unverified|unsupported)\b|n't\b", re.I)


def absolute_safety_phrase(text):
    """The first unnegated absolute safety claim in text, or None."""
    if not isinstance(text, str):
        return None
    for clause in _CLAUSE.split(text):
        for match in _matches(clause):
            if not _NEGATION.search(clause[:match.start()]):
                return ' '.join(clause.split()).rstrip(',')
    return None


def _matches(clause):
    found = list(re.finditer(_ABSOLUTE, clause, re.I))
    assurance = list(re.finditer(_ASSURANCE, clause, re.I))
    if assurance and re.search(_SAFETY, clause, re.I):
        found += assurance
    return sorted(found, key=lambda m: m.start())


def check_absolute_claims(req, admitted, finding):
    """Findings for every node and execution statement that makes an unconditional safety guarantee.

    admitted: {object_id: [admitted checker assessments]} from check_assessments.
    finding:  checks.finding, passed in to avoid a circular import.
    """
    out = []
    ctx, bundle = req['evaluation_context'], req['argument_bundle']
    monitored = ctx['monitored_interval'].get('interval')
    interval = list(monitored) if isinstance(monitored, list) else None

    def flag(object_id, node_id, where, statement, clause):
        available = admitted.get(object_id, []) if object_id is not None else \
            [a for found in admitted.values() for a in found]
        if available:
            outcomes = sorted({a['outcome'] for a in available})
            status = (f'{len(available)} admitted checker assessment(s) are supplied ({", ".join(outcomes)}); '
                      'even a no-violation result supports only no_violation_observed_within_validated_coverage, '
                      'a result limited to its validated coverage, not a guarantee.')
        else:
            status = 'No admitted checker assessment is supplied for it.'
        scope = f'object {object_id}' if object_id is not None else 'this execution'
        out.append(finding(
            CHECK_ID, 'C12',
            f'{where} states "{statement}". The clause "{clause}" is an unqualified claim of safety. R1 v2 has '
            'no outcome that guarantees safety, and the evidence package cannot establish one. ' + status,
            f'Replace the guarantee with a statement limited to what admitted evidence establishes for {scope}, '
            'or keep the claim unresolved, and supply an admitted checker assessment if a definite outcome is '
            'intended. This finding does not say a violation occurred.',
            object_id=object_id, node_id=node_id, requirement_refs=[SPEC_REF, RULE_VERSION],
            additional_evidence_needed=True, human_review_required=True,
            evidence_request={'object_id': object_id, 'measurement_type': 'checker_assessment',
                              'interval': interval,
                              'reason': f'An admitted R1 checker assessment is needed before any definite claim '
                                        f'about {scope}; a guarantee of safety cannot be supported by any.'}))

    for item in bundle['graphs']:
        object_id, graph = item.get('object_id'), item.get('graph')
        nodes = graph.get('nodes') if isinstance(graph, dict) else None
        for node in nodes if isinstance(nodes, list) else []:
            if not isinstance(node, dict) or not isinstance(node.get('id'), str):
                continue
            clause = absolute_safety_phrase(node.get('statement'))
            if clause:
                flag(object_id if isinstance(object_id, str) else None, node['id'],
                     f"Node {node['id']} ({node.get('type')})", node['statement'], clause)
    conclusion = bundle['execution_conclusion']
    clause = absolute_safety_phrase(conclusion.get('statement'))
    if clause:
        flag(None, None, 'The execution conclusion', conclusion['statement'], clause)
    return out
