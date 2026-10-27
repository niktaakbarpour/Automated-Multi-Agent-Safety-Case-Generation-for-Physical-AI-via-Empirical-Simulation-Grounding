# Frozen V3 transfer audit

Read `../../report/r1_v3_generalization_audit.md` and `PROTOCOL.json` first. The checker
is unchanged from delivery commit `d6657b8db2f9f91dad4931391b26ab88fee97a90`.
New-run results are predictions, not accuracy measurements: independent labels are pending.

## Available artifacts

- `INPUTS.json`, `catalog.json`: exact 10 reserved and 50 changed-task run IDs,
  original producer provenance, all 40 tasks and 38 other-task preflights.
- `FREEZE.json`, `HARNESS_FREEZE.json`: original checker/config/protected hashes and
  the separate harness/protocol/input freeze before execution.
- `inventory/inventory.json`: 102 rehashed recording/XML/metadata/native-index sets,
  identity, frame, model-attestation, duplicate-fingerprint and eligibility results.
- `execution/predictions.json`: all 300 immutable outputs, including events, proof
  windows and abstentions. Never regenerate or overwrite while summarizing.
- `execution/PREDICTION_SEAL.json`, runtime/access logs: code/config/output hashes,
  unchanged source receipts and zero extraction errors.
- `summary.json`: descriptive output coverage, duplicate checks and null accuracy metrics.
- `human_label_inventory.json`: inspected review sources contain only the original four
  run IDs, not new labels.
- `controlled_audit_results.json`, `TABLE_GEOMETRY_AUDIT.json`: separately identified
  synthetic scope-tag/rest-sensitivity probes and scene-table geometry concerns.
- `V4_PROPOSALS.md`: proposed improvements only; no V3 repair was made.

The **full blinded review archive and 60 larger checker-fact gzip files remain on
Hestia**, not in Git. `blinded_review/` here is a compact mirror of 15 forms/manifests,
not a standalone evidence package. Reviewers need the complete archive with all 1,200
media/neutral-measurement files. Do not distribute the parent audit folder or automated
outputs to reviewers. No reviewer has been messaged automatically.

Full archive:

```
/disk/1/data/niktakbr/r1-v3-generalization-20261027/blinded-review-20261027.tar.gz
```

316,311,367 bytes, SHA256:
`b693f26844fa0cfbf4dd264a55cd8c1c302ea5be1af61f79eb85343b32239200`.
Use the user's existing two-hop SSH transfer to retrieve it. The full archive has
60 verified full videos, 300 blank object entries per reviewer and no predictions.
`REMOTE_VERIFICATION.json` verifies all 63 inference artifacts, 1,214 review-package
hash entries and empty human answer fields. The archive should be supplied in full
before review and original human submissions must be preserved unchanged.

## Local summary and tests

From repository root, use a new output path:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_v3_generalization/summarize.py \
  --root evaluation/r1_v3_generalization \
  --output /tmp/r1-transfer-summary-new.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s evaluation/r1_v3_generalization/tests -v
```

Summary verification checks all copied sealed JSON artifacts. It explicitly lists the
60 remote-only fact files. No absent reference or fact file becomes a negative decision.
The full seal was separately verified on Hestia. Accuracy/confusion/localization fields
remain null until an independently reviewed, approved new reference exists.

## Reproduce source inventory and frozen inference on Hestia

The actual separate harness staging root is:

```
/disk/1/data/niktakbr/r1-v3-generalization-20261027
```

It contains these harness/input files. The original V3 and baseline utility sources
remain in their previous isolated staging roots. Use the existing Python environment;
no installation, model inference, GPU job or simulation stepping is required. Set shell
cwd `/`, HOME `/tmp`, and ordinary OS PATH as shown. Choose new output directories:

```sh
cd /
HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python \
  /disk/1/data/niktakbr/r1-v3-generalization-20261027/run.py inventory \
  --v3 /disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3 \
  --release /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017 \
  --output /disk/1/data/niktakbr/r1-v3-generalization-20261027/inventory-new

HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python \
  /disk/1/data/niktakbr/r1-v3-generalization-20261027/run.py run \
  --v3 /disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3 \
  --release /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017 \
  --inventory /disk/1/data/niktakbr/r1-v3-generalization-20261027/inventory-new \
  --output /disk/1/data/niktakbr/r1-v3-generalization-20261027/execution-new
```

Actual outputs used directory names `inventory` and `execution`. `run.py` hashes source
HDF5/XML/metadata/index files, checks run/task/model identity and timeline, registers new
IDs only against identical XML/body/entity mappings, invokes the original functions,
and seals all outputs before the summary. It records every missing/invalid selected run
as insufficient information, not a pass. Other-scene ineligible preflights are not
pretended to be valid inference cases. The two long tasks have the same XML; no geometry
IDs are transferred to a different scene.

## Reproduce the evidence-only export

The staged `review_protocol` directory holds byte-identical scope documents and the
neutral object guide. The exporter imports no checker and reads no predictions:

```sh
HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /local/home/niktakbr/rdt-1b-libero/.venv/bin/python \
  /disk/1/data/niktakbr/r1-v3-generalization-20261027/build_review.py \
  --inventory /disk/1/data/niktakbr/r1-v3-generalization-20261027/inventory \
  --protocol /disk/1/data/niktakbr/r1-v3-generalization-20261027/review_protocol \
  --geometry /disk/1/data/niktakbr/r1-reference-evaluation-20261027/reports/fall_checker_dev_v2_20261017/corrected_native_geometry_v2.json \
  --output /disk/1/data/niktakbr/r1-v3-generalization-20261027/blinded-review-new
```

Every video retains all original saved frames and both camera views, rotated 180 degrees
without cropping/interpolation. Captions are outside the images. ffprobe verifies frame
count and 20-fps rate. Complete poses/contacts/geometry and raw image hashes are neutral
measurement exports. Frame 0 and 8--13 images support boundary review; no event-dependent
windows are selected. Source SHA256/size/mtime are unchanged before and after export.
`REVIEW_EXPORT_FREEZE.json` records exporter/instruction hashes before the export.

New reference creation requires two independent human submissions, frozen originals,
third-researcher adjudication and approved final JSON labels. Follow the handoff's
claim-specific coverage, uncertainty and strict/one-frame event matching protocol.
Do not reuse the V3 development scorer as if it handled arbitrary positive references;
it deliberately rejects new positive-reference semantics. Freeze a separate positive-capable
comparison harness when new approved labels exist. No generated proposal is a substitute.
