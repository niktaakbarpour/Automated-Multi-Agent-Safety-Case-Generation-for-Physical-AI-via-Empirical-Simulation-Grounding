# Publication boundary for the provisional R1 adjudication

Nikta authorized publication of reviewed safe components on a new feature branch and a draft pull request against main. This is **publication approval only**: all 90 proposed decisions remain pending human adjudicator approval. No real dataset-finalization command is executed.

The branch is `feat/r1-human-evaluation-adjudication`, based on main commit `4d30ace44277b64e52d3bf5a888cfc22b7958a00`. Both reviewers’ original submissions were already merged into that commit. Their bytes, identities, dates, answers and qualifications are not modified or newly substituted.

## Included source and documentation

- `tools/adjudicate.py`: matching, comparison, provisional proposals and approval-gated finalization.
- `tools/inspect_recordings.py`, `tools/inspect_geometry.py`: read-only extraction recipes; no recording payloads or private recording locations embedded.
- `tools/publish_proposal.py`: explicit, deterministic publication transformation and public consistency/safety verifier.
- `tests/`: matching, source integrity, approval gates, unresolved cases, export reproducibility and publication restrictions.
- `.gitignore`, `README.md`, `START_HERE.md`, `VISUAL_INSPECTION.md`, and this publication boundary.

## Included derived publication snapshot

`publication_20261026/` contains alignment_report.csv, disagreements.csv, evidence_review.csv, adjudication_decisions.csv, agreement_statistics.json, approval_template.csv, four provisional table CSVs, adjudication_report.md, README.md, dataset_manifest.json, redaction_map.json and publication_checksums.json.

The ten scientific CSV/statistics artifacts are copied byte-for-byte from the original private proposal. This preserves reported agreement counts, all 90 pending decisions, complete already-public reviewer source rows and all eleven uncertainty requests. The report gains an explicit public-access notice; no scientific recommendation is changed.

The public manifest replaces private absolute recording locations with episode-scoped logical references. It excludes the detailed private native-object inventory and extraction metadata. Original recording/XML hashes, source submission hashes and original private proposal/manifest hashes remain. `redaction_map.json` documents each change without repeating private paths. Publication checksums apply to this separate version; the private proposal is not overwritten or silently relabeled.

## Deliberately excluded

- `evidence_20261026/`: raw recorded_evidence.json, disputed_geometry.csv and twelve PNG contact sheets.
- `proposed_20261026/`: unchanged private proposal, including its manifest containing private source locations.
- Temporary extracts, test logs, caches and any finalized reference directories.
- New full videos, HDF5 trajectories, model files, credentials, environment secrets or unrelated changes.

Ignored paths prevent accidental staging of local artifacts. Previously published media remain untouched on the base branch; this PR adds no binary media or new original human submissions.

## Reproducibility and evidence-access limits

The public verifier checks checksums, source preservation, lossless alignment representation, pending approval bindings, run/object/event references and unchanged statistics. These checks **do not** independently validate excluded scientific evidence. Their relative paths in CSV records are provenance identifiers, not a claim of public availability. Private-evidence integration tests run with authorized local evidence and explicitly skip when it is absent; portable comparison/publication tests still run.

The public snapshot intentionally fails the original private finalizer’s manifest-status requirement. Authoritative freezing requires the unchanged private proposal, restored authorized evidence and explicit attributable human decisions. Human consensus is not independent inter-rater reliability. Continuous safety, exact subframe timing, causal responsibility, detector accuracy and real-world safety are not established by this package.
