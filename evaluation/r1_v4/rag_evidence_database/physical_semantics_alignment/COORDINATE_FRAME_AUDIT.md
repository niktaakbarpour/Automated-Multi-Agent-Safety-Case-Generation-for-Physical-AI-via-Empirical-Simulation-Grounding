# Configuration, velocity and geometry frames

The four robot/gripper arrays are joint configuration/tangent velocities, not Cartesian vectors. Seven hinge components use radians and rad/s. Two slide components use model length/second, interpreted in m and m/s under the explicitly recorded metric convention. Signed axes and zero follow exact XML joints; no finger-opening-distance conversion is applied.

GEOMETRY_BINDINGS.csv lists native joint/body/actuator IDs, qpos/qvel addresses, body-local axes/anchors, gears and XML/model hashes for all 104 variants. Recorded indexes check every execution. BINDING_VALIDATION.json independently verifies 3,888 joint/body and 3,888 actuator/joint associations. Robot identity is the exact variant model, not a generic robot0-array assumption.

No world transform is implemented. Axis origin/orientation belongs to the owning body; configuration is not world position. No pixel/world calibration, camera clock, support inference or force-frame projection. Projection y=x[j] is an exact component view with selector/index/identity and unchanged float64 value; domain/codomain are the same native coordinate.

Phase 5G main_table remains a derived identity for 147 tabletop executions/98 variants. Floor/living-room domains do not inherit it. Source hashes/scope are preserved. Neither identity nor candidate geometry enables logical-table poses or establishes support/contact/falling.
