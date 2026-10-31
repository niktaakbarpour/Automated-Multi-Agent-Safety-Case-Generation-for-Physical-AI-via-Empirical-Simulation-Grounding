"""Strict JSON, canonical serialization, content addressing; no input-directed I/O."""
import dataclasses
from enum import Enum
import hashlib
import json
import math
from pathlib import Path


def primitive(value):
    if dataclasses.is_dataclass(value):
        return {f.name: primitive(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: primitive(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [primitive(v) for v in value]
    return value


def canonical(value):
    return json.dumps(primitive(value), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def bytes_digest(value):
    return hashlib.sha256(value).hexdigest()


def strict_loads(text):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('duplicate_json_key:' + k)
            result[k] = v
        return result
    def constant(value):
        raise ValueError('nonfinite_json:' + value)
    value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    canonical(value)  # Also rejects finite-looking exponent overflow, e.g. 1e999.
    return value


def load(path):
    return strict_loads(Path(path).read_text())


def write_new(path, value):
    with Path(path).open('xb') as f:
        f.write(canonical(value) + b'\n')
