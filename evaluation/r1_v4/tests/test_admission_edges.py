import copy
import dataclasses
import itertools
import unittest
from evaluation.r1_v4.contracts import Outcome as O
from evaluation.r1_v4.fixtures import make_bundle, record, seal
from evaluation.r1_v4.runtime import assess
import test_infrastructure as base_tests

class AdmissionEdges(unittest.TestCase):
    def setUp(self):
        self.b=make_bundle(('V','N'))
    def row(self):
        return assess(seal(self.b))['object_assessments'][0]
    def find(self, suffix):
        return next(r for r in self.b['evidence']['records'] if r['id']=='object_00_'+suffix)
    def test_malformed_optional_camera_is_local(self):
        self.b['evidence']['records'].append(record(self.b['configuration'],'bad_camera','object_00','observation',kind='camera',payload={'broken':True}))
        self.assertEqual(self.row()['outcome'],O.V.value)
    def test_malformed_essential_camera_propagates_unknown(self):
        self.b['evidence']['records'].append(record(self.b['configuration'],'bad_camera','object_00','observation',kind='camera',payload={'broken':True}))
        self.find('fall')['dependencies'].append('bad_camera')
        self.assertEqual(self.row()['outcome'],O.U.value)
    def test_raw_contact_has_no_support_exemption(self):
        self.find('fall')['dependencies'].append('touch')
        self.b['evidence']['records'].append(record(self.b['configuration'],'touch','object_00','observation',kind='contact',payload={'pairs':[['object_00','robot']], 'complete':True,'forces':None}))
        self.assertEqual(self.row()['outcome'],O.V.value)
    def test_single_frame_cannot_be_fall(self):
        self.find('fall')['payload']['downward_interval']=[1,1]
        self.assertEqual(self.row()['outcome'],O.U.value)
    def test_downward_cannot_precede_departure(self):
        self.find('fall')['payload'].update(onset=[2,2],downward_interval=[1,2])
        self.assertEqual(self.row()['outcome'],O.U.value)
    def test_unknown_config_phase_not_overridden(self):
        self.b['configuration']['temporal_alignment']['state_phase_uncertainty_s']=None
        self.assertEqual(self.row()['outcome'],O.U.value)
    def test_uncertainty_description_retained(self):
        self.find('fall')['uncertainty']['description']=['identity continuity unresolved']
        row=self.row()
        self.assertEqual(row['outcome'],O.U.value)
        self.assertTrue(row['uncertainty'])
    def test_incomplete_roster_does_not_block_known_present(self):
        self.b['artifacts']['synthetic:model']['complete_roster']=False
        self.assertEqual(self.row()['outcome'],O.V.value)
    def test_uncertain_scope_boundary_blocks_full_negative(self):
        self.b=make_bundle(('N',))
        boundary=record(self.b['configuration'],'boundary','object_00','scope_boundary',interval=[1,2],payload={'reason':'uncertain re-placement'})
        boundary['uncertainty']['temporal']=None
        self.b['evidence']['records'].append(boundary)
        self.assertEqual(self.row()['outcome'],O.U.value)
    def test_domain_cannot_omit_join(self):
        self.b['artifacts']['synthetic:domain']['cells']=[c for c in self.b['artifacts']['synthetic:domain']['cells'] if c['id']!='t01']
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_domain_cannot_relabel_clock(self):
        self.b['artifacts']['synthetic:domain']['axis']='simulator_time'
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_nonhorizontal_support_unsupported(self):
        self.b['artifacts']['synthetic:model']['surfaces']['root_A']['horizontal']=False
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_continuous_projection_unsupported(self):
        c=self.b['configuration']; c['temporal_alignment']['domain']='validated_continuous'
        c['assessment_manifest']['requested_domain']['projection']='validated_continuous'
        self.b['artifacts']['synthetic:scope']['projection']='validated_continuous'
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_cross_object_dependency_rejected(self):
        self.find('fall')['dependencies'].append('object_01_identity')
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_multiple_parent_solving_deferred(self):
        parent=record(self.b['configuration'],'second_parent','object_00','support_link',payload={'child':'object_00','parent':'root_B'})
        self.b['evidence']['records'].append(parent)
        self.find('support')['dependencies'].append('second_parent')
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_explicit_single_parent_indirect_constraints(self):
        chain=['object_00','pedestal','root_A']
        self.find('support')['payload']['chain']=chain
        self.find('support')['dependencies'].remove('object_00_link')
        for i,(child,parent) in enumerate(zip(chain,chain[1:])):
            rid='link_'+str(i)
            self.b['evidence']['records'].append(record(self.b['configuration'],rid,'object_00','support_link',payload={'child':child,'parent':parent}))
            self.find('support')['dependencies'].append(rid)
        self.assertEqual(self.row()['outcome'],O.V.value)
    def test_explicit_shared_foundation_conflict(self):
        other=copy.deepcopy(self.b['evidence']['records'][0]); other['id']='opposite_context'
        self.b['evidence']['records'].append(other)
        self.b['evidence']['conflicts'].append({'left':'shared_context','right':'opposite_context','reason':'declared incompatible transform contexts'})
        result=assess(seal(self.b))
        self.assertEqual(result['execution_outcome'],O.U.value)
        self.assertTrue(result['conflicts'])
    def test_all_3906_outcome_vectors_are_order_invariant(self):
        helper=base_tests.AggregateTruthTable()
        from evaluation.r1_v4.aggregate import aggregate
        count=0
        for n in range(6):
            for values in itertools.product(tuple(O),repeat=n):
                rows=[helper.make(str(i),v) for i,v in enumerate(values)]
                a,b=aggregate(rows),aggregate(reversed(rows))
                self.assertEqual(a,b)
                if O.V in values:self.assertEqual(a['execution_outcome'],O.V.value)
                self.assertEqual(sum(a['outcome_counts'].values()),n)
                count+=1
        self.assertEqual(count,3906)
    def test_missing_expected_source_is_unknown(self):
        self.b['artifacts'].pop('synthetic:source')
        result=assess(self.b)
        self.assertEqual(result['execution_outcome'],O.U.value)
        self.assertTrue(any('missing_observation_artifact' in str(r) for r in result['rejected_evidence']))
    def test_output_schema_and_versions(self):
        import jsonschema
        from evaluation.r1_v4.configuration import HERE
        from evaluation.r1_v4.provenance import load
        schema=load(HERE/'assessment.schema.json')
        jsonschema.Draft202012Validator.check_schema(schema)
        result=assess(self.b)
        jsonschema.validate(result,schema)
        self.assertEqual(result['object_assessments'][0]['execution_id'],'synthetic-execution')
        self.b['configuration']['requirement_version']='wrong'
        jsonschema.validate(assess(self.b),schema)
    def test_missing_negative_cells_distinct_from_unobserved(self):
        b=make_bundle(('V',))
        row=assess(b)['object_assessments'][0]
        self.assertEqual(row['coverage']['unobserved'],['s0','t01'])
        self.assertEqual(len(row['coverage']['missing']),5)
    def test_declaration_cannot_fake_validated_geometry(self):
        r=self.find('geometry');r['kind']='declaration';r['payload']={}
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_absence_does_not_override_incompatible_presence_foundation(self):
        b=make_bundle(('ABSENT',))
        b['evidence']['records'].append(record(b['configuration'],'incompatible_presence','object_00','presence',payload={'closed_roster':True}))
        self.assertEqual(assess(seal(b))['execution_outcome'],O.IC.value)
    def test_unadmitted_negative_cannot_poison_independent_positive(self):
        self.b['evidence']['records'].append(record(self.b['configuration'],'bad_clear','object_00','static_negative',
            dependencies=['object_00_support','invalid_optional_camera'],interval=[0,2],
            cells=['s0','s1','s2','t01','t12'],payload={'method':'exact_static_constraint'}))
        self.b['evidence']['records'].append(record(self.b['configuration'],'invalid_optional_camera','object_00','observation',
            kind='camera',validity='invalid_local',payload={'camera_id':'cam','indices':[],'decoded':[],'inspected':[]}))
        self.assertEqual(self.row()['outcome'],O.V.value)
    def test_unresolved_geometry_or_frame_reference_not_ignored(self):
        for field in ('geometry_ref','frame_ref'):
            b=make_bundle(('V',))
            b['configuration']['support_surfaces'][0][field]='unresolved:reference'
            self.assertEqual(assess(b)['execution_outcome'],O.IC.value)
    def test_unresolved_gravity_profile_not_ignored(self):
        self.b['configuration']['coordinate_frames']['gravity_direction_ref']='unresolved:gravity'
        self.assertEqual(self.row()['outcome'],O.IC.value)
    def test_unbound_clock_not_ignored(self):
        self.b['configuration']['temporal_alignment']['clock_ref']='unresolved:clock'
        self.assertEqual(self.row()['outcome'],O.IC.value)
