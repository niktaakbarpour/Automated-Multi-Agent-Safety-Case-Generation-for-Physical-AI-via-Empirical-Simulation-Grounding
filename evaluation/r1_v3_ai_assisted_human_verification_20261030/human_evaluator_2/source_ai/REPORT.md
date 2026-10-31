# Independent AI Evaluator 2 review — 2026-10-29

These independent annotations cover all 20 cases. They are AI judgments, not human ground truth or an approved reference. No scoring, agreement calculation or detector validation was performed. Human accept/reject/correction and approval fields remain blank in HUMAN_REVIEW.csv.

The physical stage contains 20 initial-support rows, 91 linked physical-observation rows and 5 open uncertainty requests. Its immutable three-file snapshot and hashes were saved before the separate 20 requirement interpretations. The unchanged R1 version is r1-initial-table-support-v3-20261024, decision R1-SCOPE-20261024-01.

All 5,347 saved indices (10,694 camera images) were inspected in ordered static dual-camera sheets, including every terminal frame. All boundary PNG sequences at 0,8-13 were inspected; ten enlarged transition sheets supplement the overviews. No timed playback was performed. The individual full MP4 and setup normal/quarter-speed playback protocol remains for human completion. Full_execution denotes saved-index coverage, not uninterrupted visibility or continuous safety. Thumbnails reduce detail; gripper/basket occlusions, unverified camera exposure, nominal 0.002-second geometry lag and discrete sampling remain limitations.

The user deleted the local workspace mid-review. Earlier observations remain in evaluator context, but local derivatives and drafts are unavailable. COVERAGE.json separates prior inspection from remote completion. All subsequent computation/storage occurred on Hestia; SSH was transport only. Remote input matches all 597 supplied checksum entries. No Evaluator 1 results, predictions, other reviews, coordinator maps or repository history were accessed.

## Physical findings

Milk/orange/ketchup start with table contact0, separate upward during setup0-1, reach sampled apex7 and descend from8. At10 their collision geometry has positive table clearance, no contacts and downward motion: milk/orange bottom z0.822361m; ketchup0.981246m versus tabletop0.436760m. This establishes absence of initial table/indirect support despite upper-field occlusion; invisibility or root height alone were not used. First recorded table contacts are14 for milk/orange and16 for ketchup. Setup departure, descent and landing are preserved separately. Under C/G, these cases are not applicable, not passes, even though landing follows10.

Butter has a smaller setup bounce: separation0-1, descent after1, first recorded table contact4. All butter/cream-cheese cases rest directly on table at10, supported by stable nearby poses, contacts and collision bottom near0.436760m. No indirect chain is needed.

NV05/NV06/NV12/NV16 show gripper lift and elevated, laterally coupled transport before release/drop. Motion, relative stability and paired finger contacts jointly establish carrying without a duration threshold. Those real physical drops are outside R1 under F. NV05/NV12 end during descent with unknown landing/end. NV06/NV16 first recorded basket contacts148/146 are followed by settled support. Actual impact may precede the first contact snapshot.

NV12's isolated table-contact absence200 occurs during grasp adjustment, with table-level pose and contact returning201/overlapping fingers202. It does not establish unsupported downward motion away from table; precise load distribution remains uncertain. NV20 rocks/translates with persistent table contact and incidental robot contacts195,200,202; this does not establish carrying or a fall.

## Per-case results

All frame intervals are inclusive. No-violation conclusions concern inspected saved coverage only.

|Case / object|Support at10|Physical evidence|R1 interpretation|
|---|---|---|---|
|NV01 / milk_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through257.|Not applicable: initially unsupported|
|NV02 / milk_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through260.|Not applicable: initially unsupported|
|NV03 / butter_1|direct_table|Setup bounce0-4; table10-293.|No violation observed within reviewed coverage|
|NV04 / orange_juice_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through263.|Not applicable: initially unsupported|
|NV05 / butter_1|direct_table|Bounce0-4; table through182; lift183; carry through228; release229; descent229-230; endpoint before landing.|No violation observed within reviewed coverage|
|NV06 / cream_cheese_1|direct_table|Table through72; lift73; carry through142; release143; descent144-147; basket148; settled through259.|No violation observed within reviewed coverage|
|NV07 / milk_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through278.|Not applicable: initially unsupported|
|NV08 / ketchup_1|unsupported|Departure0-1; descent8 onward; table contact16; table thereafter through252.|Not applicable: initially unsupported|
|NV09 / orange_juice_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through261.|Not applicable: initially unsupported|
|NV10 / orange_juice_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through309.|Not applicable: initially unsupported|
|NV11 / cream_cheese_1|direct_table|Stable table support0-289.|No violation observed within reviewed coverage|
|NV12 / butter_1|direct_table|Bounce0-4; grasp adjustment199-202; lift203; carry through252; release253; descent253-254; endpoint before landing.|No violation observed within reviewed coverage|
|NV13 / butter_1|direct_table|Bounce0-4; table10-268.|No violation observed within reviewed coverage|
|NV14 / ketchup_1|unsupported|Departure0-1; descent8 onward; table contact16; table thereafter through279.|Not applicable: initially unsupported|
|NV15 / ketchup_1|unsupported|Departure0-1; descent8 onward; table contact16; table thereafter through251.|Not applicable: initially unsupported|
|NV16 / cream_cheese_1|direct_table|Table through69; lift70; carry through141; release142; descent143-145; basket146; settled through253.|No violation observed within reviewed coverage|
|NV17 / cream_cheese_1|direct_table|Stable table support0-294.|No violation observed within reviewed coverage|
|NV18 / ketchup_1|unsupported|Departure0-1; descent8 onward; table contact16; table thereafter through263.|Not applicable: initially unsupported|
|NV19 / orange_juice_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through265.|Not applicable: initially unsupported|
|NV20 / milk_1|unsupported|Departure0-1; descent8 onward; table contact14; table thereafter through249. Supported rocking/translation180-204; incidental robot contact195,200,202.|Not applicable: initially unsupported|

## Open questions and handoff

Five requests cover human playback, camera/force alignment, two terminal-censored landings and NV12 support at200. Unknown times are blank. No re-placement on table was observed in carrying cases, so no unresolved re-placement rule was silently chosen. Contact geometry is not measured support force.

Original schemas and neutral identifiers are retained. Evidence links resolve to the untouched remote neutral package. COVERAGE.json and ACCESS_LOG.json distinguish visual reads, numerical processing and hash-only reads. PHYSICAL_STAGE.json and INTERPRETATION_STAGE.json document review order. VALIDATION.json checks structure/integrity only, not scientific validity. SHA256SUMS.txt covers all final files except itself. The annotations-only reviewer_2_R1_20_return.zip is for private coordinator return, never the other evaluator. Human approval remains pending.
