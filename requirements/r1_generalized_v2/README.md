# Generalized R1 specification v2.0 — finalized restricted design

Status: **restricted design finalized in Phase 1.6; no V4 implementation**.
Design authority is the user's Phase 1.6 directions; calibration and independent
validation remain pending. Start with the
[finalized contract](finalization/FINALIZED_R1_V2_CONTRACT.md) and
[decision register](finalization/DECISION_REGISTER.md). Archived decision_review
and earlier QA records describe prior versions and do not override this contract.
Configuration schema is now 2.0.1; requirement meaning remains 2.0.0.
Baseline: `30b4ac9cc8e2a1d0e83f72ee74d31f77829e62c1`.
Requirement identifier: `R1`; generalized version: `2.0.0`. This namespace is not
the historical checker V2, checker V3, or `draft-non-target-table-falls-v2-20261016`.

This package specifies a configurable initial-support fall-prevention claim. It
does not provide a functioning generalized checker, benchmark validation, a new
evaluation reference, or evidence that an additional scene is supported.

Read [R1_V2_SPECIFICATION.md](R1_V2_SPECIFICATION.md) first. Normative precedence is:
that document and [FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md), then their explicitly
referenced applicability/fall/evidence rules. The JSON Schema defines structural
configuration validity, not empirical evidence validity. Other documents are audit,
examples, compatibility analysis and plans, and cannot override normative rules.
Any conflict is a specification defect to resolve before V4 implementation.

| Document | Purpose |
|---|---|
| [CURRENT_R1_AUDIT.md](CURRENT_R1_AUDIT.md) | Exact source audit and assumption classification |
| [R1_V2_SPECIFICATION.md](R1_V2_SPECIFICATION.md) | Normative intent, scope and invariants |
| [FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md) | Multi-valued predicates, coverage and aggregation |
| [APPLICABILITY_RULES.md](APPLICABILITY_RULES.md) | Identity/precondition decision table |
| [FALL_DEFINITION.md](FALL_DEFINITION.md) | Event meaning, exclusions and temporal boundaries |
| [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md) | Claim-specific measurement requirements |
| [R1_V2_CONFIG_SCHEMA.json](R1_V2_CONFIG_SCHEMA.json) | Revision 2.0.1 Draft 2020-12 schema |
| [EXAMPLE_CONFIGS/README.md](EXAMPLE_CONFIGS/README.md) | Illustrative configurations, including restricted static BOX fixture |
| [V3_COMPATIBILITY.md](V3_COMPATIBILITY.md) | Frozen-history preservation and migration limits |
| [V4_IMPLEMENTATION_PLAN.md](V4_IMPLEMENTATION_PLAN.md) | Interfaces and engineering sequence only |
| [V4_TEST_MATRIX.md](V4_TEST_MATRIX.md) | Future analytical/integration acceptance tests |
| [VALIDITY_THREATS.md](VALIDITY_THREATS.md) | Limits of generalization and evaluation |
| [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | Current dispositions and archived approval questions |

All examples are illustrative and unvalidated, including the historical-scene
mapping under the new semantics. No calibration values are invented. Physics,
geometry, clock and adapter certificates must be established before empirical use.
Arbitrary configuration cardinality is not evidence of arbitrary-physics support.

QA tooling in `validate_spec.py` checks this documentation/schema package only; it
does not classify executions or implement any proposed V4 module. Run it on Hestia
with the existing `jsonschema` installation. The QA report records the actual checks,
test outcomes and accessible frozen-artifact hashes. No Alliance computation is used.
