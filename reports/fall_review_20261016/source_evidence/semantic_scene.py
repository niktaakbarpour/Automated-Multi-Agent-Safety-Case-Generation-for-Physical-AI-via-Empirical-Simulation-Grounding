import numpy as np
def semantic_scene(env,raw,phase):
    e=env._env.env; sim=e.sim; m,d=sim.model,sim.data; parsed=e.parsed_problem
    objects={}; fixtures={}
    for category,collection in [('objects',e.objects_dict),('fixtures',e.fixtures_dict)]:
        dest=objects if category=='objects' else fixtures
        for name,obj in collection.items():
            bid=m.body_name2id(obj.root_body)
            dest[name]={'category_name':getattr(obj,'category_name',None),'root_body':obj.root_body,'initial_position_world_m':d.body_xpos[bid].copy(),'initial_orientation_wxyz':d.body_xquat[bid].copy(),'joints':list(obj.joints),'joint_positions':{j:np.asarray(d.get_joint_qpos(j)).copy() for j in obj.joints}}
    def atoms(x):
        if isinstance(x,(list,tuple)) and x:
            if str(x[0]).lower() in ['and','or','not']:
                return [a for child in x[1:] for a in atoms(child)]
            if isinstance(x[0],str): return [list(x)]
            return [a for child in x for a in atoms(child)]
        return []
    goals=atoms(parsed.get('goal_state',[])); regions=parsed.get('regions',{})
    def entity(name):
        if name in objects or name in fixtures:
            return {'entity':name,'source':'object_root_body','position_world_m':(objects|fixtures)[name]['initial_position_world_m'],'orientation_wxyz':(objects|fixtures)[name]['initial_orientation_wxyz']}
        if name in m.site_names:
            i=m.site_name2id(name); return {'entity':name,'source':'exact_named_site','position_world_m':d.site_xpos[i].copy(),'orientation_matrix':d.site_xmat[i].reshape(3,3).copy()}
        return {'entity':name,'source':None,'position_world_m':None,'reason':'No exact object root or simulator site exposed for this goal entity.','region_definition':regions.get(name)}
    target_names=list(dict.fromkeys(str(a[1]) for a in goals if len(a)>1))
    goal_names=list(dict.fromkeys(str(a[2]) for a in goals if len(a)>2))
    targets={n:entity(n) for n in target_names}; destinations={n:entity(n) for n in goal_names}
    robot=np.asarray(raw['robot0_eef_pos']); distances={n:float(np.linalg.norm(np.asarray(v['position_world_m'])-robot)) if v['position_world_m'] is not None else None for n,v in targets.items()}
    pairs={t:{g:float(np.linalg.norm(np.asarray(v['position_world_m'])-np.asarray(w['position_world_m']))) if v['position_world_m'] is not None and w['position_world_m'] is not None else None for g,w in destinations.items()} for t,v in targets.items()}
    mentioned={str(n) for a in goals for n in a[1:]}; interests=list(getattr(e,'obj_of_interest',[]))
    related=set(mentioned)|set(interests)
    related|={regions[n]['target'] for n in mentioned if n in regions and 'target' in regions[n]}
    distractors=sorted(set(objects)-related)
    cameras={}
    for i,name in enumerate(m.camera_names):
        cameras[name]={'position_world_m':d.cam_xpos[i].copy(),'orientation_matrix_world':d.cam_xmat[i].reshape(3,3).copy(),'position_parent_m':m.cam_pos[i].copy(),'orientation_parent_wxyz':m.cam_quat[i].copy(),'parent_body_id':int(m.cam_bodyid[i]),'vertical_fov_degrees':float(m.cam_fovy[i]),'recorded':name in ['agentview','robot0_eye_in_hand']}
    lighting={}
    for i in range(m.nlight):
        light={}
        for key in ['pos','dir','ambient','diffuse','specular','castshadow','directional','active','attenuation','cutoff','exponent']:
            attr='light_'+key
            if hasattr(m,attr): light[key]=np.asarray(getattr(m,attr)[i]).copy()
        for key in ['light_xpos','light_xdir']:
            if hasattr(d,key): light[key]=np.asarray(getattr(d,key)[i]).copy()
        lighting[str(i)]=light
    background={}
    for key in ['mat_rgba','mat_texid','mat_shininess','mat_specular','mat_reflectance','geom_rgba','geom_matid','tex_type','tex_width','tex_height']:
        if hasattr(m,key): background[key]=np.asarray(getattr(m,key)).copy()
    background['material_names']=list(m.material_names) if hasattr(m,'material_names') else None
    background['texture_names']=list(m.texture_names) if hasattr(m,'texture_names') else None
    sampler=[]
    for attr in ['placement_initializer','conditional_placement_initializer','conditional_placement_on_objects_initializer']:
        p=getattr(e,attr,None)
        if p is not None: sampler.append({'attribute':attr,'class':type(p).__module__+'.'+type(p).__qualname__,'repr':str(p)})
    single=next(iter(targets.values())) if len(targets)==1 else None
    scalar_pair=next(iter(next(iter(pairs.values())).values())) if len(pairs)==1 and len(destinations)==1 else None
    return {'phase':phase,'coordinate_system':'MuJoCo world; distances in meters; object quaternions wxyz. Camera orientation is a 3x3 matrix.','task_suite':env.suite_name,'task_horizon':env._max_episode_steps,'object_initial_poses':objects,'fixture_initial_poses':fixtures,'number_of_objects':len(objects),'number_of_fixtures':len(fixtures),'objects_of_interest':interests,'goal_predicates':goals,'target_entities':targets,'goal_entities':destinations,'target_object_initial_position':single.get('position_world_m') if single else None,'target_object_initial_orientation':single.get('orientation_wxyz') if single else None,'robot_end_effector_initial_position':robot,'robot_to_target_distance':next(iter(distances.values())) if len(distances)==1 else None,'robot_to_target_distances':distances,'target_to_goal_distance':scalar_pair,'target_to_goal_distances':pairs,'distance_definition':'Euclidean end-effector-to-target root/site and target-to-goal root/site distances; not grasp approach distance, clearance, goal satisfaction distance or distance to a region boundary. Null if no unique exact entity position is exposed.','number_of_distractors':len(distractors),'distractor_objects':distractors,'distractor_definition':'Derived proxy: movable objects absent from goal entities, goal-region owners, and benchmark objects_of_interest. Not an official distractor annotation.','benchmark_distractor_labels_exposed':False,'camera_pose':cameras,'lighting':lighting,'background_settings':background,'parsed_bddl_problem':parsed,'randomization_parameters':{'protocol':'Official benchmark initial-state archive indexed by episode; native reset/10 settling steps. No added domain randomization.','region_definitions':regions,'initial_predicates':parsed.get('initial_state'),'placement_samplers':sampler,'reset_seed':env.episode_seed},'unavailable_semantics':{'single_target_or_goal':'Null when predicates do not identify a unique exact target/goal point.','sampler_draws':'Internal placement-sampler random draws are not exposed; official selected state and realized object poses are saved.','background_image':'No separate background image exposed; material/texture configuration, model XML and asset provenance are saved.'}}

