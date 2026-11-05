"""Synthetic Phase 5 structured-evidence fixtures, assembled by the release's own code.

The release (evaluation/r1_v4/rag_evidence_database/final_phase5_release/api.py) reads its database and
sources on Hestia, so it cannot run here. What it can do anywhere is assemble a bundle: these builders
take the code that does that straight from api.py with ast (StructuredRetriever.response, the group
update, the citation loop and the status rule) and run it on synthetic groups. No other part of api.py
is executed. The Critic's checks (critic/retrieval.py) are separate code; the tests check that the two
agree on every bundle built here.
"""
import ast
import copy
import types
from functools import lru_cache

from critic import contract as K
from critic import schema as SCHEMA

API = SCHEMA.PHASE5 / 'api.py'
SYNTHETIC_ROOT = '/synthetic/critic_test_fixture/phase5'
_SELF = types.SimpleNamespace(mode='verified_session')  # what response() reads from the retriever


@lru_cache(maxsize=None)
def release():
    """The bundle-assembly code of api.py, as functions: response, finish_group, cite, status_of."""
    tree = ast.parse(API.read_text(encoding='utf-8'), filename=str(API))
    retriever = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'StructuredRetriever')
    methods = {f.name: f for f in retriever.body if isinstance(f, ast.FunctionDef)}
    retrieve = methods['retrieve']
    update = next(n for n in ast.walk(retrieve) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                  and ast.unparse(n.value.func) == 'g.update')
    cite = next(n for n in ast.walk(retrieve) if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                and n.target.id == 'item')
    assigns = {t.id: n for n in ast.walk(retrieve) if isinstance(n, ast.Assign)
               for t in n.targets if isinstance(t, ast.Name)}

    def function(header, body):
        f = ast.parse(header + '\n    pass').body[0]
        f.body = body
        return f

    module = ast.Module(body=[
        methods['response'],
        function('def finish_group(g, o):', [update]),
        function('def cite(g, o, c):', [cite]),
        function('def status_of(groups, check):', [assigns['mandatory'], assigns['complete'], assigns['status'],
                                                   ast.parse('return status').body[0]]),
    ], type_ignores=[])
    namespace = {'digest': K.digest, 'VERSION': K.PHASE5_VERSION, 'DATABASE_SHA': K.PHASE5_DATABASE_SHA256}
    exec(compile(ast.fix_missing_locations(module), str(API), 'exec'), namespace)  # noqa: S102 - the team's code
    return types.SimpleNamespace(**{k: namespace[k] for k in ('response', 'finish_group', 'cite', 'status_of')})


# ------------------------------------------------------------------ requests

def scope_of(execution, task, variant):
    return {'execution_id': execution, 'task_id': task, 'variant_id': variant}


def obligation(oid, family, scope, mandatory=True, frames=None, **extra):
    """One explicit obligation (STRUCTURED_QUERY_SCHEMA.json)."""
    o = {'id': oid, 'execution_id': scope['execution_id'], 'family': family, 'field': K.PHASE5_REGISTRY[family],
         'mandatory': mandatory}
    if frames is not None:
        o['selector'] = {'kind': 'frames', 'start': frames[0], 'end': frames[1]}
    o.update(extra)
    return o


def request(scope, obligations, assurance='verified_source_values'):
    return {'schema_version': K.PHASE5_VERSION, **scope, 'assurance': assurance,
            'provenance': {'level': 'source_identity'}, 'obligations': list(obligations)}


# ------------------------------------------------------------------ items (as api.py and bundle.py build them)

def _sha(label):
    return K.digest(label)


def channel_item(scope, family, frames, conditional=()):
    """A raw channel item with one sample per saved frame (api.py:StructuredRetriever.raw). Its interpretation
    properties are verified, except those named in conditional."""
    field = K.PHASE5_REGISTRY[family]
    path = f"{SYNTHETIC_ROOT}/{scope['execution_id']}/source.h5"
    record = 'channel:' + _sha([scope['execution_id'], family])
    units = {'status': 'VERIFIED', 'value': 'rad'}
    frame = {'status': 'VERIFIED', 'value': 'native_joint_space'}
    return {'id': record, 'family': family, 'original_evidence_ids': [record], **scope,
            'source_artifact': {'path': path, 'sha256': _sha(path), 'selector': field},
            'samples': [{'saved_frame_index': i, 'source_selector': f'/frames/{i:06d}/{field}',
                         'source_status': 'verified_source', 'value': [0.0, 0.1], 'value_units': 'rad',
                         'coordinate_frame': 'native_joint_space'} for i in range(frames[0], frames[1] + 1)],
            'units': units, 'coordinate_frame': frame,
            'interpretation_properties': {
                'units': units, 'coordinate_frame': frame,
                **{p: {'status': 'CONDITIONAL' if p in conditional else 'VERIFIED', 'value': None}
                   for p in ('component_order', 'cache_offset_seconds')}},
            'derived_interpretation': 'semantic:' + _sha(record), 'integrity_status': 'verified_source',
            'origin': 'direct_recording', 'synchronized_physical_instant': False}


def reference_item(scope, family, selector, value, original_ids=()):
    """A recorded-metadata or identity item (retrieval_remediation/bundle.py:Retriever.item)."""
    path = f"{SYNTHETIC_ROOT}/{scope['execution_id']}/{family}.json"
    digest = _sha(path)
    return {'id': 'source-ref:' + K.digest([path, digest, selector]),
            'id_kind': 'verified_source_reference_not_new_measurement_record', 'family': family,
            'original_evidence_ids': list(original_ids), **scope,
            'source_artifact': {'path': path, 'sha256': digest, 'selector': selector}, 'value': value,
            'integrity_status': 'verified_source', 'origin': 'recorded_metadata_or_existing_derived_identity',
            'units': None, 'interpretation_status': 'VERIFIED_RECORDED_METADATA',
            'synchronized_physical_instant': False}


# ------------------------------------------------------------------ bundles

def evaluated(req, results, scope=None):
    """The bundle api.py returns for a request it evaluated.

    results: {obligation_id: (group status, items, reason[, conditional properties])}; obligations not
    listed come back UNAVAILABLE with no items. Independent validation accepts a group exactly when it
    is AVAILABLE with evidence (completeness.py checks more, against the database).
    """
    rel = release()
    scope = scope or {k: req[k] for k in ('execution_id', 'task_id', 'variant_id')}
    groups = []
    for o in req['obligations']:
        status, items, reason, *conditional = results.get(o['id'], ('UNAVAILABLE', [], 'No recorded samples'))
        g = {'family': o['family'], 'status': status, 'items': copy.deepcopy(list(items)), 'coverage': {},
             'reason': reason}
        if o['family'] in K.PHASE5_CHANNELS:  # raw channel groups always list them, possibly none
            g['conditional_assumptions'] = sorted(set(conditional[0])) if conditional else []
        elif conditional and conditional[0]:
            g['conditional_assumptions'] = list(conditional[0])
        rel.finish_group(g, o)
        rel.cite(g, o, scope)
        groups.append(g)
    fulfilled = [{'obligation_id': g['obligation_id'], 'mandatory': g['mandatory'],
                  'satisfied': g['status'] == 'AVAILABLE' and bool(g['items'])} for g in groups]
    check = {'passed': True, 'errors': [], 'obligations': fulfilled,
             'mandatory_fulfilled': bool(fulfilled) and all(x['satisfied'] for x in fulfilled if x['mandatory']),
             'method': 'Synthetic test fixture: groups accepted when AVAILABLE with evidence'}
    status = rel.status_of(groups, check)
    reason = ('All mandatory explicit obligations fulfilled' if status == K.PHASE5_COMPLETE else
              'Missing mandatory evidence remains explicit')
    provenance = {'scope': 'current_source_identity_only', 'historical_runtime_attested': False}
    return rel.response(_SELF, req, status, reason, groups, scope, check, provenance)


def refused(req, status, reason, scope=None, validation=None):
    """The bundle api.py returns for a request it refused, could not verify, or whose independent validation
    failed (UNVERIFIED PLAN, with that validation): no evidence."""
    return release().response(_SELF, req, status, reason, scope=scope, validation=validation)


def entry(req, bundle):
    return {'request': req, 'bundle': bundle}
