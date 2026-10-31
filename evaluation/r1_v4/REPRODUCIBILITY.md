# Reproduce Phase 2A on Hestia

Start from baseline `609ac744b1b2fb899c783de5bb3df3c39943f57e` plus this implementation
commit. Execute from the repository root on Hestia. Python 3.12.14 and the existing
jsonschema 4.19.1 installation were used; no packages were installed. Required new
artifacts belong on owned `/disk/1`; Alliance is archival/storage only.

```sh
export HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONDONTWRITEBYTECODE=1 TMPDIR=/disk/1/data/niktakbr
python3 -m unittest discover -s evaluation/r1_v4/tests -v
python3 -m evaluation.r1_v4.demonstrate --output-dir /disk/1/data/niktakbr/NEW-phase2a-demonstrations
```

To rerun the complete pipeline, use a clean detached baseline checkout at the exact
baseline commit and a new output directory:

```sh
python3 -m evaluation.r1_v4.validate --output-dir /disk/1/data/niktakbr/NEW-phase2a-validation --baseline-root /disk/1/data/niktakbr/trustworthy-phase2a-baseline --legacy-site-packages /disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages
```

The existing owned package directory provides numpy/h5py for frozen regressions;
`-S` prevents unrelated startup .pth hooks from executing. No environment is activated
or modified. Core V4 uses jsonschema/standard library only. Exact commands/env are
recorded in results. MuJoCo is unavailable; seven old compiler-based geometry tests
skip. No simulator stepping occurs.

Fixture generation refuses existing files. After intentional source/contract changes,
regenerate into a fresh directory and deliberately review new bindings:

```sh
python3 -m evaluation.r1_v4.fixtures --output-dir /disk/1/data/niktakbr/NEW-synthetic-fixtures
python3 -m evaluation.r1_v4.demonstrate --fixtures-dir /disk/1/data/niktakbr/NEW-synthetic-fixtures --output-dir /disk/1/data/niktakbr/NEW-synthetic-results
```

Checked-in fixtures bind the final checker/contract inventory. Code drift must fail
admission until fixtures are deliberately regenerated. `build_artifacts.py` rebuilds
versioned schema/profile definitions deterministically; normal runs only read them.
Never regenerate historical V3 artifacts.

## Demonstrations

1. `synthetic/three_object_violation.json`: declared V, qualified N and NA; aggregate V.
2. `synthetic/five_object_uncertain.json`: N, NA, U, verified absent NA and IC;
   aggregate IC, with absence study eligibility pending.
3. `synthetic/multiple_static_surfaces.json`: three objects with explicit two-root
   unions and source/dependency chains; qualified N at the declared cell projection.

These are exact synthetic ledgers, not LIBERO observations or simulation runs.
CLI/library assessments serialize byte-identically. Summaries record input/output
hashes, commands and expected outcomes. No empirical performance metric is produced.
Final demonstration artifacts are in `validation/demonstrations/`.

## Legacy limitations

The broad existing suite reproduces the same two failures, one error and seven
skips at the untouched baseline. They concern an old missing pilot config, a
filesystem-count assumption and an already prefilled human-review template. Historical
data, protected forms and scoring safeguards were not changed to make tests pass.
All 41 frozen V3 tests pass using the existing h5py package. The complete existing
suite is explicitly not reported as green.

The supplementary reference/generalization/provenance/verification suites are included
in the full validator. Human-validation adds one baseline-identical missing historical
report error; its other 26 tests pass. Details and logs are in
`validation/SUPPLEMENTAL_REGRESSIONS.json` and `VALIDATION_REPORT.md`.
