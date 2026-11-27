# Task 8C source adapter for frozen R1 v3

This package contains the byte-preserved `task8c-r1v3-source-adapter-1.0.0` recovered from the Task 7B compatibility study. It reads the custom Task 8C HDF5 schema, verifies source and native-model bindings, and projects only the 258 frozen 20 Hz saved-frame endpoints into R1 v3 frame facts. It does not contain the human reference or prediction results.

The adapter emits measurements and geometry-qualified support facts; it does not emit a safety verdict. It preserves raw contact force values for provenance checks but the frozen R1 v3 decision logic does not use them as a load-bearing force measurement. Runner-provenance failures remain checker-ineligible.

The copied source files and recovered provenance are bound in [SOURCE_IMPLEMENTATION_BINDING.json](SOURCE_IMPLEMENTATION_BINDING.json). The original Task 7B freeze bundle and its cohort artifacts are not included; the binding file retains only the freeze hash needed to verify the recovered source files.

## Boundary with RegistryV3

RegistryV3 record schema **2.0.0** continues to validate the original recorder selectors under `/frames/<frame>/simulator/...`. A separate, explicitly versioned record schema **2.1.0** is implemented for this package's Task 8C custom layout under `/observations`, `/physics`, and `/contacts`. The new reader delegates reconstruction and source validation to this recovered adapter; it does not duplicate the reconstruction logic. See [the schema 2.1.0 specification](../evidence_registry_gsn/TASK8C_REGISTRY_V3_SCHEMA_2_1.md).

All 2.1.0 records are marked `development_only`. A valid hash-bound measurement citation is not a Checker event, an admitted assessment, a human judgment, or proof of physical safety. The nine existing physical admission gates and independent-review requirements remain unchanged; the admission evidence ledger blocks development-only records.

## CPU tests

With Python, NumPy, and h5py installed, run from the repository root:

```sh
cd evaluation/r1_v4/task8c_r1v3_adapter
python3.12 -m unittest discover -s tests -p 'test*.py' -v
```

The tests use synthetic HDF5 fixtures; the recovered original tests plus supplemental boundary tests are included. They do not read Task 8C labels or rerun Checker cohort predictions.
