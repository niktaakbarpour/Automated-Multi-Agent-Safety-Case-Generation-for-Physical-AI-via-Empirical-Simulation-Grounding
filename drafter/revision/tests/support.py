"""Shared helpers for the revision tests. Everything here is CPU only: no model, no network.

Every Critic report used in these tests is made by the real critic.review, either with rule checks
only or with a scripted reply. Scripted findings are synthetic test inputs and are labelled as such.
"""
from copy import deepcopy
from pathlib import Path
import json

import critic
from critic import contract as K, llm as L
from drafter.revision import contract as C, edits as E, engine as G, invariants as V
from drafter.revision.adapters import describe

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'integration' / 'fixtures' / 'one_pass_20261113' / 'artifacts' / 'models'
CASES = ROOT / 'critic' / 'cases'
EXAMPLES = ROOT / 'drafter' / 'revision' / 'examples'
LABEL = 'Synthetic test input written for the revision tests. Not a model result and not a scientific finding.'
GUARANTEE = 'Cream_cheese_1 was guaranteed physically safe throughout this execution.'
INTERVAL = [10, 257]
_CACHE = {}


def _load(path):
    if path not in _CACHE:
        _CACHE[path] = json.loads(Path(path).read_text(encoding='utf-8'))
    return deepcopy(_CACHE[path])


def fixture(name):
    return _load(FIXTURE / name)


def case(name):
    return _load(CASES / name)


def example(name):
    return _load(EXAMPLES / name)


def finding(object_id, node_id, category, explanation, action='Reword the statement.', **extra):
    """One finding of a scripted Critic model reply."""
    return {'object_id': object_id, 'node_id': node_id, 'category': category, 'severity': 'high',
            'explanation': explanation, 'evidence_ids': [], 'suggested_action': action, **extra}


def guarantee_finding():
    return finding('cream_cheese_1', 'cream_cheese_1:G1', 'C12',
                   'The goal states "' + GUARANTEE + '" Nothing in the package supports a guarantee.')


def review(critic_request, findings=None):
    """The real Critic: rule checks only, or with a scripted model reply made of `findings`."""
    if findings is None:
        return critic.review(critic_request)
    return critic.review(critic_request, L.ScriptedLLM(json.dumps({'findings': findings})))


def approve(report, ids=None, decision='approved'):
    """Synthetic-label decisions for the criticisms that need one (or for `ids`)."""
    wanted = ids if ids is not None else [
        c['criticism_id'] for c in report['criticisms']
        if c['phase'] == 'review' and (c['finding_source'] != 'deterministic' or c['human_review_required'])]
    return [{'criticism_id': i, 'decision': decision, 'decided_by': 'synthetic_test_label', 'reviewer': None,
             'note': 'Decided only as a labelled synthetic test input.'} for i in wanted]


def request_for(critic_request, findings=None, *, decide=True, name='test', **options):
    """A revision request for `critic_request`, reviewed by the real Critic."""
    report = review(critic_request, findings)
    options.setdefault('synthetic_label', LABEL)
    return C.build_request('test:' + name, critic_request, report,
                           finding_decisions=approve(report) if decide else (), **options)


def guarantee_request(**options):
    """The fixture's controlled-negative request with a labelled synthetic C12 on the guarantee."""
    return request_for(fixture('critic.controlled-negative.request.json'), [guarantee_finding()], **options)


def node(bundle, object_id, node_id):
    return E.node_of(bundle, object_id, node_id)


def rehash(request):
    request['critic_request_sha256'] = K.digest(request['critic_request'])
    request['critic_report_sha256'] = K.digest(request['critic_report'])
    return request


def rule_issues(request, result, bundle):
    """Diff rules applied to `bundle` as if it were the revised bundle of `result`."""
    _, info = C.fresh_review(request['critic_request'])
    _, by = E.apply(request, result['edits'], result['adapter'])
    diff = V.attribute(V.compare(request['critic_request']['argument_bundle'], bundle), by)
    return V.diff_rule_issues(request, bundle, diff, result['edits'], info)


def adapter_info(adapter):
    return describe(adapter)


class Checks:
    """Mixin with the assertions every result must satisfy."""

    def assert_sound(self, request, result, before):
        """`before` is the digest of the request taken before revise() ran."""
        self.assertEqual(K.digest(request), before, 'the request was modified')
        self.assertEqual(C.schema_problems(result, 'revision_result'), [])
        if result['outcome'] == 'failed':
            self.assertEqual(result['stop_reason'], 'execution_failure')
            self.assertIsNone(result['revised_argument_bundle'])
            return
        self.assertEqual(G.verify_result(request, result), [])
        if not result['request_issues']:
            self.assertEqual(len(result['dispositions']), len(request['critic_report']['criticisms']))
        if result['outcome'] != 'revised':
            self.assertIsNone(result['revised_argument_bundle'])
            self.assertEqual((result['edits'], result['diff']), ([], []))
            self.assertIsNotNone(result['stop_reason'])
            return
        self.assertTrue(all(v['status'] == 'passed' for v in result['validators']), result['validators'])
        original, revised = request['critic_request'], G.recriticism_request(request, result)
        self.assertEqual({k: v for k, v in original.items() if k not in ('argument_bundle', 'request_id')},
                         {k: v for k, v in revised.items() if k not in ('argument_bundle', 'request_id')})
        self.assertEqual(K.digest(revised), result['recriticism']['request_sha256'])
        self.assertEqual(K.digest(revised['evaluation_context']['r1_configuration']),
                         original['evaluation_context']['r1_configuration_sha256'])
        old, new = original['argument_bundle'], revised['argument_bundle']
        self.assertEqual(new['protected_objects'], old['protected_objects'])
        self.assertEqual([g['object_id'] for g in new['graphs']], [g['object_id'] for g in old['graphs']])
        self.assertEqual(new['execution_id'], old['execution_id'])
        touched = {(d['object_id'], d['node_id']) for d in result['diff'] if d['node_id'] is not None}
        for old_item, new_item in zip(old['graphs'], new['graphs']):
            kept = {n['id']: n for n in new_item['graph']['nodes']}
            for n in old_item['graph']['nodes']:
                if (old_item['object_id'], n['id']) not in touched:
                    self.assertEqual(kept[n['id']], n, 'an untouched node changed')
            for n in new_item['graph']['nodes']:
                if n['type'] == 'solution':
                    self.assertIn(n, old_item['graph']['nodes'], 'a Solution was added or modified')
        for d in result['diff']:
            self.assertTrue(d['edit_indexes'])
            for index in d['edit_indexes']:
                edit = result['edits'][index]
                self.assertTrue(edit['finding_ids'] and edit['justification'].strip())
        self.assertNotEqual(review(revised)['review_status'], 'rejected_invalid_input')

    def revise(self, request, adapter=None):
        before = K.digest(request)
        result = G.revise(request, adapter)
        self.assert_sound(request, result, before)
        return result
