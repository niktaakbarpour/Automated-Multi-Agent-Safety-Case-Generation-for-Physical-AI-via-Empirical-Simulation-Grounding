# Temporal alignment and coverage

Recorder: reports/fall_review_20261016/source_evidence/run_oft.py settling/control loop and recording_base.py snapshot lines77–95. Exact hashes: SOURCE_BINDINGS.json. Historical reconstruction: reports/fall_review_v2_20261016/measurement_findings_v2.md section5. Current checks: MEASUREMENT_SUMMARY.json.

The producer sets the benchmark initial state, saves frame0, executes ten settling steps and saves each endpoint. Frame10 is the pre-first-policy boundary. Policy step i ends in frame i+11. Terminal is N+10 for N policy actions. Snapshot writes supplied raw observations, then copies state/caches/contacts without advancing physics. Host timestamps describe recording work, not camera exposure.

Exports have consecutive IDs, matching control-step offsets and complete expected saved-frame counts. Intervals are approximately0.05s with floating point variation; exact extrema are in MEASUREMENT_SUMMARY.json. This establishes saved-index continuity only. Snapshot fields can have different phases.

The historical model uses Euler integration, physics step0.002s. Earlier raw checks supported body/geom/contact caches at the last pre-integration configuration, nominal endpoint minus one substep. Endpoint qpos/qvel are distinct. Raw object observables fit an additional-substep cache hypothesis. Historical robosuite observable/camera dependencies lacked producer hashes. These inherited findings are neither a universal correction nor a calibrated alignment window.

Restore native arrays and metadata before reproducing timing residuals. Keep direct stored fields intact; static endpoint reconstruction must be separately derived, without recomputing contacts or advancing dynamics. It supplies no extra observed snapshot. qacc/cfrc_ext cannot repair phase or supply missing per-contact impulses.

Camera exposure remains unknown. Same observation dict, frame count, FPS and host timestamps do not prove camera/state simultaneity. No pixels were newly inspected. Original HDF5 lossless images or selectively restored MP4s can corroborate qualitative review, subject to display rotation and cache uncertainty.

Keep requested, available, inspected, invalid and qualified-negative domains separate. Complete saved exports do not qualify negative cells or transitions. Physics-substep/continuous coverage is absent. Boundary-straddling or gap-spanning event brackets remain unresolved; retain setup history and terminal censoring. Dynamic, handling and replacement-suffix negative composition remain disabled.
