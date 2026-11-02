"""Hash-bound symbolic workspace mapping; no spatial sample or support inference."""
import json,sqlite3,xml.etree.ElementTree as ET,collections,ast
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .channels import WORK,BASE,owned
from .validate import save

RULE=dict(version='main-table-symbolic-binding-1.0.0',problem='libero_tabletop_manipulation',logical='main_table',fixture_category='table',arena_type='table',body_name='table',geom_name='table_collision',method='Recorded parsed BDDL + metadata-hash-bound task/domain/arena source + exact saved XML/native mapping. Symbolic identity only; no support/contact inference.')

def decide(problem,fixtures,attested,chain_ok,xml_ok,native_ok):
 if problem!=RULE['problem'] or RULE['logical'] not in fixtures.get('table',[]):return 'not_applicable_other_recorded_workspace'
 if not attested:return 'unresolved_producer_hash_binding'
 if not chain_ok:return 'unresolved_code_chain'
 if not xml_ok or not native_ok:return 'unresolved_variant_binding'
 return 'verified_symbolic_alias'

def run():
 c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);rows=[];hashcache={}
 def hashed(p):
  p=owned(p)
  if str(p) not in hashcache:hashcache[str(p)]=sha(p)
  return str(p),hashcache[str(p)]
 for e,body in c.execute('select execution,body from rag_execution_env order by execution'):
  b=json.loads(body);mp=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(e,)).fetchone()[0];directory=Path(mp).parent
  scene=directory/'semantic_initial_conditions.json';ev=directory/'evaluator_version.json';version=json.load(ev.open());s=json.load(scene.open());phases=s.get('phases',{'legacy':s});problems={v.get('parsed_bddl_problem',{}).get('problem_name') for v in phases.values()};assert len(problems)==1;problem=next(iter(problems));parsed=next(iter(phases.values())).get('parsed_bddl_problem',{});fixtures=parsed.get('fixtures',{})
  attested=True;chain=True;sources=[]
  suffixes=('problems/libero_tabletop_manipulation.py','bddl_base_domain.py','arenas/table_arena.py')
  texts=[]
  for suffix in suffixes:
   matches=[(p,h) for p,h in version.get('implementation_files_sha256',{}).items() if p.endswith('/'+suffix)]
   if len(matches)!=1:attested=False;texts.append('');continue
   original,expected=matches[0];path,actual=hashed(original);attested &= actual==expected;text=Path(path).read_text();ast.parse(text);texts.append(text);sources.append(dict(recorded_path=original,owned_path=path,expected_sha256=expected,actual_sha256=actual))
  if len(texts)==3:
   chain=all(x in texts[0] for x in ('self.workspace_name = "main_table"','kwargs.update({"arena_type": "table"})')) and all(x in texts[1] for x in ('if self._arena_type == "table":','mujoco_arena = TableArena(')) and all(x in texts[2] for x in ('self.table_body = self.worldbody.find("./body[@name=\'table\']")','self.table_collision = self.table_body.find("./geom[@name=\'table_collision\']")'))
  xml=ET.parse(b['xml_path']).getroot();bodies=[x for x in xml.iter('body') if x.get('name')=='table'];geoms=[x for x in xml.iter('geom') if x.get('name')=='table_collision'];xml_ok=len(bodies)==1 and len(geoms)==1 and geoms[0] in list(bodies[0])
  m=json.load(open(b['mapping_path']));m=m.get('mapping',m);native=[g for g in m['geometries'] if g['name']=='table_collision'];native_ok=len(native)==1 and native[0]['owner_body']=='table' and m['body_names'][native[0]['owner_body_id']]=='table' and m['source_xml_sha256']==b['xml_sha256'] and e in m['validated_run_ids']
  status=decide(problem,fixtures,attested,chain,xml_ok,native_ok)
  rows.append(dict(execution_id=e,task_id=b['task_id'],variant_id=b['variant_id'],problem_name=problem,recorded_fixtures=fixtures,status=status,producer_attested=bool(attested),source_chain_verified=bool(chain),sources=sources,evaluator_version_path=str(ev),evaluator_version_sha256=sha(ev),semantic_path=str(scene),semantic_sha256=sha(scene),xml_path=b['xml_path'],xml_sha256=b['xml_sha256'],mapping_path=b['mapping_path'],mapping_sha256=b['mapping_sha256'],exact_mapping=dict(logical_alias='main_table',body_name='table',body_id=native[0]['owner_body_id'],geom_name='table_collision',geom_id=native[0]['native_geom_id']) if status=='verified_symbolic_alias' else None,physical_support_inferred=False,spatial_samples_admitted=False))
 report=dict(passed=True,rule=RULE,status_counts=dict(collections.Counter(r['status'] for r in rows)),verified_variants=len({r['variant_id'] for r in rows if r['status']=='verified_symbolic_alias'}),verified_tasks=sorted({r['task_id'] for r in rows if r['status']=='verified_symbolic_alias'}),rows=rows,qualification='This audit derives a symbolic alias only. The frozen channel selection and legacy unsupported spatial query remain unchanged; no object support or physical event is inferred.')
 save('MAIN_TABLE_AUDIT.json',report);print({k:v for k,v in report.items() if k!='rows'},flush=True)
if __name__=='__main__':run()
