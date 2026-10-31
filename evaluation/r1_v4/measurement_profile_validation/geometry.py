"""BOX computations with outward roundoff envelopes; no physical predicates."""
import itertools,math
import numpy as np
SIGNS=tuple(itertools.product((-1,1),repeat=3))
def corners(position,rotation,half_sizes):
 p=np.asarray(position,dtype=float);r=np.asarray(rotation,dtype=float).reshape(3,3);s=np.asarray(half_sizes,dtype=float)
 if p.shape!=(3,) or s.shape!=(3,) or not all(np.isfinite(x).all() for x in (p,r,s)) or np.any(s<=0):raise ValueError('invalid_BOX_inputs')
 nominal=[];lower=[];upper=[]
 for sign in SIGNS:
  point=[];lo=[];hi=[]
  for axis in range(3):
   exact_inputs_sum=float(p[axis]);l=exact_inputs_sum;u=exact_inputs_sum
   for j in range(3):
    product=float(r[axis,j])*float(sign[j]*s[j])
    l=math.nextafter(l+math.nextafter(product,-math.inf),-math.inf)
    u=math.nextafter(u+math.nextafter(product,math.inf),math.inf)
   point.append(float(p[axis]+sum(r[axis,j]*sign[j]*s[j] for j in range(3))))
   lo.append(l);hi.append(u)
  nominal.append(point);lower.append(lo);upper.append(hi)
 if not all(np.isfinite(a).all() for a in (nominal,lower,upper)):raise ValueError('BOX_computation_overflow')
 return np.asarray(nominal),np.asarray(lower),np.asarray(upper)
def union(pieces):
 if not pieces:raise ValueError('missing_collision_pieces')
 nominal=np.concatenate([p[0] for p in pieces]);lo=np.concatenate([p[1] for p in pieces]);hi=np.concatenate([p[2] for p in pieces])
 return dict(min=nominal.min(axis=0).tolist(),max=nominal.max(axis=0).tolist(),outward_min=lo.min(axis=0).tolist(),outward_max=hi.max(axis=0).tolist(),max_computational_interval_width=float(np.max(hi-lo)),input_physical_uncertainty=None)
def displacement(before,after):
 a,al,au=before;b,bl,bu=after
 if a.shape!=b.shape:raise ValueError('shape_correspondence_missing')
 d=b-a;lo=np.nextafter(bl-au,-np.inf);hi=np.nextafter(bu-al,np.inf)
 return dict(min_vertex_dz=float(d[:,2].min()),max_vertex_dz=float(d[:,2].max()),min_vertex_dz_lower=float(lo[:,2].min()),max_vertex_dz_upper=float(hi[:,2].max()),max_vertex_displacement=float(np.linalg.norm(d,axis=1).max()),physical_motion_witness=False,input_physical_uncertainty=None)
def contact_metrics(contacts,object_ids,geometries,piece_bounds):
 own=set(object_ids);table=set(range(10,16));selected=[c for c in contacts if c['geom1'] in own or c['geom2'] in own]
 partners=sorted({c['geom2'] if c['geom1'] in own else c['geom1'] for c in selected})
 categories={'table':0,'floor':0,'robot':0,'other':0};proxies=[]
 for c in selected:
  child=c['geom1'] if c['geom1'] in own else c['geom2'];other=c['geom2'] if c['geom1'] in own else c['geom1']
  geom=geometries[other];body=geom['owner_body']
  kind='table' if other in table else 'floor' if other==8 else 'robot' if body.startswith(('robot0_','gripper0_')) else 'other';categories[kind]+=1
  if other in table:
   bottom=piece_bounds[child]['min'][2];top=piece_bounds[other]['max'][2]
   proxies.append(dict(self_geom=child,other_geom=other,signed_distance=c['dist'],vertical_AABB_gap=bottom-top,vertical_AABB_gap_minus_distance=bottom-top-c['dist'],contact_z_minus_AABB_midpoint=c['pos'][2]-(bottom+top)/2,not_a_face_or_load_test=True))
 return dict(recorded_contact_count=len(selected),partners=partners,categories=categories,table_contact_proxies=proxies,load_bearing_support=None)
