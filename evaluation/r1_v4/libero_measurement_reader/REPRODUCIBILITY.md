# Reproduce on Hestia

Repository: /disk/1/data/niktakbr/trustworthy-phase16. Baseline ace3ef3becd0c2ce2d9cb45488707bf2101ce384. Branch feat/r1-v4-libero-measurement-reader. All research processing must run on Hestia; no GPU or simulator is needed.

Use system Python3.12 with the existing owned h5py/numpy/jsonschema packages and -S to avoid unrelated .pth startup hooks. No installation or environment activation is required:

```sh
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/disk/1/data/niktakbr
export PYTHONPATH=.:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages
python3 -S -m unittest discover -s evaluation/r1_v4/libero_measurement_reader/tests -v
python3 -S -m evaluation.r1_v4.libero_measurement_reader --root /disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence --episode 0 --frames 0 10 --output /disk/1/data/niktakbr/NEW-reader-output.json
python3 -S -m evaluation.r1_v4.libero_measurement_reader.validate
```

The validator runs the 44 reader tests and relevant Phase2A/frozen V3/reference/generalization suites, scans all four restored recordings, checks CLI/library byte identity, hashes every restored input before/after, and verifies frozen integrity plus every Phase2B.1 artifact digest. It writes compact reports to this new package and retains its CLI example outside Git. Repeating the exact version checks the existing CLI example rather than overwriting it. After an intentional reader-code change, use a fresh demonstration filename and review new code bindings.

RESTORED_SOURCES.json is the authoritative completed restoration result. Production CLI accepts only the four official hash-bound bundles at an owned disk1 root. Synthetic test injection is a library-only API requiring synthetic=True and preserves the synthetic marker; it is not a way to register an empirical profile.

Tests create small explicit synthetic HDF5 measurement fixtures in temporary owned disk1 directories, with native-map-consistent arrays and no simulated physics. They copy only approved metadata/reference files for fixture construction. Their separately resealed producer manifests are private synthetic fixtures, never historical manifest replacements. Defect mutations test hash failures or, after explicit synthetic re-sealing, downstream structural failures. Raw original files are never opened for writing.

## Selective restoration provenance

RESTORATION_PLAN.json records the exact transfer archive/member mapping. The original transfer manifest was scanned on Hestia; published receipts and current archive availability were checked. An authenticated Fir storage connection performed native selective tar reads only. Transport relayed bytes through the Mac without local analysis. restore_receive.py ran on Hestia, accepted only selected members/sizes, exclusively created new disk1 paths, and hashed payloads. Receiver receipts remain at the evidence root. Thirty-seven expected digests matched; the additional initial-state archive was resolved against verified run_metadata.json.

Do not blindly rerun restoration over existing data: the receiver refuses existing files. For a separately authorized fresh restoration, verify archive availability and selection, prepare a new destination, reuse supported authenticated storage access, and preserve exact member identity and receipts. No full archive, held-out run or unrelated sidecar should be retrieved. Archive-container digests in the plan are historical publication records; per-member hashes here are fresh.

No recordings/videos belong in Git. The final artifact manifest contains exact file hashes; the final commit binds that manifest. Existing broad-suite baseline failures documented by Phase2A are outside this selected regression run and are not claimed repaired.
