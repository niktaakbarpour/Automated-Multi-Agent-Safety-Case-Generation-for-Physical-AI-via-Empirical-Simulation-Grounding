# Requirement-generation v2 — prepared for researcher review, not launched

The original `data/requirement_pilots/20261016T154747Z` is preserved byte-for-byte on Hestia. The source/runtime reconciliation is recorded separately; no historical Git commit is retroactively invented. Future pilot metadata records the Git commit, dirty status, and source-file hashes.

## Proposed objective

“Prevent unintended falls of non-target objects from their supporting table during manipulation.”

This is a proposed researcher-defined objective pending review, not a built-in LIBERO rule, scene fact, approved requirement, or observed failure. It scopes this comparison only; other project objectives remain open. The v2 preparation helper explicitly refuses other task IDs rather than applying this pilot's facts to them.

## Review artifacts on Hestia

All paths are relative to `/local/home/niktakbr/trustworthy_project`:

- Exact revised task input: `data/requirement_inputs/v2/development.json`.
- Complete provenance: `data/requirement_inputs/v2/provenance.json`.
- Exact prompt: `prompts/requirements-v2.txt`.
- Output schema: `schemas/candidate_requirements.v2.schema.json`.
- Proposed objective: `config/study_objective_v2.proposed.json`.
- Geometry and asset inspection: `evidence/geometry_v2/resolved_geometry.json`.
- Separate suggested review: `reports/requirement_v2_review/suggested_review_proposal-e0af7cf5ea13e7fa42f9.json`.
- Full review document, with exact input/prompt/config embedded: `reports/requirement_v2_review/REVIEW.md`.
- Tests and offline checks: `reports/requirement_v2_review/tests-reviewed-final.log` and `offline_preflight.json`.
- Runtime discussion: `reports/requirement_v2_review/runtime_bottlenecks.md`.

The suggestion recommends `needs_revision`: the end-state check misses execution-wide coverage; “near” is undefined; root height is not support height; robot-contact causation is unestablished; basket stability is an unnecessary assumption. It does not edit the original proposal or its pending human review, and assigns no reviewer or approval.

## Geometry and measurement limits

`facts.xml_info()` now delegates MJCF transforms/defaults/mesh normalization to MuJoCo, retains body hierarchy and worldbody geometry, and distinguishes effective collision masks/explicit pairs from render groups. If compilation or assets cannot be resolved, raw geometry is retained and transforms are explicitly unresolved. No approximate transform is silently substituted.

Inspection uses the existing MuJoCo 3.8.1 environment, not the incompatible 3.3.1 parser. It performs compilation and forward kinematics only, without stepping simulation or running a robot policy. All transforms refer to the XML model's reference configuration, not recorded per-frame poses. The actual named table has its geoms in a child body. Semantic support bindings, physical measurement calibration, and temporal completeness remain unverified; no table height is inferred from object centers.

The prompt inventory remains qualified as field presence in three sampled frames (first/middle/final) of one explicitly identified reference run. This does not verify units, coordinate frames, object reference points, or full-run availability. Full provenance is retained separately. Approved requirements/checkers are not proposal prerequisites. Qualitative candidates and abstentions are allowed; neither output selection nor a minimum candidate count is imposed. Outcomes and observed failures remain excluded.

## Runtime and comparison controls

`config/requirement_generation.v2.json` pins the same Qwen model/revision, BF16/no quantization, thinking/medium reasoning, sampling values, seeds 1000/1001/1002, and 6144-token output budget as the completed pilot. It uses Transformers 5.17.0, the existing data-disk environment/model/cache paths, and an explicit configurable 14400-second request timeout. Transport errors, request-preflight failures, and output-validation failures are recorded separately.

Version 2 uses `reports/requirement_pilot_v2_queue`, leaving the original completed queue status intact. Queue statuses record process start identity; the status inspector labels unverifiable running statuses stale. The queue defaults to a printed plan and starts nothing unless `--launch-reviewed-pilot` is explicitly supplied.

## Tests (no generation server calls)

```bash
cd /local/home/niktakbr/trustworthy_project
PYTHONPATH=src /local/home/niktakbr/rdt-1b-libero/.venv/bin/python -m unittest discover -s tests -v
```

Focused tests cover nested/worldbody geometry, transforms, mesh scale/alignment, inherited collision masks, explicit contact pairs, unresolved geometry, measurement coverage/reference identity, qualitative candidates/abstentions, custom prompt/input/schema paths, timeout forwarding, separate error records, Git commit/dirty metadata, preserved generation controls, and stale queue detection. Serving calls are mocked; real tokenization uses only the cached pinned tokenizer.

## Future command — only after review

```bash
cd /local/home/niktakbr/trustworthy_project
/disk/1/data/niktakbr/trustworthy-runtime/venv-py312/bin/python \
  src/queue_requirement_pilot.py \
  --config config/requirement_generation.v2.json \
  --output data/requirement_pilots/v2-reviewed-non-target-falls \
  --launch-reviewed-pilot
```

This command has NOT been executed. Choose a fresh output name if it already exists. Dropping `--launch-reviewed-pilot` prints the plan only. Human review of the objective and exact input is the next step; requirements are not approved, and safety cases, checkers, critics, and robot reruns are outside this work.
