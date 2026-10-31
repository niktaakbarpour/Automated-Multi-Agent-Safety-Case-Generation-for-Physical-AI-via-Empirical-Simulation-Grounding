"""Immutable normalized record types. Truth and contract validity are distinct."""
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Truth(str, Enum):
    TRUE = 'T'
    FALSE = 'F'
    UNKNOWN = 'U'


class Validity(str, Enum):
    VERIFIED = 'verified'
    MISSING = 'missing'
    INVALID_LOCAL = 'invalid_local'
    INVALID_CONTRACT = 'invalid_contract'
    CONTRADICTORY = 'contradictory'


class Applicability(str, Enum):
    APPLICABLE = 'applicable'
    NA = 'not_applicable'
    UNKNOWN = 'indeterminate'
    IC = 'unsupported_evidence_contract'


class Outcome(str, Enum):
    V = 'violation_observed'
    N = 'no_violation_observed_within_validated_coverage'
    NA = 'not_applicable'
    U = 'insufficient_information'
    IC = 'invalid_measurement_contract'


@dataclass(frozen=True)
class Interval:
    start: float
    end: float

    def contains(self, other):
        return self.start <= other.start <= other.end <= self.end

    def overlaps(self, other):
        return self.start <= other.end and other.start <= self.end


@dataclass(frozen=True)
class Frame:
    id: str
    clock: str
    length_unit: str
    time_unit: str
    handedness: str


@dataclass(frozen=True)
class Uncertainty:
    temporal: float | None
    description: tuple[str, ...]


@dataclass(frozen=True)
class Measurement:
    """Stored direct/derived values; never converted into support/fall labels."""
    quantity: str
    values: tuple[float, ...]
    unit: str


@dataclass(frozen=True)
class Geometry:
    shape: str
    dimensions: tuple[float, ...]
    static: bool
    horizontal: bool
    complete: bool


@dataclass(frozen=True)
class Contact:
    pairs: tuple[tuple[str, str], ...]
    complete: bool
    forces: tuple[float, ...] | None


@dataclass(frozen=True)
class Camera:
    camera_id: str
    indices: tuple[int, ...]
    decoded: tuple[int, ...]
    inspected: tuple[int, ...]


@dataclass(frozen=True)
class Declaration:
    """Exact synthetic assumption, not an inferred physical measurement."""
    items: tuple[tuple[str, Any], ...]

    def get(self, key, default=None):
        return dict(self.items).get(key, default)


def freeze(value):
    if isinstance(value, dict):
        return tuple((k, freeze(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class Evidence:
    id: str
    kind: str
    claim: str
    truth: Truth
    validity: Validity
    object_id: str
    execution_id: str
    surfaces: tuple[str, ...]
    interval: Interval
    cells: tuple[str, ...]
    dependencies: tuple[str, ...]
    source_ref: str
    producer: str
    frame: Frame
    uncertainty: Uncertainty
    payload: Measurement | Geometry | Contact | Camera | Declaration


@dataclass(frozen=True)
class Admission:
    evidence_id: str
    status: Validity
    reasons: tuple[str, ...]
    dependencies: tuple[str, ...]
    source_hash: str | None


@dataclass(frozen=True)
class Cell:
    id: str
    kind: str
    interval: Interval


@dataclass(frozen=True)
class Coverage:
    requested: tuple[str, ...]
    available: tuple[str, ...]
    admitted: tuple[str, ...]
    negative: tuple[str, ...]
    missing: tuple[str, ...]
    dependencies: tuple[str, ...]
    source_groups: tuple[tuple[str, tuple[str, ...]], ...]
    invalid: tuple[str, ...] = ()
    unobserved: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObjectAssessment:
    object_id: str
    surfaces: tuple[str, ...]
    applicability: Applicability
    outcome: Outcome
    reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    coverage: Coverage
    uncertainty: tuple[str, ...]
    complete: bool
    scope_mismatch: bool = False
    study_eligibility: str = 'not_decided_by_checker'
    execution_id: str = ''
    requirement_version: str = '2.0.0'
    checker_version: str = '4.0.0a1'
    adapter_version: str = '1.0.0'
    profile_version: str = '1.0.0'
    validation_status: str = 'synthetic_analytical_only'


def kleene_and(*values):
    if Truth.FALSE in values:
        return Truth.FALSE
    return Truth.TRUE if all(v == Truth.TRUE for v in values) else Truth.UNKNOWN


def kleene_not(value):
    return {Truth.TRUE: Truth.FALSE, Truth.FALSE: Truth.TRUE}.get(value, Truth.UNKNOWN)
