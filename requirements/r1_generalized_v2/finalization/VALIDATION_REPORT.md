# Phase 1.6 validation report

Research QA is executed on Hestia using the existing Python/jsonschema installation.
Final results: PASS. Machine results and exact checks are in VALIDATION_RESULTS.json
and SPEC_QA_RESULTS.json in this directory. Four examples, 33 configuration fixtures,
92 relative links, 16 audited baseline sources, all 14 archived review files and
55 planned acceptance cases (13 restricted additions) pass their applicable checks.
No V4 event tests or empirical validation are claimed.

Review covered the exact D01–D11 Markdown/CSV matrix, pending approval checklist,
eight proposed amendments, formal predicates, conflict admission, aggregation,
scope/censoring, negative cells/joins and version bindings. Manual semantic review
confirms the narrow initial-support/downward hazard, handling distinctions and
conservative unresolved suffix. Automated schema/document checks cannot prove
physical semantics or an adapter's accuracy.

The validator checks Draft 2020-12 meta-schema, all four illustrative examples,
negative configuration mutations, manifest fields/consistency, relative links,
decision and amendment/test coverage, and absence of invented example calibration.
The original QA's audited baseline source hashes, four live frozen V3/prediction
hashes, two historical evaluation seals and every sealed member, and eight human
scoring protected files are rechecked. Review/source-binding/old QA bytes must match
the Phase 1.5 baseline; changes are confined to this specification subtree.

No V4 implementation, simulations, new physical labels, RAG/multi-agent code,
recording edits, historical evaluation edits, Alliance computation, push or merge.
Calibration and independent empirical validation remain BLOCKED_ON_EVIDENCE.
Exact changed files and commands are recorded in VALIDATION_RESULTS.json.

## Manual formal/aggregation review

| Admitted object vector or evidence condition | Contract conclusion reviewed |
|---|---|
| [] | empty_scope / NA; excluded, no vacuous safety pass |
| [NA, NA] | NA; neither row a TN |
| [N, NA] | qualified N over applicable object, NA retained |
| [N, U, NA] | U |
| [N, IC] | IC |
| [V, NA] | V |
| [V, U] or [V, IC] with independent valid V foundation | V plus incomplete evidence |
| Candidate V with same-event unresolved admissible contradiction | Dependent witness suspended; U, absent another independently admitted V |
| Candidate V with proven incompatible essential shared foundation | Dependent claims IC, no admitted V from that foundation |
| Boundary-censored episode or missing negative join cell | U absent independently admitted V; no full-domain N |

N denotes no_violation_observed_within_validated_coverage, V an admitted
violation_observed. This table documents review of the specified algebra; no V4
aggregation function or physical checker is implemented or executed. Permuting rows
cannot change precedence, and cardinality never changes the event predicate.

All four frozen V3/prediction hashes, both historical evaluation seals and their
members, and all eight human-scoring protected files matched the expected hashes.
Unknown calibration remains null in every example; no numeric physical tolerance,
contact threshold, alignment window or persistence default was introduced.

Operational note: work was moved to /disk/1 after discovering the documented
/disk/0 staging restriction. A failed cross-device git-worktree move left the shell
at /; a subsequent directory search briefly ran there before being interrupted.
That was an unintended out-of-scope traversal, not project work. No ISSTA or Sea
file contents were deliberately opened; the task made no edits there. The worktree
was moved and repaired on /disk/1; all subsequent edits/QA ran within it. Existing
experiments/controllers were not interrupted. No Alliance access was needed.
