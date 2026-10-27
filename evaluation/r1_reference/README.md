# Reproduce the bounded R1 development evaluation

Read `../../report/checker_reference_evaluation.md` first. This is an abstaining requirement adapter around an unchanged candidate checker. It does not establish checker accuracy.

## Score the sealed predictions locally (standard-library Python)

From the repository root, choose a **new** output filename:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_reference/score.py \
  --execution evaluation/r1_reference/execution \
  --reference human_review_package/adjudication/approved_reference/r1-reference-be76abc531f5c716efca \
  --output /tmp/r1-reference-reproduction.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s evaluation/r1_reference/tests -v
```

`results.json` is the actual computed comparison. The scorer checks the prediction seal before loading answers, requires final approved JSON labels, verifies the immutable reference's own checksums and the pre-execution protected-file hashes, and rejects incompatible identities, versions, provenance and unsupported determinate claims. It refuses to overwrite its output. All 20 units and all final event labels are retained. The scorer is intentionally restricted to adapter v1; extending the decision policy requires a new version and frozen evaluation.

`protocol.json` was fixed before predictions. `baseline_freeze.json` records exact baseline parameters, source hashes, checker-introduction commit, historical dirty-source provenance and protected-file hashes. `recordings.json` contains label-free run/frame/hash identities copied from the evidence manifest. `run_frozen.py` has no reference-answer inputs. It emits all 20 records and seals raw outputs, predictions, runtime and before/after receipts. The base config is unchanged; existing sensitivity outputs are diagnostic only.

## Repeat original-recording execution on Hestia

Use the connect-ssh workflow and the existing runtime. Work in the isolated owned disk1 staging directory (already created for the actual execution). The staged runner and baseline files have the same hashes as their repository counterparts. Use a **new** output directory:

```sh
cd /
HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python \
  /disk/1/data/niktakbr/r1-reference-evaluation-20261027/evaluation/r1_reference/run_frozen.py \
  --release /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017 \
  --output /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reproduction-new
```

The actual run used the same command with output directory `predictions`. Its eight original inputs are `episode_{000,001,002,014}/{trajectory.h5,simulator.xml}` under:

```
/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero/long/task_00
```

No original file is opened writable. Input hashes must match before execution. Each run's native XML identity, geometry count, inventory and per-frame transforms are checked by the frozen runner; no legacy native-ID fallback exists. A temporary view narrows only the run selection from the original development split. Physics and model inference are never run. Existing strict/broad profiles execute unchanged, and no threshold tuning occurs.

Original checker tests on the staged release:

```sh
cd /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017
HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python -m unittest discover -s tests -v
```

The actual logs are `baseline-tests.log` (42 passing) and `tests.log` (17 passing). Software tests verify contracts and execution behavior, not physical detector validity.

## Artifact availability and limits

`execution/PREDICTION_SEAL.json` was saved remotely before CSV answers were read. All copied JSON files match its hashes. Eight large `raw/*_geometry_contacts.json.gz` / `raw/*_observations.json.gz` artifacts remain on Hestia at the actual execution output above. The seal records their hashes; the scorer explicitly reports their absence locally and verifies them if copied. It does not infer results from absent artifacts or recordings. The compact raw per-object JSON and predictions contain the actual evidence used in comparison.

All physical candidates remain provisional. Measurement intervals and human-reviewed claim coverage have different meanings; the adapter does not equate them. Scoring reports empty binary denominators, abstentions and non-applicability rather than inflating true negatives. Unknown physical fall status and known R1 non-applicability can coexist. The matcher is tested independently, but with zero eligible R1 events neither strict nor one-frame localization performance is estimable.
