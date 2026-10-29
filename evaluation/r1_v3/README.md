# R1 evidence checker v3

Read `DESIGN.md` and `../../report/r1_v2_vs_v3_evaluation.md`. This is development
software evaluated on known selected cases, not a validated general safety detector.
Source was frozen at `a357557aac457a5cecb1ee8372f70fb12d796cdd`, based on preservation
commit `9902c788156370df985ee936473a2c294e62ea26`. No inference source changed after freeze.
The scorer and additional regression tests were added after predictions were sealed.

## Compare sealed outputs locally

From repository root, choose a **new** output filename:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_v3/evaluate_reference.py \
  --execution evaluation/r1_v3/execution \
  --reference human_review_package/adjudication/approved_reference/r1-reference-be76abc531f5c716efca \
  --output /tmp/r1-v3-comparison-new.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s evaluation/r1_v3/tests -v
```

The scorer verifies sealed JSON, implementation/configuration, recording identities,
original-file receipts and protected hashes before reading final reference JSON labels.
Its compatibility rule is the explicitly declared shared saved-frame projection, not
assumed continuous-time/video equivalence. Non-applicability, abstention and partial
coverage are excluded from binary counts. Compound events, reviewed fragments and
uncertainties remain in `results.json`. Strict and one-frame physical localization
is reported separately from R1 events. No positive R1 reference examples exist.

`execution/predictions.json` is immutable; never regenerate or overwrite it during
scoring. `FREEZE.json` binds the committed inference source; `PREDICTION_SEAL.json`
binds actual outputs. All CLIs refuse to overwrite their output path/directory.

## Original-recording execution on Hestia

The actual isolated staging root is:

```
/disk/1/data/niktakbr/r1-checker-v3-20261027
```

It contains the frozen `evaluation/r1_v3` source, label-free v2 manifests under
`evaluation/r1_reference`, and actual output `execution`. The original baseline
measurement utilities remain in their prior isolated staging directory. Using the
existing SSH session/runtime, choose a **new** output directory:

```sh
cd /
HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python \
  /disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3/execute.py \
  --release /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017 \
  --output /disk/1/data/niktakbr/r1-checker-v3-20261027/reproduction-new
```

The actual run used output `execution`. It read exactly the four manifest recordings
and XML files at the original v2-config data root. It did not step simulation, invoke
a model, install packages, submit a GPU job or modify source recordings. Python
3.12.14, numpy 2.5.3 and h5py 3.16.0 were the existing runtime. Each run is checked
against its own run/task identity, XML hash, full native mapping and transform/timing
records before evidence is admitted. Unknown mappings or missing contacts cannot
become support proof. All original SHA256/size/mtime receipts matched after the run.

Four `episode_*_facts.json.gz` files remain in the remote output directory; they are
not committed because they are larger derived evidence. The seal records their exact
hashes. The local scorer explicitly lists missing remote-only facts and verifies them
if present; it requires every sealed JSON artifact. It never substitutes missing
recordings or facts with fabricated predictions.

## Test and replay commands

Local: 33 v3 tests pass, with 8 numpy/h5py integration cases skipped. On Hestia the
frozen controlled suite ran all 31 tests, including those 8, with no skips:

```sh
HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
R1_BASELINE_RELEASE=/disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python -m unittest discover \
  -s /disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3/tests -v
```

The remote staging tests are the 31 pre-freeze controlled tests; the 10 post-seal
recorded/scoring tests live in this checkout and were run locally. There are 41
distinct passing v3 tests across the two environments (23 overlap). Baseline 42
checker and 17 evaluator tests remain unchanged and pass separately. Tests do not
establish empirical physical truth or positive-class detection recall.

`replay.py` verifies all facts and output hashes and compares recomputed core results
without reference inputs. It needs the four remote facts. The replay utility is also staged on Hestia. Use it there, or run it with a complete
local evidence copy:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_v3/replay.py \
  --execution /path/to/complete/execution \
  --output /tmp/r1-v3-replay-new.json
```

Both the direct frozen-core replay and this exact CLI reproduced all 20 outputs on
Hestia. Their reports are `replay-verification.json` and `replay-cli-verification.json`.

LaTeX-ready manuscript text: `../../report/r1_midpoint_results.tex`.
The final verification and full changed-file inventory are provided alongside results.
