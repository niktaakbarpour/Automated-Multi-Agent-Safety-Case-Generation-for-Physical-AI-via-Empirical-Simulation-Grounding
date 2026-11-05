"""A small JSON Schema (draft 2020-12) validator, standard library only.

It supports exactly the keywords used by the Critic's own schemas and the team's
GSN, registry-record, R1-configuration, checker-assessment and Phase 5 structured
retrieval schemas. Any other
keyword raises UnsupportedKeyword, so a rule can never be skipped silently. The
tests compare its verdicts with the jsonschema package wherever that is installed.
"""
import json
import math
import re
from functools import lru_cache
from pathlib import Path

ANNOTATIONS = {'$id', '$schema', 'title', 'description', '$comment', 'default', 'examples'}
KEYWORDS = {'$defs', '$ref', 'type', 'enum', 'const', 'properties', 'required', 'additionalProperties',
            'propertyNames', 'items', 'contains', 'minItems', 'maxItems', 'uniqueItems', 'minLength', 'maxLength',
            'pattern', 'minimum', 'allOf', 'anyOf', 'oneOf', 'if', 'then', 'else'}

ROOT = Path(__file__).resolve().parents[1]
PHASE5 = ROOT / 'evaluation' / 'r1_v4' / 'rag_evidence_database' / 'final_phase5_release'
SCHEMAS = {
    'request': ROOT / 'critic' / 'schemas' / 'critic_request.schema.json',
    'report': ROOT / 'critic' / 'schemas' / 'critic_report.schema.json',
    'gsn_graph': ROOT / 'evaluation' / 'r1_v4' / 'evidence_registry_gsn' / 'gsn_graph.schema.json',
    'registry_record': ROOT / 'evaluation' / 'r1_v4' / 'evidence_registry_gsn' / 'registry_record.schema.json',
    'r1_configuration': ROOT / 'requirements' / 'r1_generalized_v2' / 'R1_V2_CONFIG_SCHEMA.json',
    'checker_assessment': ROOT / 'evaluation' / 'r1_v4' / 'assessment.schema.json',
    'phase5_query': PHASE5 / 'STRUCTURED_QUERY_SCHEMA.json',
    'phase5_bundle': PHASE5 / 'EVIDENCE_BUNDLE_SCHEMA.json',
    'phase5_consumer': ROOT / 'critic' / 'schemas' / 'phase5_bundle_consumer.schema.json',
}


class UnsupportedKeyword(ValueError):
    pass


@lru_cache(maxsize=None)
def load(name):
    """One of the known schemas, by name (see SCHEMAS)."""
    return json.loads(SCHEMAS[name].read_text(encoding='utf-8'))


def check_schema(schema, path='$'):
    """Raise UnsupportedKeyword if any part of the schema uses a keyword this validator does not implement."""
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise UnsupportedKeyword(f'{path}: a schema must be an object or a boolean')
    unknown = set(schema) - KEYWORDS - ANNOTATIONS
    if unknown:
        raise UnsupportedKeyword(f'{path}: unsupported keyword(s) {sorted(unknown)}')
    for key in ('properties', '$defs'):
        for name, sub in schema.get(key, {}).items():
            check_schema(sub, f'{path}.{key}.{name}')
    for key in ('allOf', 'anyOf', 'oneOf'):
        for i, sub in enumerate(schema.get(key, [])):
            check_schema(sub, f'{path}.{key}[{i}]')
    for key in ('items', 'contains', 'additionalProperties', 'propertyNames', 'if', 'then', 'else'):
        if key in schema:
            check_schema(schema[key], f'{path}.{key}')


def errors(instance, schema, limit=20):
    """Return up to `limit` messages 'path: problem'; an empty list means valid."""
    out = []
    _check(instance, schema, schema, '$', out, limit)
    return out[:limit]


def is_valid(instance, schema):
    return not errors(instance, schema, limit=1)


# ------------------------------------------------------------------ JSON value semantics

def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _type_ok(v, kind):
    if kind == 'null':
        return v is None
    if kind == 'boolean':
        return isinstance(v, bool)
    if kind == 'object':
        return isinstance(v, dict)
    if kind == 'array':
        return isinstance(v, list)
    if kind == 'string':
        return isinstance(v, str)
    if kind == 'number':
        return _is_number(v) and math.isfinite(v)
    if kind == 'integer':
        return _is_number(v) and math.isfinite(v) and float(v).is_integer()
    raise UnsupportedKeyword(f'type {kind!r}')


def _equal(a, b):
    """JSON equality: 1 == 1.0, but true is not 1 (_is_number excludes booleans, and the type check below
    keeps true and 1 apart)."""
    if _is_number(a) and _is_number(b):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def _resolve(root, ref):
    if not ref.startswith('#'):
        raise UnsupportedKeyword(f'only local $ref is supported, got {ref!r}')
    node = root
    for part in [p for p in ref[1:].split('/') if p]:
        node = node[part.replace('~1', '/').replace('~0', '~')]
    return node


# ------------------------------------------------------------------ validation

def _check(v, s, root, path, out, limit):
    if len(out) >= limit:
        return
    if s is True:
        return
    if s is False:
        out.append(f'{path}: no value is allowed here')
        return
    unknown = set(s) - KEYWORDS - ANNOTATIONS
    if unknown:
        raise UnsupportedKeyword(f'{path}: unsupported keyword(s) {sorted(unknown)}')

    def bad(msg, at=path):
        out.append(f'{at}: {msg}')

    if '$ref' in s:
        _check(v, _resolve(root, s['$ref']), root, path, out, limit)
    if 'type' in s:
        kinds = s['type'] if isinstance(s['type'], list) else [s['type']]
        if not any(_type_ok(v, k) for k in kinds):
            bad(f"expected {' or '.join(kinds)}, got {_kind(v)}")
            return
    if 'const' in s and not _equal(v, s['const']):
        bad(f"must be {json.dumps(s['const'])}")
    if 'enum' in s and not any(_equal(v, e) for e in s['enum']):
        bad(f'{_short(v)} is not one of {json.dumps(s["enum"])[:200]}')

    if isinstance(v, str):
        if 'minLength' in s and len(v) < s['minLength']:
            bad(f"shorter than {s['minLength']} characters")
        if 'maxLength' in s and len(v) > s['maxLength']:
            bad(f"longer than {s['maxLength']} characters")
        if 'pattern' in s and not re.search(s['pattern'], v):
            bad(f"{_short(v)} does not match {s['pattern']}")
    if _is_number(v) and 'minimum' in s and v < s['minimum']:
        bad(f"{v} is below the minimum {s['minimum']}")
    if isinstance(v, list):
        if 'minItems' in s and len(v) < s['minItems']:
            bad(f"needs at least {s['minItems']} items")
        if 'maxItems' in s and len(v) > s['maxItems']:
            bad(f"allows at most {s['maxItems']} items")
        if s.get('uniqueItems') and any(_equal(v[i], v[j]) for i in range(len(v)) for j in range(i)):
            bad('items must be unique')
        if 'items' in s:
            for i, item in enumerate(v):
                _check(item, s['items'], root, f'{path}[{i}]', out, limit)
        if 'contains' in s and not any(is_valid_in(item, s['contains'], root) for item in v):
            bad('no item matches the required form (contains)')
    if isinstance(v, dict):
        for k in s.get('required', []):
            if k not in v:
                bad(f'missing required property {k!r}')
        props = s.get('properties', {})
        for k, item in v.items():
            if k in props:
                _check(item, props[k], root, f'{path}.{k}', out, limit)
            elif 'additionalProperties' in s:
                extra = s['additionalProperties']
                if extra is False:
                    bad(f'unexpected property {k!r}')
                else:
                    _check(item, extra, root, f'{path}.{k}', out, limit)
            if 'propertyNames' in s:
                _check(k, s['propertyNames'], root, f'{path} key {k!r}', out, limit)

    for sub in s.get('allOf', []):
        _check(v, sub, root, path, out, limit)
    if 'anyOf' in s and not any(is_valid_in(v, sub, root) for sub in s['anyOf']):
        bad('does not match any allowed form (anyOf)')
    if 'oneOf' in s:
        matches = sum(is_valid_in(v, sub, root) for sub in s['oneOf'])
        if matches != 1:
            bad(f'must match exactly one allowed form (oneOf), matched {matches}')
    if 'if' in s:
        branch = s.get('then') if is_valid_in(v, s['if'], root) else s.get('else')
        if branch is not None:
            _check(v, branch, root, path, out, limit)


def is_valid_in(v, s, root):
    found = []
    _check(v, s, root, '$', found, 1)
    return not found


def _kind(v):
    for k in ('null', 'boolean', 'integer', 'number', 'string', 'array', 'object'):
        try:
            if _type_ok(v, k):
                return k
        except UnsupportedKeyword:
            pass
    return type(v).__name__


def _short(v):
    text = json.dumps(v, ensure_ascii=False, default=str) if not isinstance(v, float) or math.isfinite(v) else str(v)
    return text if len(text) <= 60 else text[:57] + '...'
