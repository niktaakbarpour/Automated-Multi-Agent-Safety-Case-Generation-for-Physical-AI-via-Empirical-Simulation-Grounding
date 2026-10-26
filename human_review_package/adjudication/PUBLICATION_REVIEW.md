# Publication boundary for approved R1 reference

## Approval and authorized update — 2026-10-26

Nikta Akbarpour explicitly approved the full current AI-assisted package (90 alignment units), including the episode 014 post-lift exclusion and retained uncertainty. Her approval is of the package, not independent reannotation or manual inspection of each original event. The approved reference is `approved_reference/r1-reference-be76abc531f5c716efca/`. Its approval ledger, metadata and finalized label CSVs are authorized for publication. Ten requests remain partially resolved; original independent-review statistics and original submissions are unchanged.

Additional reviewed publication-safe files include `ai_tools/`, `ai_tests/`, the immutable safe AI proposal `ai_assisted_20261026/`, the approved reference companion, evaluation handoff and validation documentation. Historical proposal files retain their pre-approval state. Actual approval metadata binds the exact approved proposal checksums; it does not retrospectively alter an earlier package.

Raw `evidence_20261026/` and `evidence_complete_20261026/`, all contact sheets, the local HTML review interface, the private finalizer bridge, private core manifests/exports, local staging/failed-candidate artifacts, and private original proposal remain excluded. No new original submissions, raw recordings, HDF5, checkpoints, secrets or private absolute paths are added. The public companion copies all four core finalized label CSVs byte-for-byte, replaces the private manifest with an explicit allowlisted public manifest, and preserves source/evidence hashes and logical references without raw evidence payloads. Its references identify excluded evidence, not public availability.

The original publication review below describes the earlier provisional snapshot and is retained as history. Its statements that all decisions are pending apply only to that historical stage. The new explicit adjudication approval and current final reference above are authoritative for current status. The PR remains a draft for review; no merge is authorized.

---

## Historical provisional publication boundary

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
