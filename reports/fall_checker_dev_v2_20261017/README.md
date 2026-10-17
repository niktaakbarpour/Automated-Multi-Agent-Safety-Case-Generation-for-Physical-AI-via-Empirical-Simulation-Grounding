# Development checker v2 — focused corrections, 20261017

**PROVISIONAL OUTPUTS; UNAPPROVED REQUIREMENT; UNVALIDATED DETECTOR.** Software tests do not validate event detection. This release preserves the reviewed development release, pilots, audits, recordings, and human-review records. Physical thresholds and split are unchanged.

Changes: both endpoints of every counted descent interval must be valid and contact-free; active events accumulate geometry evidence with a classification history; event spans, endings and censoring are explicit; per-frame observation construction is atomic across all objects/profiles.

Run focused plus inherited tests:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Reassess using the **previous release's saved extracts** (fresh output directory required):

```sh
PYTHONDONTWRITEBYTECODE=1 python src/reassess_extracts.py \
  --root . --previous-release ../trustworthy-fall-checker-dev-20261017 \
  --output reassessed_outputs
```

The previous release must contain its outputs/*_geometry_contacts.json.gz, PACKAGE_MANIFEST.json, summary.json, and source checker.py. These are in the prior downloaded ZIP or its Hestia release directory. This ZIP excludes those large unchanged geometry extracts; their exact hashes and paths are in outputs/access_log.json. It includes revised observations for all profiles, so the final detector assessments can also be recomputed directly with checker.analyze without opening geometry extracts, HDF5, or robot recordings. Python/numpy/h5py are needed for the adapter and tests; the existing Hestia runtime is reused without dependency changes. No model weights, environments or credentials are included.

Read CHANGE_REPORT.md and REVIEW_GUIDE.md. The full per-object/per-profile comparison is in outputs/before_after.json. Persistence-only ablation uses the exact prior source with only its endpoint predicate corrected, separating the two detector fixes. The full fix additionally updates event evidence and records censoring. Human forms remain blank and predictions remain in outputs. No final requirement decisions are entered.
