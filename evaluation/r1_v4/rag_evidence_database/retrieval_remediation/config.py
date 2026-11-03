from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5k-working')
DATABASE=Path('/disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite')
DATABASE_SHA='f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8'
BASE_COMMIT='1ee2c34832e225f2ba26fd413499315782e0e5d5'
VERSION='retrieval-remediation-1.0.0'
SEED='phase5k-independent-v1'
CHANNELS=('raw.robot0_gripper_qpos','raw.robot0_gripper_qvel','raw.robot0_joint_pos','raw.robot0_joint_vel','raw.simulator_actuator_force','simulator.ncon')
FIELDS=('raw_observation/robot0_gripper_qpos/value','raw_observation/robot0_gripper_qvel/value','raw_observation/robot0_joint_pos/value','raw_observation/robot0_joint_vel/value','simulator/actuator_force/value','simulator/ncon/value')
UNITS=('m','m/s','rad','rad/s','native_actuator_force','count')
FAMILIES=CHANNELS+('action_metadata','inference_metadata','recorded_time','source_provenance','geometry_identity','main_table_identity','execution_metadata','contact_references','camera_references')
MODES=('exact','lexical','semantic','field_single','hybrid_single','bundle')
