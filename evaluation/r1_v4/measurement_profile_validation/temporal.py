"""Hypothesis residuals and observed clocks, never calibrated phase corrections."""
import numpy as np
def phase_residual(qpos,qvel,qacc,body_position,raw_position,qpos_address,dof_address,step):
 if any(x is None for x in (qpos,qvel,body_position)):return dict(endpoint_cache_residual=None,raw_two_substep_hypothesis_residual=None,calibrated_phase_bound=None)
 q=np.asarray(qpos)[qpos_address:qpos_address+3];v=np.asarray(qvel)[dof_address:dof_address+3]
 cache=float(np.max(np.abs(q-np.asarray(body_position)-step*v)))
 raw=None if raw_position is None or qacc is None else float(np.max(np.abs(np.asarray(raw_position)-(q-2*step*v+step*step*np.asarray(qacc)[dof_address:dof_address+3]))))
 return dict(endpoint_cache_residual=cache,raw_two_substep_hypothesis_residual=raw,calibrated_phase_bound=None)
def clock_summary(indices,times):
 if len(indices)!=len(times) or len(times)<2:raise ValueError('incomplete_clock_sample')
 dt=np.diff(np.asarray(times));return dict(first=float(times[0]),last=float(times[-1]),interval_min=float(dt.min()),interval_max=float(dt.max()),strictly_monotonic=bool(np.all(dt>0)),missing_indices=sorted(set(range(indices[-1]+1))-set(indices)),camera_exposure_bound=None,continuous_coverage=False)
