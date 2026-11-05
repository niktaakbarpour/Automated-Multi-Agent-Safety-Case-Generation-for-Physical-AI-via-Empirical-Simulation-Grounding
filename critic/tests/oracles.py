"""Access to the team's own code and to jsonschema, used by the tests as oracles.

The team's modules (evaluation/r1_v4) are written for Python 3.10+: they use annotations such as
`str|None`, which Python 3.9 evaluates and rejects. Postponed evaluation of annotations
(PEP 563, `from __future__ import annotations`) is all they need to load on 3.9, so on 3.9
install() compiles them that way. Nothing else about them changes, and it applies only to the
`evaluation` package, only in the tests.

jsonschema is a dependency of the team's R1 checker (evaluation/r1_v4/requirements.txt pins
jsonschema==4.19.1). Tests that only need a schema verdict fall back to the Critic's own
validator, which test_agrees_with_jsonschema compares with jsonschema wherever it is installed.
Tests that need jsonschema itself (that comparison, and running the checker) skip without it,
unless CRITIC_STRICT_TESTS=1 is set: then every missing oracle is a failure, so a test total can
never hide missing coverage.
"""
import __future__
import importlib.abc
import importlib.machinery
import os
import sys

from critic import schema as SCHEMA

STRICT = os.environ.get('CRITIC_STRICT_TESTS') == '1'

try:
    import jsonschema
except ImportError:
    jsonschema = None


class _PostponedAnnotationsLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):  # always from source, so a cached 3.10+ compilation is never reused
        path = self.get_filename(fullname)
        return compile(self.get_data(path), path, 'exec', flags=__future__.annotations.compiler_flag,
                       dont_inherit=True)


class _TeamCodeFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name != 'evaluation' and not name.startswith('evaluation.'):
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is not None and type(spec.loader) is importlib.machinery.SourceFileLoader:
            spec.loader = _PostponedAnnotationsLoader(spec.loader.name, spec.loader.path)
        return spec


def install():
    """Make the team's modules importable on Python 3.9 (no effect on 3.10+)."""
    if sys.version_info < (3, 10) and not any(isinstance(f, _TeamCodeFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _TeamCodeFinder())


def has_jsonschema4():
    return jsonschema is not None and hasattr(jsonschema, 'Draft202012Validator')


def require(test, available, reason):
    """Skip the test when an oracle is missing, or fail it under CRITIC_STRICT_TESTS=1."""
    if available:
        return
    if STRICT:
        test.fail(f'{reason} (CRITIC_STRICT_TESTS=1 turns this skip into a failure)')
    test.skipTest(reason)


def validate(instance, schema):
    """Raise AssertionError unless instance matches schema: jsonschema if installed, else critic/schema.py."""
    if has_jsonschema4():
        errors = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(instance)]
    else:
        errors = SCHEMA.errors(instance, schema)
    if errors:
        raise AssertionError('; '.join(errors[:5]))
