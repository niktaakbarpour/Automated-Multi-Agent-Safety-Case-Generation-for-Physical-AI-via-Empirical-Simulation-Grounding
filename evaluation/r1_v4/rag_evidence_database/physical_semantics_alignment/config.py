"""Phase 5H fixed scope and versioned interpretation policy."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5h-working')
BASE=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/expanded.sqlite')
BASE_SHA='d1241f28089ff910baf8ec276fbaa3f9d2b71aa3c7b850fe494b976eb51320fb'
BASE_COMMIT='a6830ad25f2f3d25ad9a28322985e128e5ab1374'
VERSION='physical-semantics-1.0.0'
NAMES=[f'robot0_joint{i}' for i in range(1,8)]+['gripper0_finger_joint1','gripper0_finger_joint2']
TOLERANCE_POLICY={'configuration_identity':'64*eps*(1+abs(q_endpoint)+abs(h*v_endpoint)) per component','actuator_equation':'64*eps*(1+abs(gain*ctrl)+abs(bias1*q_pre)) per component','timestamp_accumulation':'64*eps*(1+saved_frame*25)*(1+abs(time))','literal_source_values':0,'interpretation':'Bounds concern float64 arithmetic only; never physical/calibration tolerance.'}
