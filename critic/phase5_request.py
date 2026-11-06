"""Database-independent preflight from the frozen public prepare() implementation.

Execute its original predicates, not a second interpretation of the contract.
Catalogue/channel identity lookups cannot be authenticated from a supplied bundle;
those checks stay with the frozen retriever. This adapter never invents database
rows and never opens a database. Review scope and returned sources are separately
checked by retrieval.py. Real integration tests also exercise the full API.
"""
import ast
import json
import math
from functools import lru_cache
from types import SimpleNamespace

from . import schema as SCHEMA


@lru_cache(maxsize=1)
def _preflight():
    from jsonschema import Draft202012Validator
    from evaluation.r1_v4.rag_evidence_database.final_phase5_release.config import (
        REGISTRY, TEMPORAL_FAMILIES, CHANNELS, PROVENANCE_SCOPE)
    path = SCHEMA.PHASE5 / 'api.py'
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    error = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'QueryError')
    retriever = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'StructuredRetriever')
    original = next(n for n in retriever.body if isinstance(n, ast.FunctionDef) and n.name == 'prepare')
    retrieve = next(n for n in retriever.body if isinstance(n, ast.FunctionDef) and n.name == 'retrieve')
    budget_guard = next(n for n in ast.walk(retrieve) if isinstance(n, ast.If)
                        and 'sum(' in ast.unparse(n.test) and 'windows.values()' in ast.unparse(n.test))
    database_names = {'row', 'c', 'raw', 'sem'}

    class WithoutDatabase(ast.NodeTransformer):
        def visit_Assign(self, node):
            if any(isinstance(n, ast.Name) and n.id in database_names for n in ast.walk(node)):
                return None
            return self.generic_visit(node)

        def visit_If(self, node):
            if any(isinstance(n, ast.Name) and n.id in database_names for n in ast.walk(node.test)):
                return None
            result = self.generic_visit(node)
            result.body = result.body or [ast.Pass()]
            return result

        def visit_Return(self, node):
            return None

    fn = WithoutDatabase().visit(original)
    # scope is already bound to the review, never a fabricated catalogue row.
    fn.args.args.append(ast.arg(arg='scope'))
    fn.body.append(ast.Return(value=ast.Constant(None)))
    budget = ast.parse('def budget(windows):\n    pass').body[0]
    budget.body = [budget_guard, ast.Return(value=ast.Constant(None))]
    module = ast.fix_missing_locations(ast.Module(body=[error, fn, budget], type_ignores=[]))
    if any(isinstance(n, ast.Attribute) and n.attr in ('backend', 'store', 'execute')
           for n in ast.walk(module)):
        raise ValueError('Frozen prepare changed: preflight still contains database access')
    namespace = dict(math=math, REGISTRY=REGISTRY, TEMPORAL_FAMILIES=TEMPORAL_FAMILIES,
                     CHANNELS=CHANNELS, PROVENANCE_SCOPE=PROVENANCE_SCOPE)
    exec(compile(module, str(path), 'exec'), namespace)
    validator = Draft202012Validator(SCHEMA.load('phase5_query'))
    return namespace['prepare'], namespace['QueryError'], SimpleNamespace(validator=validator), namespace['budget']


def refusal(q, scope=None):
    """Return (public status, diagnostic), or None. No assertion of source authenticity."""
    try:
        wire = json.dumps(q, sort_keys=True, allow_nan=False)
        if not isinstance(q, dict) or len(wire) > 128000:
            return 'INVALID SCOPE', 'Finite bounded JSON object required'
    except (ValueError, TypeError, RecursionError):
        return 'INVALID SCOPE', 'Finite bounded JSON object required'
    prepare, error, adapter, _ = _preflight()
    try:
        prepare(adapter, q, scope or {k: q.get(k) for k in ('execution_id', 'task_id', 'variant_id')})
    except error as exc:
        return exc.status, exc.reason
    except (ValueError, TypeError, OverflowError, RecursionError):
        return 'INVALID SCOPE', 'Finite bounded selectors and well-formed request values required'
    return None


def returned_window_refusal(q, bundle):
    """An evaluated group with items asserts a nonempty public frames() window.

    Apply retrieve()'s original total-sample guard to that proven lower bound.
    Empty/out-of-range windows remain unknown, so legitimate unavailable bundles
    are not refused merely for requesting large windows beyond a terminal frame.
    """
    if not bundle['independent_validation']['passed']:
        return None
    obligations = q.get('obligations')
    if not isinstance(obligations, list):
        return None  # the public request/schema refusal already diagnoses this
    by_id = {o['id']: o for o in obligations if isinstance(o, dict) and isinstance(o.get('id'), str)}
    windows = {}
    for g in bundle['groups']:
        selector = by_id.get(g['obligation_id'], {}).get('selector', {})
        if g['items'] and isinstance(selector, dict) and selector.get('kind') == 'frames':
            start, end = selector.get('start'), selector.get('end')
            if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (start, end)):
                windows[g['obligation_id']] = [start, end]
    _, error, _, budget = _preflight()
    try:
        budget(windows)
    except error as exc:
        return exc.status, exc.reason
    return None
