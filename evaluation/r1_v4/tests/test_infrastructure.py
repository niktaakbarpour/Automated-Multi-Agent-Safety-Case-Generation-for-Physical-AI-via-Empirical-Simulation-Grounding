"""Analytical contracts and adversarial admission tests; no physics or simulation."""
import copy
import dataclasses
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluation.r1_v4.aggregate import aggregate
from evaluation.r1_v4.configuration import validate_configuration
from evaluation.r1_v4.contracts import (Applicability as A, Outcome as O, Coverage,
    ObjectAssessment, Truth as T, kleene_and, kleene_not)
from evaluation.r1_v4.fixtures import make_bundle, record, seal
from evaluation.r1_v4.manifest import builtins
from evaluation.r1_v4.provenance import canonical, digest, strict_loads, write_new
from evaluation.r1_v4.runtime import assess


class Infrastructure(unittest.TestCase):
    def setUp(self):
        self.b = make_bundle(('V', 'N', 'U'))

    def result(self, bundle=None, reseal=False):
        b = self.b if bundle is None else bundle
        return assess(seal(b) if reseal else b)

    def row(self, result, i=0):
        return result['object_assessments'][i]

    def outcome(self, bundle=None, reseal=False, i=0):
        return self.row(self.result(bundle, reseal), i)['outcome']

    def find(self, suffix, obj='object_00'):
        return next(r for r in self.b['evidence']['records'] if r['id'] == obj + '_' + suffix)

    def test_C05_three_object_violation(self):
        r = self.result()
        self.assertEqual(r['execution_outcome'], O.V.value)
        self.assertEqual([x['outcome'] for x in r['object_assessments']], [O.V.value, O.N.value, O.U.value])
        self.assertFalse(r['evidence_complete'])
        self.assertFalse(r['physical_safety_conclusion'])

    def test_C00_empty_scope(self):
        r = assess(make_bundle(()))
        self.assertEqual(r['object_assessments'], [])
        self.assertEqual(r['execution_outcome'], O.NA.value)
        self.assertTrue(r['empty_scope'])
        self.assertEqual(r['eligible_safety_units'], 0)
        self.assertIsNone(r['empirical_metrics'])

    def test_C01_C03_cardinalities(self):
        for n in (1, 3, 5, 17):
            with self.subTest(n=n):
                r = assess(make_bundle(('N',) * n))
                self.assertEqual(len(r['object_assessments']), n)
                self.assertEqual(r['execution_outcome'], O.N.value)
                self.assertTrue(r['evidence_complete'])

    def test_five_object_mixed(self):
        r = assess(make_bundle(('N', 'NA', 'U', 'ABSENT', 'IC')))
        self.assertEqual([o['outcome'] for o in r['object_assessments']], [O.N.value, O.NA.value, O.U.value, O.NA.value, O.IC.value])
        self.assertEqual(r['execution_outcome'], O.IC.value)
        self.assertEqual(r['study_eligibility'], 'pending_protocol_decision')

    def test_C06_input_permutation_stable_assessment(self):
        original = self.result()
        self.b['configuration']['protected_objects'].reverse()
        self.b['evidence']['records'].reverse()
        other = self.result(reseal=True)
        self.assertEqual(original['object_assessments'], other['object_assessments'])
        self.assertEqual(original['execution_outcome'], other['execution_outcome'])
        self.assertEqual(original['admitted_evidence_ids'], other['admitted_evidence_ids'])

    def invalid_config(self):
        r = self.result()
        self.assertEqual(r['configuration_status'], 'invalid')
        self.assertFalse(r['assessed'])
        self.assertIsNone(r['execution_outcome'])
        self.assertEqual(r['object_assessments'], [])

    def test_C07_duplicate_object(self):
        self.b['configuration']['protected_objects'].append('object_00'); self.invalid_config()

    def test_C07_duplicate_surface(self):
        self.b['configuration']['support_surfaces'].append(copy.deepcopy(self.b['configuration']['support_surfaces'][0])); self.invalid_config()

    def test_C07_missing_mapping(self):
        self.b['configuration']['object_surface_mapping'].pop('object_00'); self.invalid_config()

    def test_C07_dangling_mapping(self):
        self.b['configuration']['object_surface_mapping']['object_00'] = ['unknown']; self.invalid_config()

    def test_C07_empty_mapping(self):
        self.b['configuration']['object_surface_mapping']['object_00'] = []; self.invalid_config()

    def test_C07_role_collision(self):
        self.b['configuration']['support_surfaces'][0]['id'] = 'object_00'; self.invalid_config()

    def test_C08_reversed_interval(self):
        self.b['configuration']['monitoring_interval']['end']['value'] = -1; self.invalid_config()

    def test_C08_axis_mismatch(self):
        self.b['configuration']['monitoring_interval']['axis'] = 'simulator_time'; self.invalid_config()

    def test_C08_anchor_role(self):
        self.b['configuration']['monitoring_interval']['start'] = {'kind': 'terminal_recorded_snapshot', 'value': None}; self.invalid_config()

    def test_R16C01_unknown_property(self):
        self.b['configuration']['pass_override'] = True; self.invalid_config()

    def test_requirement_version(self):
        self.b['configuration']['requirement_version'] = '3.0.0'; self.invalid_config()

    def test_manifest_version(self):
        self.b['configuration']['assessment_manifest']['manifest_version'] = '2.0.0'; self.invalid_config()

    def test_R16C03_manifest_mismatch(self):
        self.b['configuration']['assessment_manifest']['adapter']['id'] = 'other'; self.invalid_config()

    def test_R16C02_wrong_checker_hash(self):
        self.b['configuration']['assessment_manifest']['checker']['sha256'] = '0' * 64
        self.assertEqual(self.outcome(), O.IC.value)
        self.assertTrue(self.result()['assessed'])

    def test_R16C02_wrong_evidence_schema_version(self):
        self.b['configuration']['assessment_manifest']['evidence_schema']['version'] = '2.0.0'
        self.assertEqual(self.outcome(), O.IC.value)

    def test_R16C02_unresolved_manifest(self):
        self.b['configuration']['assessment_manifest']['checker']['sha256'] = None
        self.assertEqual(self.outcome(), O.IC.value)

    def test_R16C03_scope_drift(self):
        self.b['artifacts']['synthetic:scope']['execution_id'] = 'other'
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_P01_source_tamper(self):
        self.b['artifacts']['synthetic:source']['records']['object_00_fall']['truth'] = 'U'
        self.assertEqual(self.outcome(), O.IC.value)

    def test_P01_record_tamper_without_source(self):
        self.find('fall')['payload']['loss'] = 'U'
        self.assertEqual(self.outcome(), O.IC.value)

    def test_no_input_directed_file_resolution(self):
        self.b['evidence']['records'][0]['source_ref'] = '/etc/passwd'
        r = self.result(reseal=True)
        self.assertNotIn('shared_context', r['admitted_evidence_ids'])
        self.assertIn('unresolved_hash_bound_artifact:/etc/passwd', str(r))

    def test_builtin_override(self):
        self.b['artifacts']['builtin:checker'] = {}
        self.assertEqual(self.outcome(), O.IC.value)

    def test_R16P01_empirical_never_admitted(self):
        for status in ('pending', 'capability_tested', 'empirically_validated'):
            with self.subTest(status=status):
                b = copy.deepcopy(self.b)
                b['configuration']['assessment_manifest'].update(purpose='empirical_assessment', validation_status=status)
                r = assess(b)
                self.assertEqual(r['execution_outcome'], O.IC.value)
                self.assertFalse(r['physical_safety_conclusion'])
                self.assertFalse(r['empirical_profiles_enabled'])

    def test_R16P01_legacy_never_empirical(self):
        self.b['configuration']['assessment_manifest']['purpose'] = 'legacy_comparison'
        self.assertEqual(self.outcome(), O.IC.value)

    def test_empirical_record_disguised_in_analytical_bundle(self):
        self.find('fall')['synthetic'] = False
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_A01_no_rearm(self):
        r = assess(make_bundle(('NA',)))
        self.assertEqual(self.row(r)['applicability'], A.NA.value)
        self.assertEqual(r['execution_outcome'], O.NA.value)

    def test_A03_verified_absent(self):
        b = make_bundle(('ABSENT',))
        b['configuration']['geometry_contract']['required_shape_capabilities'] = ['mesh']
        r = assess(b)
        self.assertEqual(r['execution_outcome'], O.NA.value)
        self.assertTrue(self.row(r)['scope_mismatch'])
        self.assertEqual(self.row(r)['study_eligibility'], 'pending_protocol_decision')

    def test_A03_missing_presence(self):
        self.b['evidence']['records'] = [r for r in self.b['evidence']['records'] if r['id'] != 'object_00_presence']
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_A03_incomplete_absence_roster(self):
        b = make_bundle(('ABSENT',)); b['artifacts']['synthetic:model']['complete_roster'] = False
        self.assertEqual(self.outcome(b, True), O.U.value)

    def test_R16P02_alias_collision(self):
        self.b['artifacts']['synthetic:model']['objects']['object_01'] = 'instance_object_00'
        r = self.result(reseal=True)
        self.assertEqual(self.row(r)['outcome'], O.IC.value)
        self.assertEqual(self.row(r, 1)['outcome'], O.IC.value)

    def test_A04_chain_cycle(self):
        self.find('support')['payload']['chain'] = ['object_00', 'object_00', 'root_A']
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_A04_uncertified_link(self):
        self.find('support')['dependencies'].remove('object_00_link')
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_A04_dependency_cycle(self):
        self.find('identity')['dependencies'].append('object_00_support')
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_A05_R16S01_dynamic_surface_scoped(self):
        b = make_bundle(('V', 'N'))
        b['configuration']['object_surface_mapping']['object_01'] = ['root_B']
        for r in b['evidence']['records']:
            if r['object_id'] == 'object_01':
                r['surfaces'] = ['root_B']
        b['artifacts']['synthetic:scope']['surfaces'] = copy.deepcopy(b['configuration']['object_surface_mapping'])
        b['configuration']['support_surfaces'][1]['motion_model'] = 'time_varying'
        r = self.result(b, True)
        self.assertEqual(self.row(r)['outcome'], O.V.value)
        self.assertEqual(self.row(r, 1)['outcome'], O.IC.value)
        self.assertEqual(r['execution_outcome'], O.V.value)

    def test_G01_unsupported_shape(self):
        self.b['configuration']['geometry_contract']['required_shape_capabilities'] = ['sphere']
        self.assertEqual(self.outcome(), O.IC.value)

    def test_G04_nonfinite_config(self):
        self.b['configuration']['monitoring_interval']['start']['value'] = float('nan'); self.invalid_config()

    def test_G04_nonfinite_evidence(self):
        self.find('geometry')['payload']['dimensions'][0] = float('nan')
        self.assertEqual(self.outcome(), O.IC.value)

    def test_G04_clock_mismatch(self):
        self.find('fall')['frame']['clock'] = 'other'
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_G04_units_mismatch(self):
        self.find('geometry')['frame']['length_unit'] = 'cm'
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_S01_R16S01_multiple_roots(self):
        r = assess(make_bundle(('N', 'N', 'N'), True))
        self.assertEqual(r['execution_outcome'], O.N.value)
        self.assertEqual(self.row(r)['surfaces'], ['root_A', 'root_B'])

    def test_S01_wrong_root(self):
        self.find('support')['payload']['chain'][-1] = 'root_B'
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_R16S02_scope_suffix_blocks_negative(self):
        b = make_bundle(('N',))
        b['evidence']['records'].append(record(b['configuration'], 'replacement', 'object_00', 'scope_boundary', interval=[1, 2], payload={'reason': 'instance_replacement'}))
        self.assertEqual(self.outcome(b, True), O.U.value)

    def test_F06_R16S02_scope_suffix_preserves_prior_positive(self):
        self.b['evidence']['records'].append(record(self.b['configuration'], 'replacement', 'object_00', 'scope_boundary', interval=[2, 2], payload={'reason': 're-placement'}))
        self.assertEqual(self.outcome(reseal=True), O.V.value)

    def test_F01_all_positive_predicates_required(self):
        for predicate in ('origin', 'loss', 'downward', 'handling_excluded'):
            with self.subTest(predicate=predicate):
                b = copy.deepcopy(self.b)
                next(r for r in b['evidence']['records'] if r['id'] == 'object_00_fall')['payload'][predicate] = 'U'
                self.assertEqual(self.outcome(b, True), O.U.value)

    def test_F04_established_handling_exclusion(self):
        self.find('fall')['payload']['handling_excluded'] = 'T'
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_F08_R16F01_censored_onset(self):
        self.find('fall')['payload']['onset'] = [-1, 1]
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_F09_terminal_censored_downward(self):
        self.find('fall')['payload']['downward_interval'] = [2, 3]
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_R16E01_same_event_contradiction(self):
        c = self.b['configuration']
        self.b['evidence']['records'].append(record(c, 'contradiction', 'object_00', 'static_negative', dependencies=['object_00_support'], interval=[0, 2], cells=['s0', 's1', 's2', 't01', 't12'], payload={'method': 'exact_static_constraint'}))
        r = self.result(reseal=True)
        self.assertEqual(self.row(r)['outcome'], O.U.value)
        self.assertTrue(r['conflicts'])
        self.assertNotIn('object_00_fall', r['admitted_evidence_ids'])

    def test_R16E01_contradictory_support(self):
        opposite = copy.deepcopy(self.find('support'))
        opposite.update(id='opposite_support', truth='F')
        opposite['payload']['all_support_excluded'] = True
        self.b['evidence']['records'].append(opposite)
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_R16E02_invalid_shared_foundation(self):
        self.b['evidence']['records'][0]['validity'] = 'invalid_contract'
        r = self.result(reseal=True)
        self.assertEqual(r['execution_outcome'], O.IC.value)
        self.assertEqual(r['admitted_evidence_ids'].count('object_00_fall'), 0)

    def test_R16E02_unrelated_invalid_optional_camera(self):
        self.b['evidence']['records'].append(record(self.b['configuration'], 'optional_camera', 'object_00', 'observation',
            kind='camera', validity='invalid_local', payload={'camera_id': 'cam', 'indices': [], 'decoded': [], 'inspected': []}))
        r = self.result(reseal=True)
        self.assertEqual(self.row(r)['outcome'], O.V.value)
        self.assertFalse(r['evidence_complete'])

    def test_invalid_optional_negative_coverage_remains_qualified(self):
        b = make_bundle(('N',))
        b['evidence']['records'].append(record(b['configuration'], 'optional_contact', 'object_00', 'observation',
            kind='contact', validity='invalid_local', payload={'pairs': [], 'complete': False, 'forces': None}))
        self.assertEqual(self.outcome(b, True), O.N.value)

    def test_dependency_on_missing_camera_blocks_positive(self):
        self.find('fall')['dependencies'].append('missing_camera')
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_T02_T04_unknown_phase(self):
        self.find('fall')['uncertainty']['temporal'] = None
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_T02_nonzero_phase_abstains(self):
        self.find('fall')['uncertainty']['temporal'] = 1
        self.assertEqual(self.outcome(reseal=True), O.U.value)

    def test_T01_recorded_anchors(self):
        c = self.b['configuration']
        c['monitoring_interval']['start'] = {'kind': 'recorded_first_policy_boundary', 'value': None}
        c['monitoring_interval']['end'] = {'kind': 'terminal_recorded_snapshot', 'value': None}
        self.assertEqual(self.outcome(), O.V.value)

    def test_T01_anchor_mismatch(self):
        self.b['artifacts']['synthetic:domain']['start'] = 1
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_O01_R16N01_gap(self):
        b = make_bundle(('N',))
        next(r for r in b['evidence']['records'] if r['claim'] == 'static_negative')['cells'].remove('t01')
        r = self.result(b, True)
        self.assertEqual(self.row(r)['outcome'], O.U.value)
        self.assertEqual(self.row(r)['coverage']['missing'], ['t01'])

    def test_R16N01_no_interval_union_invents_cells(self):
        b = make_bundle(('N',))
        clear = next(r for r in b['evidence']['records'] if r['claim'] == 'static_negative')
        clear['cells'] = ['s0', 's2']
        self.assertEqual(self.outcome(b, True), O.U.value)

    def test_R16N01_overlap_not_independence(self):
        b = make_bundle(('N',))
        clear = copy.deepcopy(next(r for r in b['evidence']['records'] if r['claim'] == 'static_negative'))
        clear['id'] = 'copy_clear'; b['evidence']['records'].append(clear)
        r = self.result(b, True)
        self.assertEqual(self.row(r)['outcome'], O.N.value)
        self.assertEqual(len(self.row(r)['coverage']['negative']), 5)
        self.assertEqual(len(self.row(r)['coverage']['source_groups']), 1)

    def test_R16N02_handling_composition(self):
        b = make_bundle(('N',))
        next(r for r in b['evidence']['records'] if r['claim'] == 'static_negative')['payload']['method'] = 'carry_phase_union'
        self.assertEqual(self.outcome(b, True), O.U.value)

    def test_A02_F03_raw_contact_or_height_not_a_witness(self):
        b = make_bundle(('U',))
        for kind, payload in [('contact', {'pairs': [['object_00', 'root_A']], 'complete': True, 'forces': None}),
                              ('direct_measurement', {'quantity': 'height', 'values': [1, 0], 'unit': 'm'})]:
            b['evidence']['records'].append(record(b['configuration'], kind, 'object_00', 'observation', kind=kind, payload=payload))
        self.assertEqual(self.outcome(b, True), O.U.value)

    def test_raw_contact_claim_cannot_masquerade_as_fall(self):
        r = self.find('fall'); r['kind'] = 'contact'
        r['payload'] = {'pairs': [], 'complete': True, 'forces': None}
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_N01_N02_no_numeric_calibration_enabled(self):
        n = self.b['configuration']['fall_detection_rules']['numeric_policy']
        n.update(persistence_window_s=1, calibration_ref='asserted:calibration')
        self.assertEqual(self.outcome(), O.IC.value)

    def test_P01_duplicate_evidence(self):
        self.b['evidence']['records'].append(copy.deepcopy(self.find('fall')))
        self.assertEqual(self.outcome(reseal=True), O.IC.value)

    def test_schema_version_evidence(self):
        self.b['evidence']['evidence_version'] = '2.0.0'
        self.assertEqual(self.outcome(), O.IC.value)

    def test_stable_serialization_hash(self):
        self.assertEqual(canonical(self.result()), canonical(self.result()))
        self.assertEqual(digest({'a': 1, 'b': 2}), digest({'b': 2, 'a': 1}))
        r = self.result(); h = r.pop('assessment_hash')
        self.assertEqual(h, digest(r))

    def test_strict_json(self):
        for text in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError): strict_loads(text)

    def test_cli_output_and_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as root:
            source, output = Path(root)/'input.json', Path(root)/'assessment.json'
            write_new(source, make_bundle(('V', 'N', 'NA')))
            cmd = [sys.executable, '-m', 'evaluation.r1_v4', '--input', str(source), '--output', str(output)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = output.read_bytes()
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
            self.assertEqual(before, output.read_bytes())

    def test_kleene_uncertainty(self):
        self.assertEqual(kleene_and(T.TRUE, T.UNKNOWN), T.UNKNOWN)
        self.assertEqual(kleene_and(T.FALSE, T.UNKNOWN), T.FALSE)
        self.assertEqual(kleene_not(T.UNKNOWN), T.UNKNOWN)


class AggregateTruthTable(unittest.TestCase):
    def make(self, object_id, outcome):
        applicability = {O.NA: A.NA, O.U: A.UNKNOWN, O.IC: A.IC}.get(outcome, A.APPLICABLE)
        coverage = Coverage(('s0',), (), (), ('s0',) if outcome == O.N else (), () if outcome == O.N else ('s0',), (), ())
        return ObjectAssessment(object_id, ('root',), applicability, outcome, (), ('synthetic-witness',), coverage, (), outcome in (O.N, O.NA))

    def test_O04_R16A01_mixed_table_and_permutations(self):
        table = [([], O.NA), ([O.NA, O.NA], O.NA), ([O.N, O.NA], O.N), ([O.N, O.U], O.U),
                 ([O.N, O.IC], O.IC), ([O.U, O.IC], O.IC), ([O.V, O.NA], O.V),
                 ([O.V, O.U], O.V), ([O.V, O.IC], O.V), ([O.V, O.N, O.IC, O.U, O.NA], O.V)]
        for values, expected in table:
            for permutation in set(itertools.permutations(values)):
                rows = [self.make(str(i), o) for i, o in enumerate(permutation)]
                self.assertEqual(aggregate(rows)['execution_outcome'], expected.value)
                self.assertEqual(sum(aggregate(rows)['outcome_counts'].values()), len(rows))

    def test_duplicate_rows_rejected(self):
        r = self.make('object', O.N)
        with self.assertRaises(ValueError): aggregate([r, r])

    def test_unqualified_negative_rejected(self):
        r = self.make('object', O.N)
        with self.assertRaises(ValueError): aggregate([dataclasses.replace(r, applicability=A.UNKNOWN)])


if __name__ == '__main__':
    unittest.main()
