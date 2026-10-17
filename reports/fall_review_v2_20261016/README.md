# Requirement/checker decision package — fall review version 2

This is a new version. Both pilots, original responses, human-review records and the reviewed fall-review-v1 directory/ZIP are preserved unchanged. No LLM pilot, robot experiment, physics step, event checker or critic was run/built. Static kinematics is separate derived evidence only. The requirement and all event/support interpretations remain pending human approval/review.

Read **decision_table.md** first for findings, recommendations and blockers. The concrete decisions are initial support/study scope despite setup flight, indirect support, and whether table-origin history persists through robot carry until stable transfer. The interval is already explicit and no longer ambiguous.

## Deliverables

- requirement_v2.json: exact clarified interval, unchanged five-object list, three original proposal links and pending approval.
- measurement_findings_v2.md: targeted setup, timing, sources, corrected geometry and numerical findings.
- corrected_native_geometry_v2.json and corrected_entity_inventory_v2.json: full native IDs/derived inventory, preserving the old inventory.
- checker_specification_v2.md and proposed_rule_parameters.json: concrete proposed rules, four output categories and unset physical parameters; no floor-only definition or intent inference.
- examples/*.png, example_manifest.json, example_interpretations_provisional.json: four existing development runs, exact frames/times and separately labelled provisional interpretations.
- human_review/: blank initial-support, event and uncertainty forms; no human labels or identities entered.
- proposed_split.json and validation_and_review_v2.md: fixed proposed 40/10 split by run and the actual evidence/label limitations.
- synthetic_cases/: constructed case specifications kept separate from recorded robot evidence; no claimed detector validation.
- src/, tests/, fixtures/, test logs and source_evidence/: matching code, real small recorded excerpts, arithmetic/ID regressions, producer-verified and qualified dependency sources.
- settling_findings_by_run.json, targeted_measurements.json/.csv, constraints_and_identities.json: targeted physical traces/contact owners, not a repeated availability audit.
- static_reconstructions.jsonl, prepolicy_static_endpoint_geometry.json: separate non-dynamic kinematics with method/limitations, never replacement observations or contacts.
- source_provenance.json, external_source_references.json, preservation_before/after.json and PACKAGE_MANIFEST.json: source identities, original-data preservation and member hashes.

## Downstream integration contract

Use `src/native_geometry_v2.py` with the corrected native map/inventory. `NativeGeometryIndex` rejects legacy/truncated records and invalid run/XML/contact identities; `validate_snapshot_transforms` checks the coherent body/geom arrays without changing them or classifying events. No new code indexes a contact ID through legacy geom_names. The retained original collector/inventory is provenance, not a valid geometry-ID interface for the next checker.

The old inputs remain untouched. This versioned overlay is ready for the next checker to import; it does not install a checker into an active pipeline or create events/approvals.

## Reproduce the included tests

Requires Python 3.12+ and NumPy as pinned in requirements-tests.txt. No GPU, model weights, MuJoCo, original recordings or asset files are needed for the tests.

```bash
python3.12 -m venv .venv-test
.venv-test/bin/python -m pip install -r requirements-tests.txt
PYTHONPATH=src .venv-test/bin/python -m unittest discover -s tests -v
```

The real mapping/timing excerpts are explicitly recorded evidence; the corrupted-order test is artificial error injection. Tests check measurement/ID handling and pending-review safeguards, not fall-detection accuracy or robot safety.

## Reproduce targeted derivations on Hestia

Original recordings/assets, the retained original task/run inventory and parent audit are required. They are excluded from this ZIP. Reuse the pinned existing CPU environment `/local/home/niktakbr/rdt-1b-libero/.venv/bin/python` (Python 3.12.14; versions in requirements-targeted.txt). No dependency/environment/model changes were made. The code performs XML compilation and static kinematics but contains no physics stepping.

Point output at a **fresh directory**, copy proposed_split.json there before examining event windows, and run:

```bash
python src/targeted_investigation.py --project /local/home/niktakbr/trustworthy_project --output NEW_OUTPUT
python src/finish_targeted_evidence.py --project /local/home/niktakbr/trustworthy_project --output NEW_OUTPUT
python src/capture_source_provenance.py --project /local/home/niktakbr/trustworthy_project --output NEW_OUTPUT
python src/prepare_blank_forms.py --output NEW_OUTPUT
```

Create NEW_OUTPUT first. The scripts use the original source paths and parent audit; update paths only explicitly for a relocated copy. The second command adds endpoint static evidence, actual timing fixtures and the focused episode_014 sheet. The first command is a targeted settling/timing derivation, not a need to repeat the parent full availability audit. No fresh robot recording is generated.

The package excludes credentials, weights, environments and large robot recordings. Camera sheets are selected original images rotated for display; exact raw HDF5 references remain on Hestia. Nothing in this package supplies human approval or proves continuous safety.
