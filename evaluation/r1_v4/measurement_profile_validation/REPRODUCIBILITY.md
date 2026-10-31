# Reproduce on Hestia

Baseline 51cf76ad47bccff9f6a4de1c3651141f1e5c954b, branch feat/r1-v4-measurement-profile-validation. Run from /disk/1/data/niktakbr/trustworthy-phase16. Existing packages only; no install, simulator or GPU job is required.

```sh
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/disk/1/data/niktakbr
export PYTHONPATH=.:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages
python3 -S -m evaluation.r1_v4.measurement_profile_validation.analyze
python3 -S -m evaluation.r1_v4.measurement_profile_validation.gates
python3 -S -m evaluation.r1_v4.measurement_profile_validation.calibration
python3 -S -m evaluation.r1_v4.measurement_profile_validation.prepare_candidates
python3 -S -m evaluation.r1_v4.measurement_profile_validation.validate
```

The analyzer verifies38 original digests and prior audit/reader manifests, checks baseline bindings, and computes a diagnostic pass. Full rows remain at /disk/1/data/niktakbr/r1-v4-phase2b3-working/object_geometry_contacts.csv; selected rows/summaries are committed. Rebuilding updates this package and owned generated files, never originals or historical contracts. SOURCE_BINDINGS.json records input and full-table hashes.

To recreate Hestia-only camera sheets, run `python3 -S -m evaluation.r1_v4.measurement_profile_validation.references`. It extracts 24 selected arrays, rotates/resizes for display and records raw/derived hashes. It does not visually inspect images, synchronize exposure, export them or authorize transfer. Image transfer was automatically rejected and remains pending explicit permission.

The validator runs profile, Phase2A, reader, frozen V3, reference and generalization tests. It checks originals before/after, prior artifact digests, code bindings and frozen live sources/predictions/seals/scoring safeguards. Logs, commands and counts are in validation/RESULTS.json. The broader historical suite is not claimed repaired or fully rerun.

Exact rational tests cover 27 constructed BOX cases and 648 coordinates. They test arithmetic enclosure, not physical calibration or empirical reference labels. Physical bounds remain null. Gate reports cannot activate an empirical profile.

ARTIFACT_SHA256.json inventories compact deliverables except itself; Git binds that manifest. Raw recordings/media, full tables and sheets remain outside Git. No restoration, original alteration or deletion occurred. Alliance/Sea were not used; computation stayed on Hestia.
