"""Independent joint/body ownership checks against exact XML and recorded native indexes."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from .config import WORK,NAMES
from .audit import save

def validate_joint(joint,index,xml):
 nodes={n.get('name'):n for n in xml.iter('joint') if n.get('name')};parents={child:parent for parent in xml.iter() for child in parent};node=nodes[joint['name']];body=parents[node]
 assert body.tag=='body' and body.get('name')==joint['body_name']
 assert index['body_names'][joint['body_id']]==joint['body_name']
 i=index['joint_names'].index(joint['name']);assert joint['id']==i and joint['qpos_address']==index['jnt_qposadr'][i] and joint['qvel_address']==index['jnt_dofadr'][i]
 return True

def run():
 joint_checks=actuator_checks=0;executions=set();variants=set()
 for p in (WORK/'models').glob('*.json'):
  m=json.loads(p.read_text());xml=ET.parse(m['xml_path']).getroot();act=list(xml.find('actuator'));variants.add(m['variant_id']);joints={j['id']:j for j in m['joints']}
  for binding in m['executions']:
   index=json.loads(Path(binding['index_path']).read_text());executions.add(binding['execution_id'])
   for j in m['joints']:
    if j['name'] in NAMES:validate_joint(j,index,xml);joint_checks+=1
   for a in m['actuators']:
    assert act[a['id']].get('name')==a['name'] and act[a['id']].get('joint')==joints[a['joint_id']]['name'];actuator_checks+=1
 save(WORK/'BINDING_VALIDATION.json',dict(passed=True,executions=len(executions),variants=len(variants),joint_body_identity_checks=joint_checks,actuator_joint_identity_checks=actuator_checks,frame='Exact XML parent body and recorded body/joint native IDs; no world Cartesian projection'))
 print('Independent body/actuator bindings passed',joint_checks,actuator_checks,flush=True)
if __name__=='__main__':run()
