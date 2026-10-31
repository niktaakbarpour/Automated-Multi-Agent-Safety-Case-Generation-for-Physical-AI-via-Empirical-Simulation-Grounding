# Reproduce Phase 2B.4 on Hestia

Baseline f15d3a9da13e535db49b19f023f762824b4ea26c. Worktree /disk/1/data/niktakbr/trustworthy-phase16; branch feat/r1-v4-evidence-review-readiness. Original source and complete numerical tables stay on Hestia. The only image transfer was the explicitly authorized three JPEGs into the current Codex session.

```sh
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/disk/1/data/niktakbr
export PYTHONPATH=.:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages
python3 -S -m evaluation.r1_v4.evidence_review_readiness.review_sources
python3 -S -m evaluation.r1_v4.evidence_review_readiness.assessments
python3 -S -m evaluation.r1_v4.evidence_review_readiness.update_gates
python3 -S -m evaluation.r1_v4.evidence_review_readiness.validate
```

review_sources verifies prior manifests and all 38 original source digests, inspects the ten numerical case windows, cross-checks native contacts/BOX unions and preserves exact visual-source/frame/camera/snapshot-time metadata. C04 stays unfilled. Root/finger-collision-center comparisons are numerical indicators, not holding/fall classifiers. Full datasets are never exported or committed.

assessments materializes the authored AI observations from this review. Re-running Python is not another visual analysis or independent review. update_gates records unchanged dispositions and minimum additional evidence; it never mutates an empirical runtime gate. Readiness documents are plans, not implemented retrieval/GSN/multi-agent systems.

The validator runs review/V4/reader/profile/frozen V3/reference/generalization tests; hashes original files before/after; verifies prior packages, frozen live outputs/seals and protected human-scoring safeguards; and confirms the old blank forms are unchanged. Commands, environment and counts are in validation/RESULTS.json. No packages were installed or environments activated; -S avoids unrelated startup hooks.

AUTHORIZED_VISUAL_EVIDENCE.json records exactly what was authorized/viewed. The three copied JPEGs are under /tmp/trustworthy-phase2b4-approved-contact-sheets in the authorized session; original sheets stay on Hestia. Do not infer authorization for more images, raw videos, HDF5 or full per-frame data. New transfers require separate scope/approval.

ARTIFACT_SHA256.json inventories compact files except itself; Git binds that manifest. Raw recordings/media remain outside Git. No experiment, RAG or multi-agent implementation, push or merge occurs in this phase.
