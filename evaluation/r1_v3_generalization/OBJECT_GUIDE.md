# Object identity guide

The five protected scene identities remain cream_cheese_1, ketchup_1, orange_juice_1,
milk_1 and butter_1. Other scene identities are alphabet_soup_1, tomato_sauce_1 and
basket_1. living_room_table names the table. These names identify entities, not
initial support, event types or expected outcomes.

The instruction differs by task; read the original instruction recorded for each run
in evidence_manifest.json. A task target is not automatically exempt from the unchanged
named R1 scope. Record uncertainty rather than assuming an outcome from task intent.

Both full camera views and boundary images come from each run's own recording. The
native_geometry.csv maps collision geometry to owner bodies, and object_poses.csv
links world poses to canonical IDs. Appearance, object-center proximity and geometric
contact alone do not establish visibility or load bearing. Use temporal continuity,
both cameras and neutral measurement references; retain uncertain identity if occluded.
No images or event labels from the original four reviewed executions are included.
