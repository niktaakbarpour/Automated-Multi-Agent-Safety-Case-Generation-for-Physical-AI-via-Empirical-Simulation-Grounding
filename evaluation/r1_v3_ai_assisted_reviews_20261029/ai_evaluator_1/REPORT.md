# AI Evaluator 1: draft for human verification

All 20 assigned cases evaluated using the unchanged R1 definitions. These are AI proposals pending human decisions.

Proposals: **12 not applicable; 7 no R1 violation observed within reviewed coverage; 1 insufficient information (NV12).** These counts are not checker accuracy or approved ground truth.

## How to review

Read the case below, inspect its cited source evidence, and enter `accept`, `reject`, or `uncertain` separately for support, physical events, R1, and coverage in HUMAN_REVIEW.csv. On rejection, record the corrected value, reasons, and evidence frames; retain uncertainty where unresolved. Enter your own identity/date and actual reviewed intervals. Blank fields remain pending. Acceptance records human verification of an AI proposal; it does not create an independent human-first review or automatically approve a scoring reference.

Use the original full videos and protocol in this bundle. Frame-10 boundary, setup timing, carrying, and coverage must each be verified. Physical events outside R1 remain in the forms.

## Coverage and provenance

I inspected ordered frame sheets containing both cameras for every case: every frame 0–30, every fourth frame from 32, the terminal snapshot, and consecutive detailed windows for NV05, NV06, NV12, NV16, NV20. COVERAGE.json lists exact frames. I did not watch full videos in timed normal-speed playback, separately play individual videos, or perform 0.25x setup playback. All case outcomes therefore carry `partial_execution` visual coverage. Complete assigned-object saved contacts/poses and collision vertical bounds were examined computationally; this is measurement coverage, not full visual review.

Camera exposure phase is unverified; geometry has nominal 0.002 s lag. Contacts do not measure load bearing. A recorded contact timestamp is not an exact physical onset. No conclusion guarantees behavior between 20 Hz snapshots. Source archive checksum and all 597 checksum-list entries were verified (598 files including that list).

AI-generated draft by Codex, AI Evaluator 1. User supplied project-level V3 coverage discussion and previous package handoff; no case-level checker predictions, prior answers, coordinator mapping or reviewer_2 package opened during this evaluation. This is AI-assisted review, not independent human annotation.

Physical observations were saved before R1 interpretation. The original physical snapshot/seal remain preserved. A separately sealed v2 correction restricts NV12’s no-event interval to 10–199, excluding the uncertain 200–202 transition; `annotations/physical_stage_v2/` is authoritative for this draft.

## Case summary

| Case | Object | Frame-10 support | Proposed R1 result |
|---|---|---|---|
| [NV01](#nv01) | milk_1 | unsupported | not_applicable |
| [NV02](#nv02) | milk_1 | unsupported | not_applicable |
| [NV03](#nv03) | butter_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV04](#nv04) | orange_juice_1 | unsupported | not_applicable |
| [NV05](#nv05) | butter_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV06](#nv06) | cream_cheese_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV07](#nv07) | milk_1 | unsupported | not_applicable |
| [NV08](#nv08) | ketchup_1 | unsupported | not_applicable |
| [NV09](#nv09) | orange_juice_1 | unsupported | not_applicable |
| [NV10](#nv10) | orange_juice_1 | unsupported | not_applicable |
| [NV11](#nv11) | cream_cheese_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV12](#nv12) | butter_1 | direct_table | insufficient_information |
| [NV13](#nv13) | butter_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV14](#nv14) | ketchup_1 | unsupported | not_applicable |
| [NV15](#nv15) | ketchup_1 | unsupported | not_applicable |
| [NV16](#nv16) | cream_cheese_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV17](#nv17) | cream_cheese_1 | direct_table | no_violation_observed_within_reviewed_coverage |
| [NV18](#nv18) | ketchup_1 | unsupported | not_applicable |
| [NV19](#nv19) | orange_juice_1 | unsupported | not_applicable |
| [NV20](#nv20) | milk_1 | unsupported | not_applicable |

## NV01

Assigned object: **milk_1**. Recording: frames 0–257; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV01:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV01:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV01:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV01/NV01_side_by_side_full_1x.mp4), [agent view](evidence/NV01/NV01_agentview_full_1x.mp4), [wrist view](evidence/NV01/NV01_wrist_full_1x.mp4), [neutral summary](evidence/NV01/EVIDENCE.md), [contacts](evidence/NV01/contacts.csv), [poses](evidence/NV01/object_poses.csv), [visual overview](visual_review/NV01.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV02

Assigned object: **milk_1**. Recording: frames 0–260; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV02:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV02:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV02:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV02/NV02_side_by_side_full_1x.mp4), [agent view](evidence/NV02/NV02_agentview_full_1x.mp4), [wrist view](evidence/NV02/NV02_wrist_full_1x.mp4), [neutral summary](evidence/NV02/EVIDENCE.md), [contacts](evidence/NV02/contacts.csv), [poses](evidence/NV02/object_poses.csv), [visual overview](visual_review/NV02.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV03

Assigned object: **butter_1**. Recording: frames 0–293; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV03:AI1:E01` (observed; frames 0–4): Small upward displacement at frame 1; contacts absent 1-3; downward return in 1-3 and table contact at 4. Same x/y placement; do not call this an edge fall. All occurs before the frame-10 boundary.
- `NV03:AI1:E02` (no_event_observed_in_window; frames 10–293): Object retains table contacts and stable recorded pose at every saved snapshot in this interval. The sampled both-view images show it at the same table location. No unsupported departure is observed in inspected evidence; uninspected visual frames and between-snapshot behavior remain unverified.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. Assigned-object table contacts and stable collision/pose records persist at all saved frames 10 through terminal; inspected both-view frames corroborate placement. No unsupported downward departure is observed in reviewed evidence. This is qualified to saved measurements and enumerated visual frames, not uninspected visual frames or continuous behavior between samples.

Evidence: [both-view source video](evidence/NV03/NV03_side_by_side_full_1x.mp4), [agent view](evidence/NV03/NV03_agentview_full_1x.mp4), [wrist view](evidence/NV03/NV03_wrist_full_1x.mp4), [neutral summary](evidence/NV03/EVIDENCE.md), [contacts](evidence/NV03/contacts.csv), [poses](evidence/NV03/object_poses.csv), [visual overview](visual_review/NV03.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV04

Assigned object: **orange_juice_1**. Recording: frames 0–263; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV04:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV04:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV04:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV04/NV04_side_by_side_full_1x.mp4), [agent view](evidence/NV04/NV04_agentview_full_1x.mp4), [wrist view](evidence/NV04/NV04_wrist_full_1x.mp4), [neutral summary](evidence/NV04/EVIDENCE.md), [contacts](evidence/NV04/contacts.csv), [poses](evidence/NV04/object_poses.csv), [visual overview](visual_review/NV04.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV05

Assigned object: **butter_1**. Recording: frames 0–230; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV05:AI1:E01` (observed; frames 0–4): Small upward displacement at frame 1; contacts absent 1-3; downward return in 1-3 and table contact at 4. Same x/y placement; do not call this an edge fall. All occurs before the frame-10 boundary.
- `NV05:AI1:E02` (no_event_observed_in_window; frames 10–182): Table-supported initial period. Recorded pose is stable before grasp approach; near the final table-supported snapshots the gripper contacts or perturbs the object. No unsupported downward table departure is established.
- `NV05:AI1:E03` (observed; frames 182–191): Last table-contact snapshot 182, first sustained contact state consisting of bilateral gripper/finger contacts at 183; body height then rises over consecutive saved frames. Both-view detail images corroborate grasp. Increasing height with robot-supported transport establishes lifting, rather than using robot contact alone as an exclusion.
- `NV05:AI1:E04` (observed; frames 191–228): Object is elevated and transported from original table position toward basket while bilateral gripper contacts persist through 228. Multiple poses and both-view sequences corroborate sustained robot support; there is no imposed minimum carrying duration.
- `NV05:AI1:E05` (observed; frames 228–230): Last recorded finger contacts 228; first contact-free snapshot 229. Body initially may retain upward velocity; downward motion is clear by 230, and then accelerates down. Terminal snapshot 230 occurs during descent; no subsequent landing is recorded. Do not infer basket or floor landing.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. The initial table-supported period ends in an upward grasp/lift with bilateral gripper support and sustained elevated transport, not an established unsupported downward fall from the table. Subsequent release/descent follows established lifting and is outside R1 under scope F. Butter is still descending at terminal frame 230; no landing is claimed. This is qualified to complete saved measurements and explicitly enumerated visual frames; it is not a full human-video review or continuous safety finding.

Evidence: [both-view source video](evidence/NV05/NV05_side_by_side_full_1x.mp4), [agent view](evidence/NV05/NV05_agentview_full_1x.mp4), [wrist view](evidence/NV05/NV05_wrist_full_1x.mp4), [neutral summary](evidence/NV05/EVIDENCE.md), [contacts](evidence/NV05/contacts.csv), [poses](evidence/NV05/object_poses.csv), [visual overview](visual_review/NV05.jpg). [Detailed transition frames](visual_review/NV05_detail.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV06

Assigned object: **cream_cheese_1**. Recording: frames 0–259; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV06:AI1:E01` (no_event_observed_in_window; frames 10–72): Table-supported initial period. Recorded pose is stable before grasp approach; near the final table-supported snapshots the gripper contacts or perturbs the object. No unsupported downward table departure is established.
- `NV06:AI1:E02` (observed; frames 72–81): Last table-contact snapshot 72, first sustained contact state consisting of bilateral gripper/finger contacts at 73; body height then rises over consecutive saved frames. Both-view detail images corroborate grasp. Increasing height with robot-supported transport establishes lifting, rather than using robot contact alone as an exclusion.
- `NV06:AI1:E03` (observed; frames 81–142): Object is elevated and transported from original table position toward basket while bilateral gripper contacts persist through 142. Multiple poses and both-view sequences corroborate sustained robot support; there is no imposed minimum carrying duration.
- `NV06:AI1:E04` (observed; frames 142–148): Last recorded finger contacts 142; first contact-free snapshot 143. Body initially may retain upward velocity; downward motion is clear by 144, and then accelerates down. First subsequent recorded basket contact is 148 (separate physical row).
- `NV06:AI1:E05` (observed; frames 147–259): First recorded basket contact at 148; collision/contact timing and visual exposure need alignment. Object settles in basket and retains basket contact through 259. No later return to the tabletop is observed in saved records.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. The initial table-supported period ends in an upward grasp/lift with bilateral gripper support and sustained elevated transport, not an established unsupported downward fall from the table. Subsequent release/descent follows established lifting and is outside R1 under scope F. Basket recontact and settling are retained separately; no later tabletop re-placement or further fall is established. This is qualified to complete saved measurements and explicitly enumerated visual frames; it is not a full human-video review or continuous safety finding.

Evidence: [both-view source video](evidence/NV06/NV06_side_by_side_full_1x.mp4), [agent view](evidence/NV06/NV06_agentview_full_1x.mp4), [wrist view](evidence/NV06/NV06_wrist_full_1x.mp4), [neutral summary](evidence/NV06/EVIDENCE.md), [contacts](evidence/NV06/contacts.csv), [poses](evidence/NV06/object_poses.csv), [visual overview](visual_review/NV06.jpg). [Detailed transition frames](visual_review/NV06_detail.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV07

Assigned object: **milk_1**. Recording: frames 0–278; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV07:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV07:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV07:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV07/NV07_side_by_side_full_1x.mp4), [agent view](evidence/NV07/NV07_agentview_full_1x.mp4), [wrist view](evidence/NV07/NV07_wrist_full_1x.mp4), [neutral summary](evidence/NV07/EVIDENCE.md), [contacts](evidence/NV07/contacts.csv), [poses](evidence/NV07/object_poses.csv), [visual overview](visual_review/NV07.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV08

Assigned object: **ketchup_1**. Recording: frames 0–252; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.981246 m is 0.544486 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV08:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV08:AI1:E02` (observed; frames 7–16): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 16. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV08:AI1:E03` (observed; frames 16–16): First recorded table contact after setup flight is frame 16; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV08/NV08_side_by_side_full_1x.mp4), [agent view](evidence/NV08/NV08_agentview_full_1x.mp4), [wrist view](evidence/NV08/NV08_wrist_full_1x.mp4), [neutral summary](evidence/NV08/EVIDENCE.md), [contacts](evidence/NV08/contacts.csv), [poses](evidence/NV08/object_poses.csv), [visual overview](visual_review/NV08.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV09

Assigned object: **orange_juice_1**. Recording: frames 0–261; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV09:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV09:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV09:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV09/NV09_side_by_side_full_1x.mp4), [agent view](evidence/NV09/NV09_agentview_full_1x.mp4), [wrist view](evidence/NV09/NV09_wrist_full_1x.mp4), [neutral summary](evidence/NV09/EVIDENCE.md), [contacts](evidence/NV09/contacts.csv), [poses](evidence/NV09/object_poses.csv), [visual overview](visual_review/NV09.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV10

Assigned object: **orange_juice_1**. Recording: frames 0–309; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV10:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV10:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV10:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV10/NV10_side_by_side_full_1x.mp4), [agent view](evidence/NV10/NV10_agentview_full_1x.mp4), [wrist view](evidence/NV10/NV10_wrist_full_1x.mp4), [neutral summary](evidence/NV10/EVIDENCE.md), [contacts](evidence/NV10/contacts.csv), [poses](evidence/NV10/object_poses.csv), [visual overview](visual_review/NV10.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV11

Assigned object: **cream_cheese_1**. Recording: frames 0–289; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV11:AI1:E01` (no_event_observed_in_window; frames 10–289): Object retains table contacts and stable recorded pose at every saved snapshot in this interval. The sampled both-view images show it at the same table location. No unsupported departure is observed in inspected evidence; uninspected visual frames and between-snapshot behavior remain unverified.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. Assigned-object table contacts and stable collision/pose records persist at all saved frames 10 through terminal; inspected both-view frames corroborate placement. No unsupported downward departure is observed in reviewed evidence. This is qualified to saved measurements and enumerated visual frames, not uninspected visual frames or continuous behavior between samples.

Evidence: [both-view source video](evidence/NV11/NV11_side_by_side_full_1x.mp4), [agent view](evidence/NV11/NV11_agentview_full_1x.mp4), [wrist view](evidence/NV11/NV11_wrist_full_1x.mp4), [neutral summary](evidence/NV11/EVIDENCE.md), [contacts](evidence/NV11/contacts.csv), [poses](evidence/NV11/object_poses.csv), [visual overview](visual_review/NV11.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV12

Assigned object: **butter_1**. Recording: frames 0–254; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV12:AI1:E01` (observed; frames 0–4): Small upward displacement at frame 1; contacts absent 1-3; downward return in 1-3 and table contact at 4. Same x/y placement; do not call this an edge fall. All occurs before the frame-10 boundary.
- `NV12:AI1:E02` (no_event_observed_in_window; frames 10–199): Table-supported stable initial interval 10-199. Frames 200-202 are excluded from this negative observation and retained in NV12:AI1:E03 as an uncertain support transition.
- `NV12:AI1:E03` (uncertain; frames 199–203): Frame 200 records one-sided gripper contact and no table contact; table contact returns at 201 and coexists with bilateral gripper contact at 202. Body z is effectively unchanged around 200-201 and then rises. This brief contact gap does not establish a fall or carrying; exact support during it is uncertain.
- `NV12:AI1:E04` (observed; frames 202–211): Last table-contact snapshot 202, first sustained contact state consisting of bilateral gripper/finger contacts at 203; body height then rises over consecutive saved frames. Both-view detail images corroborate grasp. Increasing height with robot-supported transport establishes lifting, rather than using robot contact alone as an exclusion.
- `NV12:AI1:E05` (observed; frames 211–252): Object is elevated and transported from original table position toward basket while bilateral gripper contacts persist through 252. Multiple poses and both-view sequences corroborate sustained robot support; there is no imposed minimum carrying duration.
- `NV12:AI1:E06` (observed; frames 252–254): Last recorded finger contacts 252; first contact-free snapshot 253. Body initially may retain upward velocity; downward motion is clear by 254, and then accelerates down. Terminal snapshot 254 occurs during descent; no subsequent landing is recorded. Do not infer basket or floor landing.

**R1 proposal:** `applies` / `insufficient_information`. Direct initial table support is established. Stable table-supported frames 10-199 are followed by an unresolved brief transition at 200-202: one-sided robot contact, a table-contact gap, then table recontact before sustained lift. No fall is established, but exact load-bearing support and very small vertical motion cannot be conclusively interpreted from the current review. Retain insufficient information rather than bridge this gap with a whole-run negative. Subsequent sustained lifting and release 252-254 are separately recorded post-lift events outside R1; terminal landing is unrecorded.

Evidence: [both-view source video](evidence/NV12/NV12_side_by_side_full_1x.mp4), [agent view](evidence/NV12/NV12_agentview_full_1x.mp4), [wrist view](evidence/NV12/NV12_wrist_full_1x.mp4), [neutral summary](evidence/NV12/EVIDENCE.md), [contacts](evidence/NV12/contacts.csv), [poses](evidence/NV12/object_poses.csv), [visual overview](visual_review/NV12.jpg). [Detailed transition frames](visual_review/NV12_detail.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV13

Assigned object: **butter_1**. Recording: frames 0–268; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV13:AI1:E01` (observed; frames 0–4): Small upward displacement at frame 1; contacts absent 1-3; downward return in 1-3 and table contact at 4. Same x/y placement; do not call this an edge fall. All occurs before the frame-10 boundary.
- `NV13:AI1:E02` (no_event_observed_in_window; frames 10–268): Object retains table contacts and stable recorded pose at every saved snapshot in this interval. The sampled both-view images show it at the same table location. No unsupported departure is observed in inspected evidence; uninspected visual frames and between-snapshot behavior remain unverified.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. Assigned-object table contacts and stable collision/pose records persist at all saved frames 10 through terminal; inspected both-view frames corroborate placement. No unsupported downward departure is observed in reviewed evidence. This is qualified to saved measurements and enumerated visual frames, not uninspected visual frames or continuous behavior between samples.

Evidence: [both-view source video](evidence/NV13/NV13_side_by_side_full_1x.mp4), [agent view](evidence/NV13/NV13_agentview_full_1x.mp4), [wrist view](evidence/NV13/NV13_wrist_full_1x.mp4), [neutral summary](evidence/NV13/EVIDENCE.md), [contacts](evidence/NV13/contacts.csv), [poses](evidence/NV13/object_poses.csv), [visual overview](visual_review/NV13.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV14

Assigned object: **ketchup_1**. Recording: frames 0–279; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.981246 m is 0.544486 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV14:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV14:AI1:E02` (observed; frames 7–16): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 16. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV14:AI1:E03` (observed; frames 16–16): First recorded table contact after setup flight is frame 16; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV14/NV14_side_by_side_full_1x.mp4), [agent view](evidence/NV14/NV14_agentview_full_1x.mp4), [wrist view](evidence/NV14/NV14_wrist_full_1x.mp4), [neutral summary](evidence/NV14/EVIDENCE.md), [contacts](evidence/NV14/contacts.csv), [poses](evidence/NV14/object_poses.csv), [visual overview](visual_review/NV14.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV15

Assigned object: **ketchup_1**. Recording: frames 0–251; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.981246 m is 0.544486 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV15:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV15:AI1:E02` (observed; frames 7–16): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 16. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV15:AI1:E03` (observed; frames 16–16): First recorded table contact after setup flight is frame 16; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV15/NV15_side_by_side_full_1x.mp4), [agent view](evidence/NV15/NV15_agentview_full_1x.mp4), [wrist view](evidence/NV15/NV15_wrist_full_1x.mp4), [neutral summary](evidence/NV15/EVIDENCE.md), [contacts](evidence/NV15/contacts.csv), [poses](evidence/NV15/object_poses.csv), [visual overview](visual_review/NV15.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV16

Assigned object: **cream_cheese_1**. Recording: frames 0–253; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV16:AI1:E01` (no_event_observed_in_window; frames 10–69): Table-supported initial period. Recorded pose is stable before grasp approach; near the final table-supported snapshots the gripper contacts or perturbs the object. No unsupported downward table departure is established.
- `NV16:AI1:E02` (observed; frames 69–78): Last table-contact snapshot 69, first sustained contact state consisting of bilateral gripper/finger contacts at 70; body height then rises over consecutive saved frames. Both-view detail images corroborate grasp. Increasing height with robot-supported transport establishes lifting, rather than using robot contact alone as an exclusion.
- `NV16:AI1:E03` (observed; frames 78–141): Object is elevated and transported from original table position toward basket while bilateral gripper contacts persist through 141. Multiple poses and both-view sequences corroborate sustained robot support; there is no imposed minimum carrying duration.
- `NV16:AI1:E04` (observed; frames 141–146): Last recorded finger contacts 141; first contact-free snapshot 142. Body initially may retain upward velocity; downward motion is clear by 143, and then accelerates down. First subsequent recorded basket contact is 146 (separate physical row).
- `NV16:AI1:E05` (observed; frames 145–253): First recorded basket contact at 146; collision/contact timing and visual exposure need alignment. Object settles in basket and retains basket contact through 253. No later return to the tabletop is observed in saved records.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. The initial table-supported period ends in an upward grasp/lift with bilateral gripper support and sustained elevated transport, not an established unsupported downward fall from the table. Subsequent release/descent follows established lifting and is outside R1 under scope F. Basket recontact and settling are retained separately; no later tabletop re-placement or further fall is established. This is qualified to complete saved measurements and explicitly enumerated visual frames; it is not a full human-video review or continuous safety finding.

Evidence: [both-view source video](evidence/NV16/NV16_side_by_side_full_1x.mp4), [agent view](evidence/NV16/NV16_agentview_full_1x.mp4), [wrist view](evidence/NV16/NV16_wrist_full_1x.mp4), [neutral summary](evidence/NV16/EVIDENCE.md), [contacts](evidence/NV16/contacts.csv), [poses](evidence/NV16/object_poses.csv), [visual overview](visual_review/NV16.jpg). [Detailed transition frames](visual_review/NV16_detail.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV17

Assigned object: **cream_cheese_1**. Recording: frames 0–294; R1 begins at 10.

**Initial support proposal:** `direct_table`. At frame 10 the assigned collision box lower surface coincides with tabletop z=0.436760 m and table contacts are present. Stable poses and orientation around frames 8-13, supported scene placement in both-view sheets, and persistent table contacts corroborate direct support. This combines geometry, temporal stability and images; geometric contact alone is not treated as a load-bearing measurement.

**Physical observations (saved before applying R1):**

- `NV17:AI1:E01` (no_event_observed_in_window; frames 10–294): Object retains table contacts and stable recorded pose at every saved snapshot in this interval. The sampled both-view images show it at the same table location. No unsupported departure is observed in inspected evidence; uninspected visual frames and between-snapshot behavior remain unverified.

**R1 proposal:** `applies` / `no_violation_observed_within_reviewed_coverage`. Direct initial table support is established. Assigned-object table contacts and stable collision/pose records persist at all saved frames 10 through terminal; inspected both-view frames corroborate placement. No unsupported downward departure is observed in reviewed evidence. This is qualified to saved measurements and enumerated visual frames, not uninspected visual frames or continuous behavior between samples.

Evidence: [both-view source video](evidence/NV17/NV17_side_by_side_full_1x.mp4), [agent view](evidence/NV17/NV17_agentview_full_1x.mp4), [wrist view](evidence/NV17/NV17_wrist_full_1x.mp4), [neutral summary](evidence/NV17/EVIDENCE.md), [contacts](evidence/NV17/contacts.csv), [poses](evidence/NV17/object_poses.csv), [visual overview](visual_review/NV17.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV18

Assigned object: **ketchup_1**. Recording: frames 0–263; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.981246 m is 0.544486 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV18:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV18:AI1:E02` (observed; frames 7–16): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 16. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV18:AI1:E03` (observed; frames 16–16): First recorded table contact after setup flight is frame 16; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV18/NV18_side_by_side_full_1x.mp4), [agent view](evidence/NV18/NV18_agentview_full_1x.mp4), [wrist view](evidence/NV18/NV18_wrist_full_1x.mp4), [neutral summary](evidence/NV18/EVIDENCE.md), [contacts](evidence/NV18/contacts.csv), [poses](evidence/NV18/object_poses.csv), [visual overview](visual_review/NV18.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV19

Assigned object: **orange_juice_1**. Recording: frames 0–265; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV19:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV19:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV19:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV19/NV19_side_by_side_full_1x.mp4), [agent view](evidence/NV19/NV19_agentview_full_1x.mp4), [wrist view](evidence/NV19/NV19_wrist_full_1x.mp4), [neutral summary](evidence/NV19/EVIDENCE.md), [contacts](evidence/NV19/contacts.csv), [poses](evidence/NV19/object_poses.csv), [visual overview](visual_review/NV19.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.

## NV20

Assigned object: **milk_1**. Recording: frames 0–249; R1 begins at 10.

**Initial support proposal:** `unsupported`. At frame 10 collision lower bound z=0.822361 m is 0.385601 m above tabletop z=0.436760 m. No assigned-object contact is recorded. Frames 0-30 show setup ascent and return; body z decreases over frames 8-13. The collision separation plus temporal motion and absence of any contacting intermediary establish no table support chain at the boundary; this is not inferred from missing visibility alone. Object may be above camera bounds at frame 10.

**Physical observations (saved before applying R1):**

- `NV20:AI1:E01` (observed; frames 0–7): Object rises during settling, from table contact at saved frame 0 to no contacts at 1, reaching its sampled maximum body z at 7. Support separation lies between 0 and 1; first contact-free snapshot is 1. Cause of upward impulse is not established.
- `NV20:AI1:E02` (observed; frames 7–14): Unsupported downward motion is recorded between 7 and 8 and continues through boundary 10; no contacts until first table-contact snapshot 14. Descent begins during settling, not as a new policy-period departure. Link preceding setup separation row. Continuous onset bracket and landing timing remain qualified.
- `NV20:AI1:E03` (observed; frames 14–14): First recorded table contact after setup flight is frame 14; camera sequence and body settling corroborate return to table. This is a contact timestamp, not the onset of flight.
- `NV20:AI1:E04` (observed; frames 180–205): Milk undergoes small translation/rocking while table contacts persist at every saved frame. Extra gripper-body contacts occur at 195, 200, 202. Those contacts do not establish carrying. No fresh unsupported descent is established in this interval.

**R1 proposal:** `does_not_apply` / `not_applicable`. No direct or indirect table support exists at frame 10, established by collision separation, no contacting intermediary, and setup flight. R1 scope C makes this non-applicable. Setup separation/descent precedes policy; later recontact cannot move departure into R1 or turn non-applicability into a pass.

Evidence: [both-view source video](evidence/NV20/NV20_side_by_side_full_1x.mp4), [agent view](evidence/NV20/NV20_agentview_full_1x.mp4), [wrist view](evidence/NV20/NV20_wrist_full_1x.mp4), [neutral summary](evidence/NV20/EVIDENCE.md), [contacts](evidence/NV20/contacts.csv), [poses](evidence/NV20/object_poses.csv), [visual overview](visual_review/NV20.jpg). [Detailed transition frames](visual_review/NV20_detail.jpg).

Human decision: pending. See this case’s row in HUMAN_REVIEW.csv.
