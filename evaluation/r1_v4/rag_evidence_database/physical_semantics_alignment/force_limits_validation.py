"""Verify force-equation parameter prerequisites for every exact native variant."""
import json,mujoco
from .config import WORK
from .audit import save
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def run():
 assert mujoco.__version__=='3.8.1';rows=[]
 for p in sorted((WORK/'models').glob('*.json')):
  meta=json.loads(p.read_text());assert sha(meta['xml_path'])==meta['xml_sha256'];m=mujoco.MjModel.from_xml_path(meta['xml_path']);assert m.nu==9
  assert list(map(bool,m.actuator_forcelimited))==[False]*7+[True]*2
  for i in (7,8):assert m.actuator_forcerange[i].tolist()==[-20.,20.]
  assert m.actuator_gaintype.tolist()==[0]*9 and m.actuator_biastype.tolist()==[0]*7+[1]*2
  assert m.actuator_gainprm[:7,0].tolist()==[1.]*7 and m.actuator_gainprm[7:,0].tolist()==[1000.]*2
  assert m.actuator_biasprm[7:,0].tolist()==[0.,0.] and m.actuator_biasprm[7:,1].tolist()==[-1000.,-1000.] and m.actuator_biasprm[7:,2].tolist()==[0.,0.]
  rows.append(dict(variant_id=meta['variant_id'],xml_sha256=meta['xml_sha256'],forcerange=m.actuator_forcerange.tolist(),forcelimited=m.actuator_forcelimited.tolist(),ctrlrange=m.actuator_ctrlrange.tolist(),mujoco_version=mujoco.__version__,simulations_stepped=0))
 save(WORK/'FORCE_LIMITS_VALIDATION.json',dict(passed=True,variants=len(rows),actuator_parameters_checked=len(rows)*9,rows=rows));print('FORCE LIMITS VERIFIED',len(rows),flush=True)
if __name__=='__main__':run()
