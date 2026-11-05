# Deployment-blocked mock example

This is the documented mock fallback from the Drafter handoff. No model was run.
The example demonstrates how an existing requirement and archived evidence package
can be organized into the shared GSN format while keeping unsupported claims unresolved.

Open **scenario_a.mock.review.md** first for the readable argument.

- `scenario_a.mock.argument.json`: clearly labelled mock envelope and GSN graph bundle.
- `scenario_a.mock.run.json`: complete mock run record, including its plan and checks.
- `scenario_a.mock.review.md`: readable claims, evidence references and limitations.

All five protected objects remain in scope. Only cream cheese has eligible metadata
in the supplied package, at frames 10 and 11. Frame 12 and the other four objects
have missing metadata. Those gaps remain explicit. No initial physical support or
qualifying fall is established, so all safety conclusions remain unresolved.

The original evidence records and sources are unchanged. Fixed program rules build
the example; model identity is null and model execution is false. The graphs pass
the shared schema and graph validator. This does not establish model quality or
physical safety, and the mock envelope is not an accepted live `DraftArgument`.

Reproduce it from the repository root, using new output paths:

```sh
mkdir -p drafter/runs
python3 -m drafter --mock-demo drafter/cases/scenario_a.request.json \
  --out drafter/runs/scenario_a.mock.run.json \
  --argument-out drafter/runs/scenario_a.mock.argument.json \
  --review-out drafter/runs/scenario_a.mock.review.md
```

The run ID and timestamp change. The graph bundle and plan remain identical when
using the same generator code and input. A live model demonstration can be added
later when a suitable model server is available.
