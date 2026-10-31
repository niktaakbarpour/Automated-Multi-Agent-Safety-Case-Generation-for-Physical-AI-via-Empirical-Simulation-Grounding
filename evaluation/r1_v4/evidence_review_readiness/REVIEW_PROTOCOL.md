# Phase 2B.4 evidence review protocol

Baseline f15d3a9da13e535db49b19f023f762824b4ea26c; branch feat/r1-v4-evidence-review-readiness. Review all eleven Phase 2B.3 entries without admitting empirical V4 outcomes. Originals, full numerical datasets and historical review forms remain unchanged on Hestia.

## Authorization and actual inspection

The user explicitly authorized only these derived JPEGs to this Codex session:

| Hestia sheet under /disk/1/data/niktakbr/r1-v4-phase2b3-working/reference_sheets/ | Bytes | SHA256 |
|---|---:|---|
| episode_000.jpg | 39207 | c2f08248d428f264db8c8c9e6c6e5fe070d8ade454d320926d77e3e2f4308ddc |
| episode_002.jpg | 38183 | ea0a058a1dfc75e4e8eecefe7e7976461514b88436a1213c0d6ba58f61cf4210 |
| episode_014.jpg | 43542 | 8e60c7bf21f8dab834d0bb95c5968b98bfc673775bb2f631751978f28caeef19 |

Total 120932 bytes. The source digests/sizes were checked on Hestia against the prior manifest. SCP transferred these three literal paths to /tmp/trustworthy-phase2b4-approved-contact-sheets/; view_image displayed those JPEGs in the current Codex visual context. No additional images, original HDF5, raw video or full per-frame measurement dataset was transferred. No image payload is committed to Git. Local payload hashes were not separately recomputed; source hashes and the authenticated transfer are recorded without claiming a local hash audit.

The approved sheets contain 24 panels from two cameras: agentview_image and robot0_eye_in_hand_image. Episode 000 frames 0/10/14/16, episode 002 frames 0/7/10/12, episode 014 frames260/276/282/284 were visually inspected. The prior display transform is 180-degree rotation, resizing to 192 pixels and derived JPEG encoding. AUTHORIZED_VISUAL_EVIDENCE.json preserves source execution/HDF5/raw-byte/derived-sheet hashes, frame indices, camera identities and exact snapshot endpoint times and host UTC/wall/monotonic timestamps. Actual exposure time remains null. Caption time is not camera synchronization.

Numerical review ran on Hestia. review_sources.py verified 38 original hashes, all prior package manifests and the complete diagnostic-table digest, then read each cited candidate interval plus one leading context frame where available. Contact-owner timelines and BOX unions were cross-checked with original datasets. Root/finger-collision-center co-motion is a descriptive indicator only, not a load-bearing witness. Ten sourced cases comprise 317 object-snapshot inspections including overlap. C04 has no source and remains unfilled.

## Review and dependence

AI_REFERENCE_REVIEWS.csv contains authored AI interpretations, not measurement facts or human labels. EVIDENCE_LEDGER.csv separates source identity, raw/derived numerical review, qualitative visual observations and missing physical contracts. It records internal dependencies and shared execution groups. More than one view or overlapping case does not create independent evidence.

The same AI conversation has prior development/audit/V3-context exposure. This is one dependent, provisional review, not a fresh-context replication or human confirmation. Evidence sufficiency is qualitative and claim-specific; no probability/confidence threshold is invented. All empirical predicates remain unadmitted.

For each entry record source/task identity, initial-support context, geometry, contacts, motion, robot/gripper context, visual coverage, counterinterpretations and missing evidence. Do not infer support from contact, falling from root/image movement, or absence from occlusion. Do not assume uncertain holding either present or absent to force R1 scope. Do not populate human forms.

Reproduce source checks and report materialization on Hestia with the existing package path documented in REPRODUCIBILITY.md. Re-running scripts reproduces this recorded AI review; Python does not perform a new visual review or obtain human evidence. No experiments, RAG or multi-agent implementation occur in this phase.
