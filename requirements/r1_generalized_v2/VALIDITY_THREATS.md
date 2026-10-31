# Research validity and claim boundaries

The generalized claim quantifies over a configurable object/surface/domain set.
Increasing that set changes the safety claim and potential coverage burden; it is
not merely a parser change. Execution aggregation can expose uncertainty hidden by
object-level reporting. Empty or selected-after-outcome sets would bias evaluation.

## Construct validity

- Initial-support falling, arbitrary departure, surface containment, handling drops
  and robot causation are different constructs. Preserve scope or version the change.
- Support is inferred from geometry/contact/dynamics, not directly measured by every
  simulator. Contact caches, penetration stabilization, sleeping bodies and missing
  normals/forces can invalidate a seemingly stable support inference.
- Supported motion, moving surfaces and multi-parent load paths need a valid model.
  Exact world-pose invariance is neither a universal support definition nor a calibrated
  noise policy. Meshes, deformable/active objects and ambiguous COM/root conventions
  require separate capability validation.
- Handling exclusion retains old semantics but requires independently established
  carrying. Intention or temporal association with robot motion cannot establish it.
- Clock labels can agree while image exposure and cached contact states differ.
  A sampled negative does not establish absence of a short intersample fall.

## Internal and statistical validity

- Existing NV01–NV20 support patterns and outcomes are already known. Repeated V4
  design or threshold selection on them risks leakage/overfitting. Use them for
  transparent development regressions only, not newly claimed independent validation.
- Current references are AI-origin and include human-reported acceptance in historical
  artifacts, not a new independent human ground truth. AI3 had prior conversation
  exposure and narrower visual review than AI2. Agreement can reflect shared model
  assumptions, anchoring, common evidence gaps and selected abstention policies.
- No confirmed positive R1 reference exists. Zero alarms and four qualified negatives
  cannot establish violation-detection recall, a low false-alarm population rate or
  broad safety. Excluding NA/unknown/IC/abstentions changes denominators and must be
  reported. Execution-level false-positive denominators are not object-level ones.
- Multiple objects in one run are correlated. New object counts do not create
  independent executions or improve sample size automatically. Per-task/site and
  per-execution clustering should be addressed in a future statistical protocol.
- Synthetic fixtures validate code against chosen assumptions, not physical truth.
  New perturbation experiments need separate authorization and explicit provenance.

## External validity

LIBERO Long tasks00/01 share scene geometry; changed task roles are not cross-scene
transfer. OpenVLA checkpoint identity is experiment provenance, not universal contact
semantics. The 38 other-scene preflight rejections demonstrate binding restrictions,
not evaluated cross-scene correctness. Arbitrary counts and IDs in examples establish
configurability only. Another benchmark may lack contacts, collision geometry,
gravity/clock conventions or calibrated states. An adapter must abstain or return IC
where the evidence contract cannot be admitted; it must not hallucinate equivalence.

## Reproducibility and infrastructure

Missing raw HDF5 currently prevents fresh raw/export regeneration. Preserved packages
have checksummed measurement/video coverage but retain phase/force limits. Archive
receipts alone do not prove current payload readability. Keep evidence-source and
derived-code hashes and separate validity judgments. Hestia processing, disk1 staging,
Alliance archival, no source deletion and immutable old seals remain mandatory.

## Supported versus deferred claims

Supported by this phase: inspected hardcoding/contract restrictions, a coherent
proposed generalized semantics, schema/example structure and documentation QA.
Deferred: implementation correctness of V4, empirical positive detection, calibrated
dynamic support, portable geometry/clock inference, new benchmark performance and
end-to-end safety-case quality. Each requires later implementation and experiments;
none follows from specification acceptance.
