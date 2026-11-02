# Measurement channel coverage and exclusions

The six indexed raw measurement families are object_pose (body_xpos,
body_xquat), native_geometry (geom_xpos, geom_xmat), contact (recorded contact
identities/distances/positions), robot_state (qpos, qvel, ctrl), timestamp
(saved time), and camera_reference (agentview and eye-in-hand image references).
Each unit covers a bounded saved-frame window, with native object/body and
collision IDs, exact HDF5 selector, original source hash and scope. Source arrays
are not duplicated in the database. Shared robot/camera/contact source groups
are contextual references under each object; they are not claims of an
object-specific physical interaction or independently acquired measurements.

Native qpos/qvel include the recorded robot/gripper and free-object state,
with the original simulator joint mapping available in the hash-bound source
index. The reader also exposes available raw joint/gripper observables, but raw
observable coordinate/unit/quaternion conventions remain explicitly unverified.
Do not treat a query scoped to one object as proof that the robot contacted it.

Other saved simulator arrays include act, actuator_force, cfrc_ext, cvel,
flattened, ncon, qacc and sensordata. These remain in their original hash-bound
files and in per-execution channel inventories; they are not new separately
searchable measurement families in this release. Site poses (site_xpos,
site_xmat) are listed but not exposed by the restricted reader. Aggregate body or
actuator arrays are not recorded per-contact forces or normals, and must not be
substituted for those missing fields.

Raw observation inventories include object positions/quaternions, relative
object-to-end-effector observables, robot end-effector pose, gripper position and
velocity, joint position/velocity and encoded proprioceptive vectors. The reader
reports unexposed relative/proprioceptive fields. RAG does not silently upgrade
unverified coordinate conventions or index these as calibrated physical events.
Per-execution available/unexposed field inventories and diagnostic codes are in
validation/BUILD_MANIFEST.json. Camera pixel arrays are not copied into SQLite;
exposure alignment remains unsupported.

A request for an unindexed measurement type, such as contact_force, returns a
missing type/interval, not a negative observation. Tests cover this explicitly.
Indexing all six supported families does not mean every saved field has a
standalone retrieval unit, every physical capability is valid, or every source
file/media asset from the historical archive has been restored. Restoration is
exactly the nine required episode files plus two shared task files per task.
Additional channel extractors are future database-only work and require their
own declared frame, unit and provenance contracts.

## Instruction source variants

All four BDDL language clauses say "Pick the ...", whereas recorder metadata
says "pick up the ...". Task names, checkpoint revisions and metadata-to-BDDL
hash bindings match for every execution, but the two strings are not literally
identical. TASK_DECLARATIONS.json preserves both sources without asserting
semantic equivalence. The indexed task_instruction units quote `/instruction`
from run_metadata.json, not the BDDL language clause. BDDL files are separately
hash-bound source references; this release does not silently rewrite metadata
or claim that its instruction chunk is a verbatim BDDL quote.
