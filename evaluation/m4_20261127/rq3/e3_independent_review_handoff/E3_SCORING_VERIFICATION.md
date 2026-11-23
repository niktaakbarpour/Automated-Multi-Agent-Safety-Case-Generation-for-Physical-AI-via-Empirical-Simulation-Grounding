# E3 scoring and frozen-response verification

**Purpose:** verify the existing deterministic RQ3 scoring path and immutable saved 108-response experiment for handoff. This is not a new evaluation or independent-label result. No inference was run. Frozen outputs and source artifacts were not modified.

## Frozen artifacts and structural checks

Inputs/code:

- `evaluation/m4_20261127/rq3/MATCHED_RUN_MANIFEST.csv`
- `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl`
- `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl.meta.jsonl`
- `evaluation/m4_20261127/rq3/experiment/score.py`
- `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_PER_CASE_RESULTS.csv`
- `.../RQ3_SUMMARY.csv` and `.../RQ3_TABLES.md`

Standard-library structural check results:

- Matched manifest: 108 unique run IDs.
- Raw JSONL: 117 attempt records, 108 unique run IDs and 108 server replies; 9 attempts have no reply. No response body or per-case prediction is repeated in this report.
- Saved per-case CSV: 108 request rows, covering T/R/C and repeats 1–3; saved summary: 92 rows.
- Metadata sidecar: 5 records.
- Raw response records and saved result files have distinct SHA-256 values recorded in the accompanying verification log/working audit; no source file was rewritten.
- `make_tables.py` was run on a temporary copy of the saved score directory. The regenerated table compared byte-for-byte equal with the frozen `RQ3_TABLES.md` (`cmp` exit 0). The temporary file was removed.

## Deterministic scorer semantics audited

Source: `evaluation/m4_20261127/rq3/experiment/score.py`; table builder: `experiment/make_tables.py`; tests: `evaluation/m4_20261127/rq3/tests/test_experiment.py` and `test_mutations.py`.

- **Model-only:** findings are screened and counted after output validity and finding gates. A target hit must match the labeled GSN node and object (or omit object only when the node is unique); detection also requires a mutation-acceptable category.
- **Rule-only:** deterministic rule findings are evaluated once per case, separate from model conditions.
- **Combined:** rule-only detection OR model detection, counted once (logical union); clean-control false positive is similarly the union of any accepted model finding and any rule finding. This is not an independent run.
- **Accepted/rejected findings:** the scorer tracks raw, accepted, and rejected findings and records rejection reasons including target/object/node/category and citation issues. Invalid/no-reply/missing outputs are distinct from valid outputs.
- **Denominators and abstention:** detection and clean-control false-positive rates use valid outputs. A valid empty findings list is an abstention, not a negative/correct finding by default. Missing and invalid outputs are not treated as negatives. Clean-control outputs with at least one accepted finding count as false positives.
- **Repeats:** three repeated requests per case and condition. Summaries carry case/group denominators and repeat-level mean/SD. Repeat variation is not independent source-group uncertainty: the data are 12 cases in two parent groups, with zero independent groups.
- **Citations:** only findings whose citation checks are reached contribute to citation-scope counts; findings rejected before citation checking are excluded from that denominator. Citation screening uses the full case, so a passing citation can refer to evidence that was not present in the model’s condition-specific prompt. This limits claims about evidence use.
- **Condition C:** availability conveys checker admission status only. No independently verified physical checker judgment was available; C must not be described as a checker-evidence condition.
- **References:** the current scorer reads developer reference labels and case mutation files. Those inputs must not be exposed to the reviewer before the review submission has been frozen. Current outputs are development results, not human-validated metrics.

## Reproducibility tests and environment blocker

Command attempted:

```text
env PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq3/tests -p 'test_*.py' -v
```

The environment exposes Python 3.9.6 only; Python 3.11/3.12 was not found. The run executed 9 test entries and ended with 5 errors:

- Three test paths and the scorer dry-run fail while importing `jsonschema` (`ModuleNotFoundError`); that dependency is absent.
- `test_mutations` cannot import a project module that uses Python 3.10+ `str | None` annotation syntax under Python 3.9 (`TypeError`).
- One class setup scorer error shares the missing `jsonschema` cause.
- The other batch shape/view/repeat/settings checks that did not require the unavailable paths passed. The output is not an all-green test result.

No assertion failure indicating changed science was observed; the suite is incomplete due to environment/import errors. No dependency was installed and no frozen outputs were edited. The full scorer was not rerun successfully; the byte-identical table rebuild is a downstream consistency check, not a substitute for rescoring.

## Integrity digests

SHA-256, in repository-relative path order:

| Artifact | SHA-256 |
|---|---|
| `experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl` | `42f1aef874af00435cb892a5b78de7879629a91229e9b2fe30125903411e4fe7` |
| `experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl.meta.jsonl` | `3a9b21b3e80282fc0f1ebcffa67188394a891bbad633b472569d8fc92d3f29f8` |
| `experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_PER_CASE_RESULTS.csv` | `6df445fb11c4d4f669527b20e9f93b4884c38dc69429de304f459b73c491099c` |
| `experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_SUMMARY.csv` | `2767768748b51caf88c8b945e417b7e85b8e4a75c926efbfcfe7dcd639097f6d` |
| `experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_TABLES.md` | `8ea0986ad3c563ed8205276de8b4d92bbc9411179acd23c17f3255dc8d29ae4a` |
| `experiment/score.py` | `d385bdae0a5528ec6500b943ff3af35e4c16e3244ab814b507e17c1cd10aadcd` |

These digests identify the bytes observed during this audit; they are not an external signature or independent provenance attestation.
