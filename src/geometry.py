"""MJCF hierarchy and compiler-resolved reference geometry; never execution evidence."""
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np


def xml_geometry(path):
    path = Path(path).resolve()
    root = ET.parse(path).getroot()
    bodies = {e.get('name'): e for e in root.findall('.//body') if e.get('name')}
    sensors = [{'type': e.tag, **e.attrib} for e in root.findall('./sensor/*')]
    world = root.find('worldbody')
    hierarchy = []

    def walk(element, parent='world'):
        for i, body in enumerate(element.findall('./body')):
            name = body.get('name') or f'{parent}/unnamed_body_{i}'
            hierarchy.append({'name': name, 'parent': parent, 'xml_attributes': dict(body.attrib),
                              'direct_geometry_count': len(body.findall('./geom'))})
            walk(body, name)
    if world is not None:
        walk(world)
    result = {'bodies': bodies, 'sensor_declarations': sensors, 'body_hierarchy': hierarchy,
              'native_surface_geometry': [], 'worldbody_geometry': [], 'all_geometry': [],
              'geometry_resolution': {'status': 'unresolved', 'source_xml': str(path),
                  'source_xml_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'pose_scope': 'Model reference configuration qpos0, not recorded execution poses.',
                  'limitations': ['Geometry is not an approved support binding, safety rule, or observed contact.']}}
    try:
        import mujoco
        model = mujoco.MjModel.from_xml_path(str(path))
        data = mujoco.MjData(model)
        # Kinematics only: no mj_step, rollout, rendering, or robot experiment.
        mujoco.mj_kinematics(model, data)
    except (ImportError, ValueError, RuntimeError) as error:
        result['geometry_resolution']['error'] = str(error)
        # Preserve raw subtree declarations, including unnamed geometry. Do not guess transforms/defaults.
        for name, body in bodies.items():
            if name in ('table', 'floor') or name.endswith('_table'):
                result['native_surface_geometry'].append({'native_body_name': name,
                    'geometries': [{'xml_attributes': dict(g.attrib), 'transform_status': 'unresolved'}
                                   for g in body.findall('.//geom')], 'verification': 'unresolved'})
        if world is not None:
            result['worldbody_geometry'] = [{'xml_attributes': dict(g.attrib), 'transform_status': 'unresolved'}
                                           for g in world.findall('./geom')]
        return result
    name = lambda kind, i: mujoco.mj_id2name(model, kind, i)
    body_names = [name(mujoco.mjtObj.mjOBJ_BODY, i) or f'compiled_body_{i}' for i in range(model.nbody)]
    compiled_bodies = []
    for i in range(model.nbody):
        compiled_bodies.append({'body_id': i, 'name': body_names[i],
            'parent': body_names[int(model.body_parentid[i])] if i else None,
            'position_world_reference': data.xpos[i].tolist(),
            'rotation_world_reference': data.xmat[i].reshape(3, 3).tolist(),
            'has_joints': bool(model.body_jntnum[i]), 'mocap': int(model.body_mocapid[i]) >= 0})
    result['compiled_body_hierarchy'] = compiled_bodies
    explicit_pairs = set()
    for i in range(model.npair):
        explicit_pairs.update([int(model.pair_geom1[i]), int(model.pair_geom2[i])])
    for i in range(model.ngeom):
        bid = int(model.geom_bodyid[i]); ancestry = []; ancestor = bid
        while ancestor:
            ancestry.append(body_names[ancestor]); ancestor = int(model.body_parentid[ancestor])
        ancestry.append('world')
        rotation = data.geom_xmat[i].reshape(3, 3); position = data.geom_xpos[i]
        typ = int(model.geom_type[i]); size = model.geom_size[i]
        contype = int(model.geom_contype[i]); affinity = int(model.geom_conaffinity[i])
        collision = bool(contype or affinity or i in explicit_pairs)
        geom = {'geom_id': i, 'name': name(mujoco.mjtObj.mjOBJ_GEOM, i),
            'source_id': f'xml:{result["geometry_resolution"]["source_xml_sha256"]}:compiled_geom:{i}',
            'owner_body': body_names[bid], 'body_ancestry': ancestry,
            'type': mujoco.mjtGeom(typ).name.removeprefix('mjGEOM_').lower(),
            'size': size.tolist(), 'position_world_reference': position.tolist(),
            'rotation_world_reference': rotation.tolist(),
            'contype': contype, 'conaffinity': affinity, 'render_group': int(model.geom_group[i]),
            'explicit_contact_pair_member': i in explicit_pairs,
            'geometry_role': 'collision_enabled' if collision else 'visual_only',
            'role_qualification': 'Collision capability from effective masks/explicit pairs; actual contacts still depend on pair filtering and state.',
            'transform_status': 'compiler_resolved_model_reference'}
        if typ == mujoco.mjtGeom.mjGEOM_BOX:
            extent = np.abs(rotation) @ size
            geom['world_aabb_reference'] = {'min': (position-extent).tolist(), 'max': (position+extent).tolist()}
            # A geometric face candidate, not a semantic or approved table-top binding.
            if np.max(np.abs(rotation[2])) > 1-1e-8:
                geom['horizontal_upper_face_z_candidate'] = float(position[2]+extent[2])
        elif typ == mujoco.mjtGeom.mjGEOM_MESH:
            mid = int(model.geom_dataid[i]); start = int(model.mesh_vertadr[mid]); count = int(model.mesh_vertnum[mid])
            vertices = model.mesh_vert[start:start+count] @ rotation.T + position
            geom['mesh_asset'] = name(mujoco.mjtObj.mjOBJ_MESH, mid)
            geom['world_aabb_reference'] = {'min': vertices.min(axis=0).tolist(), 'max': vertices.max(axis=0).tolist()}
            geom['bounds_qualification'] = 'Compiled mesh vertices and compiler-resolved mesh/geom transforms; not an identified support face.'
        else:
            geom['bounds_qualification'] = 'No surface/extents derivation implemented for this primitive.'
        result['all_geometry'].append(geom)
        if bid == 0:
            result['worldbody_geometry'].append(geom)
    for body in compiled_bodies:
        n = body['name']
        if n in ('table', 'floor') or n.endswith('_table'):
            geoms = [g for g in result['all_geometry'] if n in g['body_ancestry']]
            result['native_surface_geometry'].append({'native_body_name': n, 'geometries': geoms,
                'selection_basis': 'Named surface candidate with all descendant-body geometry; not a prohibited region.',
                'verification': 'compiler_resolved_model_reference'})
    for g in result['worldbody_geometry']:
        if g['name'] in ('floor', 'table') or (g['name'] or '').endswith('_table'):
            result['native_surface_geometry'].append({'native_body_name': g['name'], 'owner_body': 'world',
                'geometries': [g], 'selection_basis': 'Named worldbody geometry; not a semantic support binding.',
                'verification': 'compiler_resolved_model_reference'})
    result['geometry_resolution'].update(status='compiler_resolved', compiler='mujoco',
        compiler_version=mujoco.__version__, body_count=model.nbody, geom_count=model.ngeom,
        units='MuJoCo model length units (normally meters); no independent physical calibration.',
        hierarchy_note='XML nesting retained separately; compiled hierarchy includes frames/defaults resolved by MuJoCo.')
    return result
