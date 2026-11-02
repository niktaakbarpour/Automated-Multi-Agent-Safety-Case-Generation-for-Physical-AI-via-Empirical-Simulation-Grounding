"""Property-wise classifications; direct readings remain separate from interpretation."""
from .config import VERSION
from evaluation.r1_v4.provenance import digest

def property(value,status='VERIFIED',basis='exact recorded source and version-bound model validation'):
 return dict(value=value,status=status,basis=basis)

def make(raw,execution,velocity,proofs):
 c=raw['channel_id'];count=c=='simulator.ncon';force=c=='raw.simulator_actuator_force';gripper='gripper_q' in c;vel=c.endswith(('qvel','joint_vel'));js=execution['joints'][7:] if gripper else execution['joints'][:7]
 if count:components=[];unit='count';frame='not_applicable_count';quantity='simulator_contact_entry_count'
 elif force:components=execution['actuators'];unit='native_actuator_force';frame='actuator_transmission';quantity='scalar_actuator_output'
 else:components=js;unit=('m/s' if vel else 'm') if gripper else ('rad/s' if vel else 'rad');frame='joint_tangent_velocity' if vel else 'joint_configuration';quantity='prismatic_joint_velocity' if gripper and vel else 'prismatic_joint_configuration' if gripper else 'hinge_joint_velocity' if vel else 'hinge_joint_configuration'
 props=dict(quantity=property(quantity),units=property(unit,basis='Native joint-angle/tangent units; linear length follows explicitly recorded metric convention. No physical calibration assertion.'),coordinate_frame=property(frame),component_order=property([x['name'] for x in components]),raw_vs_normalized=property('raw_recording; identity decode; not normalized policy input'),saved_sampling=property(dict(simulator_interval_seconds=.05,nominal_hz=20,physics_timestep_seconds=.002)),action_recording_order=property('frame k+11 saved after action k; inference input follows recorded chunk metadata'),missing_behavior=property('fail closed; no interpolation/filling'),physical_synchronization=property(None,'UNRESOLVED','No per-sensor timestamps or calibrated common-instant proof'),spatial_transform=property(None,'UNSUPPORTED','Configuration/tangent coordinates are not Cartesian world coordinates'))
 if force:
  props['component_dimensions']=property(['model_torque']*7+['model_linear_force']*2)
  props['si_component_units']=property(['N*m']*7+['N']*2,'CONDITIONAL','Requires MKS mass/length/time convention; physical force calibration unavailable')
  props['force_equation']=property('gain*ctrl + affine_bias(q_pre), declared limits; unit-gear joint transmission')
  props['contact_force_interpretation']=property(False,'UNSUPPORTED','Actuator force is not per-contact force or total generalized force')
 if not count and not force:
  props['cache_offset_seconds']=property(dict(initial=0.,noninitial=-.002),'CONDITIONAL','Euler-consistent preintegration interpretation; no runtime cache timestamp or binary attestation')
  props['algebraic_preintegration_relation']=property('inverse Euler velocity consistency' if vel else 'q_raw=q_endpoint-h*v_endpoint',basis='Full source/model comparisons; fixed float64 roundoff bounds')
  props['cache_sampling_rate_hz']=property(20,'CONDITIONAL','Version-matched Observable definition; individual sensor clock not recorded')
 props['physical_calibration']=property(None,'UNRESOLVED','Numeric consistency is not physical calibration')
 content=dict(version=VERSION,execution_id=raw['execution_id'],task_id=raw['task_id'],variant_id=raw['variant_id'],channel_id=c,raw_record_id=raw['id'],source_path=raw['source_path'],source_sha256=raw['source_sha256'],source_field=raw['source_field'],expected_dtype='int64' if count else 'float64',expected_shape=raw['contract']['shape'],properties=props,components=components,model_map_path=execution['model_map_path'],model_map_sha256=execution['model_map_sha256'],metadata_path=execution['metadata_path'],metadata_sha256=execution['metadata_sha256'],proof_digest=digest(proofs),traceability=proofs['validation_artifacts'],origin='interpretation_of_direct_recording',value_transformation='identity',new_measurement_channel=False,empirical_admission_enabled=False)
 return dict(id='semantics:'+digest(content),**content)
