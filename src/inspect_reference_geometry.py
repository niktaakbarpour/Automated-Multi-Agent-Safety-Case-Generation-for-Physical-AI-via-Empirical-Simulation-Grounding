"""Inspect saved model/assets only; no outcomes, rollout, event checks, or model inference."""
import argparse, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
from facts import xml_info
from requirement_proposals import read, write, digest


def inspect(project, task_id, output):
    project = Path(project)
    task = next(t for t in read(project/'data/tasks.json')['records'] if t['task_id'] == task_id)
    run_id = task['facts']['objects']['reference_run_id']
    run = next(r for r in read(project/'data/runs.json')['records'] if r['run_id'] == run_id)
    source = Path(read(project/'config/project.json')['source_results'])
    xml_source = source/run['evidence']['simulator_xml']['source_relative_path']
    assert digest(xml_source.read_bytes()) == run['evidence']['simulator_xml']['sha256']
    evidence_dir = project/'evidence/geometry_v2'; evidence_dir.mkdir(exist_ok=True)
    snapshot = evidence_dir/'simulator.xml'
    if snapshot.exists(): assert snapshot.read_bytes() == xml_source.read_bytes()
    else: snapshot.write_bytes(xml_source.read_bytes())
    extracted = xml_info(xml_source)
    root = ET.parse(xml_source).getroot(); compiler = root.find('compiler')
    settings = compiler.attrib if compiler is not None else {}
    assets = []
    for asset in root.findall('./asset/*'):
        if not asset.get('file'): continue
        filename = asset.get('file')
        folder = settings.get('meshdir' if asset.tag=='mesh' else 'texturedir',settings.get('assetdir',''))
        p = Path(filename)
        if not p.is_absolute(): p = xml_source.parent/folder/p
        item = {'type':asset.tag,'name':asset.get('name'),'xml_file':filename,
                'resolved_path':str(p),'exists':p.is_file(),'attributes':dict(asset.attrib)}
        if p.is_file():
            with p.open('rb') as f: item['sha256'] = hashlib.file_digest(f,'sha256').hexdigest()
            item['bytes'] = p.stat().st_size
        assets.append(item)
    surfaces = extracted['native_surface_geometry']
    table = next(s for s in surfaces if s['native_body_name']=='living_room_table')
    table.update(collision_enabled_geoms=sum(g.get('geometry_role')=='collision_enabled' for g in table['geometries']),
                 visual_only_geoms=sum(g.get('geometry_role')=='visual_only' for g in table['geometries']))
    report = {'task_id':task_id,'reference_run_id':run_id,'source_xml_relative_path':str(xml_source.relative_to(source)),
        'source_xml_sha256':digest(xml_source.read_bytes()),'saved_xml':'evidence/geometry_v2/simulator.xml',
        'original_empty_geometry_explanation':'The named living_room_table body has sites but no direct geom. Seven geoms are in child living_room_table_col; body.findall(./geom) omitted them.',
        'table':table,'geometry_resolution':extracted['geometry_resolution'],
        'xml_body_hierarchy':extracted['body_hierarchy'],
        'compiled_body_hierarchy':extracted.get('compiled_body_hierarchy',[]),
        'worldbody_geometry':extracted['worldbody_geometry'],'assets':assets,
        'unresolved':['Supporting tabletop face and object-to-support semantic bindings are not validated.',
            'Reference transforms are qpos0/model-reference configuration, not per-frame execution poses.',
            'Bounds are geometric candidates, not approved fall thresholds or proof of support.',
            'No table height is inferred from object-center positions.'],
        'inspection_only_no_simulation_steps':True}
    write(output,report)
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True)
    ap.add_argument('--task-id',default='2448c758145ae5ad500f');ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();r=inspect(a.project,a.task_id,a.output)
    print(json.dumps({'geometry_resolution':r['geometry_resolution'],'collision_geoms':r['table']['collision_enabled_geoms'],
        'visual_geoms':r['table']['visual_only_geoms'],'assets':len(r['assets']),'missing_assets':sum(not a['exists'] for a in r['assets'])},indent=2))
