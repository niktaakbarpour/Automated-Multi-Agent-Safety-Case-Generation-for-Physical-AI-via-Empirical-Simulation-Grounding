# R1 v3 Checker assessment and admission

The [versioned contract](contract.schema.json) defines the frozen Checker configuration, an admission request, independent review metadata, and the resulting assessment. The admission route works with the [R1 v3 evidence registry](../evidence_registry_gsn/R1_V3_REGISTRY.md).

## Inputs and scope

- A request names one execution, task, protected object, original trajectory SHA-256 and inclusive saved-frame interval. It binds one row of the original prediction JSON array, the prediction artifact SHA-256 and its output seal. The row must also match the frozen Checker configuration and implementation hashes.
- Measurement citations use R1 v3 registry IDs, a measurement type and explicit saved frames. The registry verifies the intersections with the requested scope and the initial-support stencil. Citations with native evidence bindings must agree on the simulator model and native body ID. The assessment retains the raw source, selected HDF5 paths, native map binding and verified frame times.
- Derived events remain distinct from measurements. An admitted violation cites the saved Checker event by JSON pointer and interval. The descent bracket must follow the support-loss bracket. A qualified negative requires the full declared saved-frame interval, including the Checker’s qualified static coverage. Scoped non-applicability requires the initial-support absence result. Coverage between saved frames remains unknown.

The assessment lists every required physical gate and its disposition. Its content hash covers the scope, configuration, prediction and seal hashes, evidence ledger, gate ledger and conclusion. A blocked assessment has a null conclusion and lists the outstanding checks.

## Trusted review

Use `development_diagnostic` for Task 5’s existing development result and other exposed predictions. Declared development or synthetic predictions and the archived development recordings always produce a blocked assessment.

A prospective assessment requires a coordinator-approved independent review. The review metadata binds the same request digest, declares the independently validated source group, and supplies a verification digest and verified evidence IDs for each of the nine gates. Each measurement-based gate checks the evidence types and saved frames in its own cited proof. The reported outcome determines which witness or coverage check applies to the case.

Compute the review’s `input_sha256` as `digest({key: value for key, value in request.items() if key != "review"})` using `evaluation.r1_v4.provenance.digest`. Deployment code must supply the independently approved review file SHA-256 in `trusted_review_hashes` from its own trusted configuration. The default set is empty. Keep evaluation-only human references outside the admission source root. Review receipts carry identifiers, verification hashes and evidence IDs.

## CPU API

```python
from evaluation.r1_v4.checker_v3_admission.admission import (
    assess, require_admitted_assessment, validate_assessment,
)

runtime = {
    "source_root": source_root,
    "registry": registry,
    "trusted_review_hashes": approved_review_hashes,
}
assessment = assess(request, **runtime)
validate_assessment(assessment, request, **runtime)

# The consumer boundary raises if the assessment is blocked.
verified = require_admitted_assessment(assessment, request, **runtime)
```

Use the same trusted review hashes at assessment creation and validation. Validation rebuilds the assessment from the pinned sources, current registry and trust policy. `require_admitted_assessment` is the consumer boundary for the subsequent Critic change.

Run the tests from the repository root with Python 3.12 and `requirements-m4-cpu.lock`.

```sh
python3 -m unittest discover -s evaluation/r1_v4/checker_v3_admission/tests -p test_admission.py -v
```

The tests exercise prospective admission with synthetic artifacts and check the blocked path against all 20 archived development predictions.
