# Short independent review guide

Detector predictions are only in outputs/. Forms in human_review/ remain blank. Do not copy a detector prediction into a human label automatically. Prefer independent clip review before opening episode predictions.

| Review | Exact clips (both cameras) | Form |
|---|---|---|
| Initial support / settling examples, episodes 000 and 001 | clips/episode_000_agentview_image_000000-000030.mp4 and clips/episode_000_robot0_eye_in_hand_image_000000-000030.mp4; matching episode_001 files | human_review/initial_support_forms.json, entries for each object's frame 10; event_forms.json for setup observations |
| Episode 002 setup departure and later landing | clips/episode_002_agentview_image_000000-000030.mp4 and clips/episode_002_robot0_eye_in_hand_image_000000-000030.mp4 (frames 0–30; simulator endpoint t=0–1.50 s) | Initial-support form for cream_cheese_1 at frame 10; separate event form for setup onset and possible later landing |
| Episode 014 lift, release/descent and table recontact | clips/episode_014_agentview_image_000260-000300.mp4 and clips/episode_014_robot0_eye_in_hand_image_000260-000300.mp4 (frames 260–300; t=13–15 s) | Event form for cream_cheese_1; inspect frames 281–284 particularly. Requirements interpretation belongs in requirement_interpretation_forms.json, not the physical label |

1. **Initial-support labels:** direct table support, indirect support through a named entity, unsupported, or uncertain. Cite frame/contact/geometry evidence. A visual impression or contact count alone does not establish load bearing. Unknown initial support is insufficient information, never an automatic pass or verified non-applicability.
2. **Physical-event labels:** describe supported tipping/sliding, table departure, lift/carry candidate, post-lift drop, catch, landing, setup anomaly or uncertainty. Give first/last possible event frames and uncertainty. The corrected persistence detector may miss an apparent short drop; absence of a candidate is not a human non-event label.
3. **Requirement interpretation:** separately decide whether reviewed applicability, the proposed fall definition and the event evidence support a violation, no violation observed in stated coverage, insufficient information, or verified non-applicability. Keep this pending until reviewed. A post-lift drop is not automatically a direct table fall. Requirement approval itself remains a separate decision.

clip_manifest.json provides every exact HDF5 camera frame path, run ID, stage, host snapshot reference and simulator endpoint time. Display is rotated 180° to match the producer. Camera exposure timing is unverified; geometry/contact evidence is nominally t−2 ms, while images may have another cached observation phase. Clips are consecutive excerpts, not whole-run negatives. No human identity, approval or decision is entered.

The two changes to inspect first in CHANGE_REPORT.md are episode 014's persistence result and any newly strengthened direct-departure candidates. Review ambiguous contact history before interpreting those candidates. Held-out recordings remain reserved and are not included for event review here.
