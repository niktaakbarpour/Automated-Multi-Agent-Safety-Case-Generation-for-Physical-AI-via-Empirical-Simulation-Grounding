"""Versioned native-ID access for recorded contact evidence; no fall classification.

Never accept simulator_index.geom_names as a native-ID array. It is a lossy
name projection. Corrected inventories carry the XML hash and all native IDs.
"""
import json
from pathlib import Path

SCHEMA='native-geometry-index-v2'

class NativeGeometryIndex:
    def __init__(self, record):
        if record.get('schema_version')!=SCHEMA:
            raise ValueError('Require corrected native-geometry-index-v2; legacy geom_names is not an ID index')
        self.record=record
        self.geometries=record['geometries']
        if [g['native_geom_id'] for g in self.geometries]!=list(range(record['native_geom_count'])):
            raise ValueError('Native IDs must be complete and contiguous, including every anonymous geom')
        if not record.get('source_xml_sha256'):
            raise ValueError('Missing source XML identity')
        self.names={}
        for g in self.geometries:
            n=g['name']
            if n is not None:
                if n in self.names:raise ValueError('Duplicate named geom')
                self.names[n]=g['native_geom_id']

    @classmethod
    def load(cls,path):return cls(json.loads(Path(path).read_text()))

    def by_id(self,native_id):
        if isinstance(native_id,bool) or not isinstance(native_id,int) or not 0<=native_id<len(self.geometries):
            raise ValueError('Invalid native contact geometry ID')
        return self.geometries[native_id]

    def named_id(self,name):
        if name is None:raise ValueError('Anonymous geometry must be addressed by native ID')
        return self.names[name]

    def contact_pair(self,contact):
        return self.by_id(contact['geom1']),self.by_id(contact['geom2'])

    def validate_recording(self,run_id,xml_sha256,geom_count):
        if xml_sha256!=self.record['source_xml_sha256'] or geom_count!=len(self.geometries):
            raise ValueError('Recording/model geometry identity mismatch')
        if run_id not in self.record['validated_run_ids']:
            raise ValueError('Run not validated against this corrected mapping')

    def geometries_for_body(self,body_name,descendants=True):
        return [g for g in self.geometries if body_name==g['owner_body'] or (descendants and body_name in g['body_ancestry'])]

    def validate_snapshot_transforms(self,body_positions,body_quaternions_wxyz,geom_positions,geom_rotations):
        """Read-only identity/phase guard. Never alters arrays or classifies an event."""
        import numpy as np
        bp=np.asarray(body_positions);q=np.asarray(body_quaternions_wxyz)
        gp=np.asarray(geom_positions);gr=np.asarray(geom_rotations)
        nb=len(self.record['body_names']);ng=len(self.geometries)
        if bp.shape!=(nb,3) or q.shape!=(nb,4) or gp.shape!=(ng,3) or gr.shape not in [(ng,9),(ng,3,3)]:
            raise ValueError('Snapshot geometry/body array shape mismatch')
        if not all(np.isfinite(a).all() for a in [bp,q,gp,gr]) or np.any(np.sum(q*q,axis=1)==0):
            raise ValueError('Invalid snapshot numerical values')
        w,x,y,z=q.T;s=2/np.sum(q*q,axis=1)
        br=np.stack([1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w),s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w),s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)],axis=-1).reshape(nb,3,3)
        ids=np.array([g['owner_body_id'] for g in self.geometries])
        localp=np.array([g['local_position_derived_from_recorded_snapshot'] for g in self.geometries]);localr=np.array([g['local_rotation_derived_from_recorded_snapshot'] for g in self.geometries])
        expectedp=bp[ids]+np.einsum('gij,gj->gi',br[ids],localp);expectedr=br[ids]@localr
        pe=float(np.max(np.abs(expectedp-gp)));re=float(np.max(np.abs(expectedr-gr.reshape(ng,3,3))))
        rt=512*np.finfo(float).eps;pt=rt*max(1.,float(np.max(np.abs(bp))),float(np.max(np.abs(gp))))
        if pe>pt or re>rt:raise ValueError('Geometry identity/transform/phase consistency failed; no legacy fallback permitted')
        return {'position_error_m':pe,'rotation_component_error':re,'position_arithmetic_allowance_m':pt,'rotation_arithmetic_allowance':rt,'physical_or_fall_tolerance':False}

def corrected_entity_inventory(original_runs,index):
    """New derived records only. Do not copy legacy numerical geom_ids."""
    records=[]
    for run in original_runs:
        index.validate_recording(run['run_id'],run['evidence']['simulator_xml']['sha256'],len(index.geometries))
        entities=[]
        for obj in run['objects']:
            gs=index.geometries_for_body(obj['root_body_name'])
            entities.append({'name':obj['name'],'root_body_name':obj['root_body_name'],
                'body_id':obj['body_id'],'joint_ids':obj['joint_ids'],
                'native_geom_ids':[g['native_geom_id'] for g in gs],
                'named_geom_ids':{g['name']:g['native_geom_id'] for g in gs if g['name'] is not None},
                'anonymous_geom_ids':[g['native_geom_id'] for g in gs if g['name'] is None]})
        records.append({'run_id':run['run_id'],'task_id':run['task_id'],'entities':entities,
            'source_xml_sha256':index.record['source_xml_sha256'],'geometry_index_schema':SCHEMA,
            'contact_geometry_lookup':'NativeGeometryIndex.by_id/contact_pair; never legacy geom_names list indexing'})
    return {'schema_version':'corrected-entity-inventory-v2','original_inventory_modified':False,
        'legacy_geom_names_is_not_native_id_order':True,'records':records}
