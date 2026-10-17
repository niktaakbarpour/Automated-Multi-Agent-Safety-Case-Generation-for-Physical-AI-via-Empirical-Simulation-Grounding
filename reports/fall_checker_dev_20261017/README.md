# Fall checker development release — 20261017

**PROPOSED CONFIGURATION; UNAPPROVED REQUIREMENT; UNVALIDATED DETECTOR.** Implementation authorization does not approve a requirement, detector output, or event label. Pilots, audit v1/v2, recordings and human-review records are preserved.

This release reads only the locked 40-run development partition. The ten held-out runs are listed as not processed. No robot simulation, LLM generation, critic, physics stepping, or held-out event evaluation is performed.

Run with Python plus numpy and h5py (Pillow, imageio and imageio-ffmpeg are also needed to export clips):

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python src/run_development.py --root . --output new_outputs
PYTHONDONTWRITEBYTECODE=1 python src/export_clips.py .
```

Output directories must be fresh. `config.json` explicitly binds task/source paths, objects, native surfaces, geometry phase, interval, physical candidate parameters and scope. Missing required parameters fail. The pinned Hestia runtime and exact command/environment are recorded in runtime_provenance.json. No installation or dependency/model change is performed. Hestia access is needed to reprocess the full lossless recordings; weights, environments and robot recordings are excluded from this package. Included synthetic tests require only numpy/h5py and small fixtures. The geometry/contact extracts and object observations can be inspected without original recordings.

The package contains object-wise initial applicability candidates, physical event candidates with frame/time references, setup findings, uncertainty and sensitivity outputs. `requirement_verdict` stays not assessed/pending approval. A physical candidate is never automatically a requirement violation. No object is reported as passing, especially the initially airborne objects.

Read `DEVELOPMENT_SPEC.md`, `PARAMETERS.md`, `RESULTS.md`, `REVIEW_DECISIONS.md`, and `human_review/INSTRUCTIONS.md`. Clips are excerpts for independent review; they do not establish whole-run negatives. Native contact IDs must go through the copied corrected v2 API, never the lossy 155-name list.

`outputs/all_run_object_index.json` retains all five objects across all 50 run identities: 200 provisional development assessments and 50 explicitly unevaluated held-out object placeholders. Unknown initial support is marked insufficient information; direct-support candidates remain provisional.
