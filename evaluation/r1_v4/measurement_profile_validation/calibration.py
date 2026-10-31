"""Calibration feasibility table: no empirical physical threshold is proposed."""
import csv,json,socket
from .analyze import HERE
from evaluation.r1_v4.libero_evidence_audit.audit_sources import csvwrite,load

def main():
 assert socket.gethostname().lower()=='hestia'
 s=load(HERE/'DIAGNOSTIC_SUMMARY.json');g=s['global_ranges'];samples=list(csv.DictReader((HERE/'DIAGNOSTIC_SAMPLES.csv').open()));proxies=[p for r in samples for p in json.loads(r['contact_proxies'])]
 proxy_range=lambda key:json.dumps({'min':min(p[key] for p in proxies),'max':max(p[key] for p in proxies)}) if proxies else ''
 rows=[]
 def add(pid,name,definition,unit,source,method,sample,observed,uncertainty,bound,status,validation,limitations):
  rows.append(dict(parameter_id=pid,parameter=name,definition=definition,unit=unit,measurement_source=source,estimation_method=method,calibration_sample=sample,observed_range=observed,measurement_uncertainty=uncertainty,proposed_conservative_bound=bound,status=status,validation_method=validation,known_limitations=limitations,empirical_physical_threshold=False))
 add('P01','BOX_computational_roundoff','Rounding in p+R*corner for declared binary64 inputs','m','geom_xpos/geom_xmat + XML-declared BOX half sizes','Outward nextafter product/sum intervals','28 BOX pieces x1312 snapshots;27 exact-rational cases',json.dumps(g['box_roundoff_width']),'Computational only; physical input uncertainty remains null','Dynamic outward interval, not a fixed clearance or support tolerance','VERIFIED','Exact Fraction oracle:648 coordinates','Does not bound actual native shape/pose/model/phase uncertainty')
 add('P02','retained_transform_arithmetic_guard','Native body/local/world recomposition residual','m and rotation component','Pinned NativeGeometryIndex helper','Reuse existing512*epsilon arithmetic budget','1312 snapshots',json.dumps(s['transform_residuals']),'Arithmetic budget only','Existing formula:512*epsilon*max(1,coordinate scale); rotation512*epsilon','VERIFIED','Raw body/geometry transforms pass retained guard','No physical contact/alignment tolerance implied')
 physical=[
 ('P03','BOX_physical_geometry_tolerance','Difference between reconstructed collision envelope and native physical collision model','m','Serialized XML size/rotation descriptors and raw poses','Resolve native-size/serialization provenance and compare independent geometry references','Four executions; prior XML serialization audit','See GEOMETRY_CALIBRATION.md','No independent geometry-uncertainty reference; native geom_size not stored'),
 ('P04','surface_boundary_uncertainty','Uncertainty in designated support regions/faces','m','All six table collision pieces','Propagate validated shape/pose/serialization bounds; independent boundary checks','Same exact table model',json.dumps({r['geom_id']:r['bounds']['max'][2] for r in s['table_pieces']}),'No universal table-height/edge band; lower piece15 differs'),
 ('P05','support_contact_consistency','Geometric contact interpretation versus load-bearing support','m and physical role','Native contacts and BOX/pose comparisons','Validate face-role and alternative support model against independent references',f'{len(proxies)} selected table-contact observations',proxy_range('vertical_AABB_gap_minus_distance'),'Vertical AABB proxy is not signed normal distance for arbitrary contacts; no independent support labels'),
 ('P06','downward_motion_physical_uncertainty','Uncertainty in shape-corresponding gravity-frame displacement','m','Adjacent recorded collision corners','Combine validated input and phase uncertainty plus correspondence',f"{s['object_frames']} object frames",json.dumps(dict(min_dz=g['min_vertex_dz'],max_dz=g['max_vertex_dz'])),'Numerical motion indicators do not prove support loss, handling or event scope'),
 ('P07','persistence_requirement','Evidence persistence needed to resolve physical events','s or observations','Control-rate snapshots','Independent multi-rate event/onset reference and sensitivity study','No independent short-fall reference cases','No estimate','No minimum hazard duration is defined; no hysteresis invented'),
 ('P08','native_cache_alignment_uncertainty','Bound on cache phase relative to endpoint clock','s','qpos/qvel/body cache, physics step and producer order','Test Euler phase hypothesis then validate version-specific clock contract','All nonzero frames x5 objects',json.dumps({'translation_identity_residual_m':g['endpoint_cache_residual']}),'Nominal timestep0.002s is not a calibrated alignment bound; residual unit is meters'),
 ('P09','camera_exposure_alignment','Bound on exposure relative to native state','s','Camera dataset indices and host timestamps','Verify producer observable/exposure contract or retain qualitative modality','Selected24 arrays extracted; exposure timestamps absent','No observed exposure bound','Source timestamps/nominal20Hz do not establish synchronized capture'),
 ('P10','raw_observable_phase','Bound on raw-observation phase/frame relation','s','raw object positions plus qpos/qvel/qacc','Compare prior two-substep expression; independently validate producer semantics','All nonzero frames x5 objects',json.dumps({'position_fit_residual_m':g['raw_phase_hypothesis_residual']}),'Residuals in meters are not time-error bounds and do not transfer to cameras'),
 ]
 for pid,name,definition,unit,source,method,sample,observed,limit in physical:
  add(pid,name,definition,unit,source,method,sample,observed,'null: necessary physical/reference uncertainty unavailable','', 'BLOCKED_ON_EVIDENCE','Independent verified reference/profile needed',limit)
 csvwrite(HERE/'CALIBRATION_PARAMETERS.csv',rows)
 print('Parameters',len(rows),'empirical physical bounds proposed:0')
if __name__=='__main__':main()
