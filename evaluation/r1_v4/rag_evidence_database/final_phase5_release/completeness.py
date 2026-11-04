"""Independent fulfillment checker consumes original explicit obligations, not a plan."""
import json
from evaluation.r1_v4.provenance import digest
from .config import *
def expected_frames(store,selector):
 if selector is None:return None
 if selector['kind']=='frames':return list(range(selector['start'],selector['end']+1))
 return [r[0] for r in store.db.execute('select frame from i_clock_labels where execution=? and sim_time>=? and sim_time<=? order by frame',(store.execution,selector['start'],selector['end']))]

def validate(request,bundle,store):
 errors=[];fulfilled=[];byid={g['obligation_id']:g for g in bundle['groups']};expected={o['id'] for o in request['obligations']}
 if len(byid)!=len(bundle['groups']) or set(byid)!=expected:errors.append('obligation_set_changed')
 binding=store.binding(request['execution_id'])
 for o in request['obligations']:
  g=byid.get(o['id'])
  if not g:continue
  if g['request_digest']!=digest(o) or g['family']!=o['family'] or g['mandatory']!=o['mandatory']:errors.append('obligation_identity_changed');continue
  frames=expected_frames(store,o.get('selector'));ok=g['status']=='AVAILABLE' and bool(g['items']);observed=set()
  for item in g['items']:
   if any(item[k]!=binding[k] for k in ('execution_id','task_id','variant_id')):errors.append('cross_scope_evidence')
   if item['integrity_status']!='verified_source':errors.append('unverified_evidence')
   if o['family'] in CHANNELS:
    row=store.db.execute('select body from rag_channel_records where id=?',(item['id'],)).fetchone()
    if not row:errors.append('unknown_original_record');continue
    raw=json.loads(row[0])
    if (raw['execution_id'],raw['channel_id'],raw['source_sha256'],raw['source_field'])!=(binding['execution_id'],o['family'],item['source_artifact']['sha256'],item['source_artifact']['selector']):errors.append('wrong_source_field')
    semantic=json.loads(store.db.execute('select body from h_semantics where raw_id=?',(item['id'],)).fetchone()[0]);props=semantic['properties']
    if item['interpretation_properties']!=props or item['units']!=props['units'] or item['coordinate_frame']!=props['coordinate_frame']:errors.append('interpretation_annotation_changed')
    if o.get('record_id',item['id'])!=item['id'] or o.get('source_sha256',raw['source_sha256'])!=raw['source_sha256'] or o.get('object_id',raw['object_id'])!=raw['object_id']:errors.append('source_constraint_changed')
    component=None
    if o.get('component'):
     names=[c['name'] for c in semantic['components']]
     if o['component'] not in names:errors.append('unknown_component')
     else:component=names.index(o['component'])
    for s in item['samples']:
     i=s['saved_frame_index'];observed.add(i)
     if frames is None or i not in frames or s['source_selector']!=f'/frames/{i:06d}/'+REGISTRY[o['family']]:errors.append('wrong_temporal_source_selector')
     if s['source_status']!='verified_source':errors.append('unverified_sample')
     if s['value_units']!=props['units']['value'] or s['coordinate_frame']!=props['coordinate_frame']['value']:errors.append('unit_or_frame_changed')
     if component is not None:
      if s.get('selected_component')!=semantic['components'][component] or s.get('selected_value')!=s['value'][component]:errors.append('component_projection_changed')
      if s.get('selected_value_units')!=o.get('units',props['units']['value']):errors.append('component_unit_changed')


   elif frames is not None:
    indices=[item.get('value',{}).get('saved_frame_index')]
    if o['family'] in ('recorded_time','camera_references','contact_references'):
     if indices[0] not in frames:errors.append('metadata_temporal_scope')
     observed.update(x for x in indices if x is not None)
   if o.get('object_id') and o['family']=='geometry_identity' and item['value'].get('object_id')!=o['object_id']:errors.append('wrong_object')
  if o['family'] in CHANNELS and (frames is None or set(frames)!=observed):ok=False
  if frames is not None and o['family'] in ('action_metadata','inference_metadata'):
   h=json.loads(store.db.execute('select body from h_execution where execution=?',(store.execution,)).fetchone()[0]);rows=[h['temporal_rows'][i] for i in frames if 0<=i<len(h['temporal_rows'])]
   if len(rows)!=len(frames) or any(i<11 for i in frames):ok=False
   if o['family']=='action_metadata':
    actual={i['value']['policy_step'] for i in g['items']};expected_actions={r['preceding_policy_action'] for r in rows if r['preceding_policy_action'] is not None}
    if actual-expected_actions:errors.append('wrong_action_scope')
    if actual!=expected_actions:ok=False
   else:
    actual={i['value']['chunk_id'] for i in g['items']};expected_chunks={r['chunk_id'] for r in rows if r['chunk_id'] is not None}
    if actual-expected_chunks:errors.append('wrong_inference_scope')
    if actual!=expected_chunks:ok=False
  if frames is not None and o['family'] in ('recorded_time','camera_references','contact_references') and observed!=set(frames):ok=False
  fulfilled.append(dict(obligation_id=o['id'],mandatory=o['mandatory'],satisfied=bool(ok)))
 return dict(passed=not errors,errors=errors,obligations=fulfilled,mandatory_fulfilled=bool(fulfilled) and all(x['satisfied'] for x in fulfilled if x['mandatory']),method='Original explicit request vs emitted obligations, original DB source binding and independent selector lookup')
