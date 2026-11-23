# Saved Drafter response: serializer rejection receipt

## Artifact chain

The saved request is the repository fixture at drafter/cases/scenario_a.request.json; request SHA-256 is 0b88d922311b5bb6535b59f13c72b68fd053b566c22c7b8d0334690a8550a1ad. It is explicitly marked test_fixture=true and has no source-replay validation.

The prior run record identifies run ID 7ea617fa-5f97-4992-8588-ee4603f268d8. The associated saved artifact set is named:

- attempt-02.model-content.txt — original model text.
- attempt-02.model-plan.json — parsed plan.
- attempt-02.run.json — request hash, historical schema result, and serializer diagnostic.
- REAL_PLAN_AUDIT.json — plan counts and audit flags.
- attempt-02.stdout.json and attempt-02.argument.json — rejected result envelope; argument_bundle is null.
- attempt-02.review.md and attempt-02.model-plan.review.md — saved diagnostics.
- attempt-02.stderr.log — empty.
- request-validation.json — validates a fixture only; source replay was not performed.

The prior artifact-level report records the containing artifact directory and confirms it was left unchanged. These external run files are not copied into this repository. No traceback was saved; the rejection was recorded as a structured diagnostic.

## Failure classification

The historical plan passed JSON shape validation under graph-plan schema 0.1.0. It did not pass the graph-semantic contract: four supported_by edges target evidence registry IDs rather than declared graph-node IDs. The structured rejection includes plan_invalid_edge_endpoint:cream_cheese_1. The audit reports five graphs, 26 nodes, 25 edges, zero valid node evidence citations, and four evidence IDs used as edge targets.

Independent defects make a mechanical repair unsound: node statements and the summary are the single character R, limitations are [R], and proposed nodes lack usable evidence citations. Removing dangling edges or inserting citations would change the argument's substance and evidence support.

This is an invalid model response, not evidence of a serializer implementation defect or an interface mismatch. The historical request is also only a test fixture and is not a real empirical parent.

## Current implementation check

The repository's current graph-plan schema is urn:trustworthy:drafter-graph-plan:0.2.2; serializer version is graph-plan-to-gsn/0.2.0. Current validation checks graph semantics before serialization, and the targeted 42-test CPU suite passes endpoint, citation, prose, and ordering regressions. No validation was weakened or code changed.

The saved response cannot be converted into an accepted argument without substantive claim, graph, and source-evidence decisions. It remains rejected. A future approved execution needs a new request and a new model response, followed by all acceptance gates.
