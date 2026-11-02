# One new measurement-only contract

Profile object-task02:1.0.0; reader 1.2.0; recorder/data 4.0; requirement 2.0.0; configuration 2.0.1; evidence 1.0.0; database extension 1.1.0. Old profiles and evidence IDs are preserved. This is not an empirical R1 checker profile.

plan.py records task/case selection, members, expected hashes, receipts and exclusions. receive.py writes only fresh allowlisted paths. pilot.py verifies eleven pilot/task files, compiles identities and scans all 127 pilot frames. An early prototype rejected the old table fixture name; the final profile instead uses the new task's declared floor and actual compiled IDs. Remaining 48 cases were restored only after the pilot passed. activate.py verifies all 443 source hashes before registration; every read still validates full snapshots.

native.py compiles verified saved MJCF with existing MuJoCo 3.8.1 for IDs, ownership/masks and dimensions. It crosschecks complete recorded body/name projections and joint addresses, retaining anonymous IDs if present. Cached rigid local transforms come from recorded frame 0. No MjData, mj_step, mj_forward, rollout, policy or renderer runs. Compiler version is pinned; this is not a claim of replaying the original dynamics. Machine-roundoff guards are not physical tolerances. recompile.py reproduces the native profile independently.

Objects are the explicit source inventory, not an R1 protected-object configuration. Static fixture references do not establish load-bearing support. Plane/non-BOX physical bounds and empirical admission remain unsupported/blocked. Camera refs identify source arrays, not object detections or known exposure instants. Native robot-state references include configuration, velocity and control vectors; the full reader also exposes recorded gripper observables with their source convention/phase limitations. Contact normals/forces are not invented.

build.py copies the immutable Phase 5C release and appends 49 executions. Optional closed independent append validates all new dependencies/conflicts within the new execution, rejects execution mismatch and preserves source integrity. New records use corpus_expansion, not development. Query stratum is optional; its absence preserves prior query IDs. No evaluation-only stratum is enabled.

On Hestia, use the approved h5py/numpy PYTHONPATH, PYTHONDONTWRITEBYTECODE=1 and TMPDIR=/disk/1/data/niktakbr. Call populate on a NEW owned database path, never a prior release:

```
python3 -S -c "from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.build import populate; print(populate('/disk/1/data/niktakbr/NEW.sqlite'))"
```

Repeat on that working copy to resume. validate.main('/disk/1/data/niktakbr/NEW-VALIDATION-DIRECTORY') performs independent builds, resume, source/coverage checks, retrieval and regressions. Reports refuse overwrites. PROFILE/SOURCE_PLAN/NATIVE_PROFILE are pinned inputs; do not regenerate them inside a published build. A new task needs a new reviewed registration.

For independent compilation only, append existing /disk/0/home/niktakbr/smolVLA_libero/.venv/lib/python3.12/site-packages after the h5py environment in PYTHONPATH. recompile.py uses verified existing assets; no installation/API is needed. Its report path must be fresh. Sources and large datasets remain on Hestia; no original imagery is transferred into Codex.
