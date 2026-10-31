"""Local delivery/provenance checks, not a rerun of research scoring."""
import csv
import hashlib
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
ROOT = HERE / 'preserved_evidence'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


class ImportedReports(unittest.TestCase):
    def test_all_23_imported_bytes_match_hestia(self):
        transfer = load(ROOT/'TRANSFER_SHA256.json')
        self.assertEqual(len(transfer['files']), 23)
        self.assertFalse(transfer['original_evidence_included'])
        for name, digest in transfer['files'].items():
            self.assertEqual(sha(ROOT/name), digest, name)

    def test_both_seals_and_report_manifest(self):
        for directory, name in [('assessment','AI_EVALUATOR_3_SEAL.json'),
                                ('comparison','AI_REFERENCE_SEAL.json')]:
            seal = load(ROOT/directory/name)
            for member, digest in seal['files'].items():
                self.assertEqual(sha(ROOT/directory/member), digest, member)
        for member, digest in load(ROOT/'reports/REPORT_SHA256.json').items():
            self.assertEqual(sha(ROOT/'reports'/member), digest)
        self.assertFalse(load(ROOT/'comparison/AI_REFERENCE_SEAL.json')['human_approval'])

    def test_case_identity_completeness(self):
        expected = {f'NV{i:02d}' for i in range(1,21)}
        for name in ['assessment/AI_EVALUATOR_3_DECISIONS.csv',
                     'assessment/EVIDENCE_SUFFICIENCY.csv',
                     'comparison/AI_ADJUDICATED_REFERENCE.csv',
                     'comparison/THREE_EVALUATOR_COMPARISON.csv']:
            rr = rows(ROOT/name)
            self.assertEqual(len(rr),20)
            self.assertEqual({r['case_id'] for r in rr},expected)
        self.assertEqual({r['case_id'] for r in rows(ROOT/'comparison/UNRESOLVED_CASES.csv')},
                         {'NV06','NV12','NV16'})

    def test_all_original_uncertainty_fields_preserved(self):
        original = load(ROOT/'comparison/ORIGINAL_UNCERTAINTIES.json')
        self.assertEqual({k:len(v) for k,v in original.items()},{'1':23,'2':5})
        for n in ['1','2']:
            p = REPO/f'evaluation/r1_v3_ai_assisted_reviews_20261029/ai_evaluator_{n}/annotations/uncertainty_requests.csv'
            self.assertEqual(original[n],rows(p))

    def test_human_scoring_protected_files_unchanged(self):
        live = load(ROOT/'LIVE_SOURCE_VERIFICATION.json')
        self.assertTrue(live['passed'])
        self.assertEqual(live['export_files_live_matches'],23)
        self.assertEqual(len(live['protected_files']),8)
        original = REPO/'evaluation/r1_v3_human_validation_20'
        self.assertEqual(live['protected_files'],load(original/'SCORING_FREEZE.json')['files'])
        for name, digest in live['protected_files'].items():
            self.assertEqual(sha(original/name),digest,name)

    def test_frozen_prediction_hash_binding(self):
        expected = '0ef93ece9c3d0cb02a49a450979315a4e3be3d5f127aa48105970321f5b34984'
        score = load(ROOT/'comparison/EXPLORATORY_V3_SCORES.json')
        self.assertEqual(score['prediction_sha256'],expected)
        self.assertEqual(load(ROOT/'LIVE_SOURCE_VERIFICATION.json')['prediction_sha256'],expected)
        seal = load(REPO/'evaluation/r1_v3_generalization/execution/PREDICTION_SEAL.json')
        self.assertEqual(seal['files']['predictions.json'],expected)

    def test_seal_chain_and_disclosed_limits(self):
        score = load(ROOT/'comparison/EXPLORATORY_V3_SCORES.json')
        self.assertEqual(score['reference_seal_sha256'],sha(ROOT/'comparison/AI_REFERENCE_SEAL.json'))
        refseal = load(ROOT/'comparison/AI_REFERENCE_SEAL.json')
        self.assertEqual(refseal['assessment_seal_sha256'],sha(ROOT/'assessment/AI_EVALUATOR_3_SEAL.json'))
        self.assertFalse(refseal['prediction_inputs_used'])
        provenance = load(ROOT/'assessment/PROVENANCE.json')
        self.assertFalse(provenance['fresh_context_blinded'])
        self.assertTrue(provenance['prior_conversation_exposure'])
        self.assertFalse(provenance['human_validation'])

    def test_reported_denominators_and_undefined_metrics(self):
        score = load(ROOT/'comparison/EXPLORATORY_V3_SCORES.json')
        overall = score['overall']
        self.assertEqual(overall['units'],20)
        self.assertEqual(overall['reference_determinate']+overall['reference_unresolved'],20)
        self.assertEqual(overall['reference_unresolved'],3)
        self.assertEqual(overall['eligible_applicable'],5)
        self.assertEqual(overall['binary_compared'],4)
        self.assertEqual(overall['operational_abstentions'],1)
        self.assertEqual(sum(overall['binary_confusion'].values()),overall['binary_compared'])
        self.assertEqual(overall['reference_positive_R1_cases'],0)
        self.assertIsNone(overall['positive_recall'])
        self.assertIsNone(overall['positive_F1'])
        self.assertIsNone(overall['precision'])


if __name__ == '__main__':
    unittest.main()
