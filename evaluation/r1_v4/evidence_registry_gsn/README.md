# Versioned evidence registry and GSN scaffold — Phase 5A

This package implements deterministic, provenance-preserving evidence discovery and unresolved safety argument construction. It is not a safety certificate. Empirical V4 admission remains disabled.

## Components

| Module | Interface |
|---|---|
| models.py; registry_record.schema.json | Closed version 1.0.0 metadata envelope, content-addressed evidence IDs |
| registry.py; schema.sql | Persistent immutable SQLite index; atomic builder insert; read-only reopen; source and dependency integrity |
| retrieval.py | Exact scoped Query -> stable results, rejection reasons, dependency provenance, coverage gaps, uncertainty and capabilities |
| gsn.py; gsn_graph.schema.json | Typed nodes/edges, traceability, source and interval constraints, cycle detection, forbidden promotion |
| adapter.py | Existing unknown-truth V4 observation guard; hard-disabled empirical assessment adapter |
| builder.py | Approved development source -> compact index through the existing verified reader |
| demo.py; __main__.py | Executable R1 retrieval -> capability check -> unresolved assessment -> JSON graph and readable report |
| validate.py; tests/ | Synthetic boundary tests, real development integration, regression and preservation checks |

Reuses V4 canonical serialization and evidence types, reader validation, corrected complete native geometry mapping, and Phase 2B.4 gate statuses. Existing requirement-generation and empty claim/objection collections are preserved. The new schema is an explicitly namespaced metadata envelope; it does not redefine existing physical Evidence payloads. Registry and graph versions are 1.0.0, requirement version is 2.0.0, and existing configuration 2.0.1/assessment-manifest 1.0.0 contracts remain unchanged. This module does not manufacture an assessment manifest or invoke a physical checker.

The committed demonstration indexes one approved episode (000), frames 9, 10, 11, explicitly scoped to cream_cheese_1. Its 18 records comprise 15 raw measurement references (three each of object pose, native BOX geometry, contact, recorded timestamp, and camera reference), two source documents and one provisional AI interpretation. Geometry selectors include designated static table components and the object's native collision geometry. No anonymous native geometries are discarded from the underlying mapping.

The query requests all five measurement types through frame 12. It returns 15 structurally valid measurement records, reports frame 12 absent from this index for each type, and keeps the R1 claim unresolved. The AI review remains outside the measurement result set. Registry validation is a source/metadata capability; it does not validate load-bearing support, continuous physical coverage or a fall predicate.

Implemented: immutable versioned indexing, byte integrity, exact deterministic retrieval, dependency closure/conflict handling, metadata availability gaps, provenance-preserving graph export and unresolved assessment. Deferred: retrieval ranking/embeddings, cross-version migrations, multi-agent drafting and argument evaluation, cross-clock and dynamic composition. Blocked: empirical support inference, fall witnesses, qualified negatives, physical geometry/phase uncertainty and independent physical references. Camera exposure alignment remains unresolved/unsupported by recorded timestamps. No genuine in-scope R1 positive was verified in previous work.

See ARCHITECTURE.md for decisions recorded before implementation; REPRODUCIBILITY.md for commands and API trust boundaries; VALIDATION_REPORT.md and validation/RESULTS.json for the completed checks. The production database and duplicate-build outputs stay outside Git. demo/ contains compact source manifests, exports, unresolved graph and report only.
