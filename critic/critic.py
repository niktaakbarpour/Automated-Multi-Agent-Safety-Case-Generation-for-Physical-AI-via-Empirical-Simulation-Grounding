"""Critic.review: rule-based checks, then an optional LLM pass, then one report."""
from collections import Counter

from . import checks
from . import contract as K
from . import llm as L
from . import schema as SCHEMA

CRITIC_VERSION = '0.2.0'
DISCLAIMER = ('A report with no blocking findings means only that this Critic found no issue within the '
              'supplied evidence and review scope. It does not show that R1 holds or that the robot was '
              'physically safe.')


def review(request, llm=None):
    """Review one execution's argument bundle.

    request: dict following critic/schemas/critic_request.schema.json
    llm:     NullLLM (default), ScriptedLLM or OpenAICompatibleLLM
    returns: dict following critic/schemas/critic_report.schema.json

    Never raises on bad input. review_status says what happened:
      completed               input valid, review done (the LLM step, if any, worked)
      completed_llm_failed    input valid, rule-based review done, the LLM step failed
      rejected_invalid_input  input failed validation; its diagnostics are the 'validation' findings,
                              the LLM was not called, and this is not a completed critique
      internal_error          the report itself failed its schema (a Critic bug); see status_detail
    """
    llm = llm or L.NullLLM()
    deterministic, info = checks.run_all(request)
    if not info['input_valid']:
        accepted, rejected = [], []
        status = {'backend': llm.backend, 'model': llm.name, 'prompt_version': L.PROMPT_VERSION,
                  'called': False, 'ok': False, 'latency_s': None,
                  'error': 'Skipped: the input failed validation, so no model review was run.'}
        review_status = 'rejected_invalid_input'
    else:
        accepted, rejected, status = L.run(llm, request, deterministic, info['records'], info['checker_admission'])
        review_status = 'completed' if status['ok'] else 'completed_llm_failed'

    criticisms, evidence_requests = [], []
    for number, f in enumerate(deterministic + accepted, start=1):
        f = dict(f)
        request_for_evidence = f.pop('_evidence_request', None)
        criticism_id = f'CRIT-{number:03d}'
        criticisms.append({'criticism_id': criticism_id, 'critic_version': CRITIC_VERSION, **f})
        if request_for_evidence is not None:
            evidence_requests.append({**request_for_evidence, 'criticism_id': criticism_id})

    req = request if isinstance(request, dict) else {}
    ctx = req.get('evaluation_context') if not info['fatal'] else {}
    report = {
        'schema_version': K.REPORT_SCHEMA_VERSION,
        'critic_version': CRITIC_VERSION,
        'request_id': str(req.get('request_id', '')),
        'execution_id': str((ctx or {}).get('execution_id', '')),
        'test_fixture': bool(req.get('test_fixture')),
        'review_status': review_status,
        'input_valid': info['input_valid'],
        'status_detail': None,
        'llm': status,
        'checker_admission': info['checker_admission'],
        'criticisms': criticisms,
        'evidence_requests': evidence_requests,
        'unresolved_concerns': _unresolved_concerns(req, info),
        'rejected_llm_findings': rejected,
        'summary': _summary(req, info, criticisms),
    }
    return _checked(report)


def _checked(report):
    """Validate the report against its own schema; a failure is a Critic bug, reported, never hidden."""
    try:
        problems = SCHEMA.errors(report, SCHEMA.load('report'), limit=5)
    except Exception as exc:  # pragma: no cover - only a broken schema file gets here
        problems = [f'{type(exc).__name__}: {exc}']
    if problems:
        report['review_status'] = 'internal_error'
        report['status_detail'] = 'The report failed its own schema: ' + '; '.join(problems)
    return report


def _summary(req, info, criticisms):
    if info['fatal']:
        configured, graph_objects, claimed = [], set(), None
    else:
        configured = req['evaluation_context']['protected_objects']
        graph_objects = {g['object_id'] for g in req['argument_bundle']['graphs']}
        claimed = req['argument_bundle']['execution_conclusion'].get('claimed_outcome')
    return {
        'objects_configured': list(configured),
        'objects_with_graphs': [o for o in configured if o in graph_objects],
        'objects_missing': [o for o in configured if o not in graph_objects],
        'claimed_execution_outcome': claimed if isinstance(claimed, str) else None,
        'recomputed_execution_outcome': info['expected_outcome'],
        'counts_by_source': dict(Counter(c['finding_source'] for c in criticisms)),
        'counts_by_category': dict(sorted(Counter(c['category'] for c in criticisms).items())),
        'blocking_defects': any(c['blocking'] for c in criticisms),
        'needs_human_review': [c['criticism_id'] for c in criticisms if c['human_review_required']],
        'disclaimer': DISCLAIMER,
    }


def _unresolved_concerns(req, info):
    """Open issues the Critic cannot settle, stated without judging the argument."""
    if info['fatal']:
        return ['The request could not be reviewed because it failed structural validation.']
    out = []
    if not info['input_valid']:
        out.append('The input failed validation (see the criticisms in the validation phase), so this is a rejection, '
                   'not a completed critique: no model review was run, and review-phase criticisms are provisional.')
    supplied = len(req['checker_assessments'])
    admitted = sum(1 for a in info['checker_admission'] if a['admitted'])
    if not admitted:
        out.append(f'No admitted checker assessment ({supplied} supplied, 0 admitted). Treated as unavailable, '
                   'not as "no violation"; violation, no-violation and non-applicability outcomes cannot be '
                   'established from this package.')
    elif any(a['route'] == 'synthetic_test_fixture' for a in info['checker_admission']):
        out.append('Admitted checker assessments are synthetic test-fixture outputs, not validated empirical results.')
    for oid, found in sorted(info['admitted'].items()):
        outcomes = sorted({a['outcome'] for a in found})
        verdict, conflict = checks.assessment_verdict(found)
        if conflict:
            out.append(f'Admitted checker assessments for {oid} disagree ({", ".join(outcomes)}). Both are kept; the '
                       'conflict needs an evidence-consistency investigation.')
        elif len(outcomes) > 1:
            out.append(f'Admitted checker assessments for {oid} differ ({", ".join(outcomes)}), but only because some '
                       f'are insufficient_information, which is a gap rather than counter-evidence; {verdict} is used.')
        for a in found:
            notes = (['its evidence is incomplete (complete: false)'] if not a['complete'] else []) + \
                [f'uncertainty: {u}' for u in a['uncertainty']]
            if notes:
                out.append(f"The admitted checker assessment {a['assessment_id']} ({oid}, {a['outcome']}) reports "
                           f"{'; '.join(notes)}.")
    retrieval = req['retrieval_context']
    if not retrieval.get('complete_within_requested_scope', False):
        out.append('Retrieval reports that the evidence package is incomplete for the requested scope.')
    for gap in retrieval.get('gaps') if isinstance(retrieval.get('gaps'), list) else []:
        if isinstance(gap, dict):
            out.append(f"Missing {gap.get('measurement_type')} for {gap.get('object_id')} over {gap.get('interval')}.")
    if req.get('test_fixture'):
        out.append('This request contains synthetic test data; its results are not empirical findings.')
    return out
