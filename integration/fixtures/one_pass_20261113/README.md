# One-pass Qwen Drafter/Critic fixture

This package contains the saved real-model Drafter argument, Critic request, two Qwen Critic reports/messages, and a separately labeled controlled guarantee mutation. It is one development fixture and is not a new independent physical-source experiment.

## CPU verification

From the repository root, run:

```sh
python integration/verify_saved_fixture.py
```

The verifier checks the eight files listed in `MANIFEST.json` against their committed byte counts and SHA-256 values. It validates both Critic requests and reports with the current repository schemas, runs the current deterministic Critic input checks, binds each saved report to the request and execution, and checks that the saved Drafter argument bundle matches the original Critic request. It makes no model or network calls.

The historical manifest records schema validation as unavailable in an earlier checkout. The current repository does include these schemas and validators, so the current CPU checks are now possible. This verifier does not pretend to reconstruct the original Drafter validation run: the original Drafter request and generation report are not present in this fixture.

## Saved model result and interpretation

Both saved Qwen Critic reports completed with zero criticisms, including the controlled unsupported guarantee. The mutation is a controlled prose edit, not a second generated argument. The current deterministic Critic flags that guarantee, but this later rule result is distinct from and does not rewrite the historical Qwen response. The original result remains a model false negative on one deliberately constructed control, not an estimate of population recall.

The fixture uses `test_fixture=true`. Its source measurements and initial real model calls were reported in `integration/END_TO_END_QWEN_INTEGRATION_REPORT.md`; this Git package is a saved-output fixture, not a self-contained source recording. The full source recordings, original Drafter request/run envelope and runtime trace are external. A zero-finding report does not establish safety.
