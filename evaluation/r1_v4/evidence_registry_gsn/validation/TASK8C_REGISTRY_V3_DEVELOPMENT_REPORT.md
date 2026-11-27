# Task 8C RegistryV3 development verification

**Status:** development-only source-reader verification; not an independent evaluation or physical admission.

One existing Task 8C matched pulse/sham source group was used. Both original recording byte streams matched exactly one row in the authoritative source manifest, and both had verified capture-runner bindings under the existing runner audit. The source records remained on private Hestia storage; no recording, per-case identifier, coordinator mapping, or human-review material is included here.

The recovered Task 8C source adapter validated the complete custom HDF5 inputs, native model bindings, contact arrays, saved-frame/native-sample mapping, and timestamps. RegistryV3 record schema `2.1.0` registered eight raw source records: object pose, reconstructed native geometry, contact observations, and timestamps for each recording. Eight citations scoped to the exact execution, protected object, source hash, measurement family, and saved frames 10–257 resolved against those records.

The admission evidence ledger blocked both recordings with `development_only_source`. This is the expected result. No Checker prediction or human reference was read or created; no physical gate review or empirical assessment was attempted. These records cannot be used as independent validation or evidence of physical safety. RegistryV3 2.0.0 behavior and all nine admission gates remain unchanged.

## Reproduction boundary

Run the synthetic CPU regressions from the repository root using Python 3.12 with the locked CPU dependencies:

```sh
python3.12 -m unittest evaluation.r1_v4.evidence_registry_gsn.tests.test_registry_v3_task8c -v
python3.12 -m unittest evaluation.r1_v4.evidence_registry_gsn.tests.test_registry_v3 -v
python3.12 -m unittest evaluation.r1_v4.checker_v3_admission.tests.test_admission -v
```

Reproducing the real-recording demonstration additionally requires authorized access to the private Task 8C HDF5 recordings, their source manifest, runner-binding audit, and the hash-pinned simulator/configuration artifacts. Those inputs are intentionally not redistributed in this repository. The one-pair development demonstration was run in the existing Python 3.12 CPU environment; it did not run model inference, Checker scoring, or human evaluation.
