"""Integrity, approval, privacy and repeatability of the actually approved version."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('freeze_tests',ROOT/'ai_tools/freeze_approved.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
PACKAGE=ROOT.parent
VERSIONS=sorted((ROOT/'approved_reference').glob('r1-reference-*'))


class FrozenReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(VERSIONS)!=1:raise unittest.SkipTest('Approved version is not installed')
        cls.out=VERSIONS[0]
        cls.manifest=json.loads((cls.out/'dataset_manifest.json').read_text())
        cls.rows=f.core.readcsv(cls.out/'final_decision_ledger.csv')

    def test_full_public_verifier(self):
        self.assertEqual(f.verify(self.out,PACKAGE)['approved'],90)

    def test_actual_approval_and_scope(self):
        metadata=json.loads((self.out/'approval_metadata.json').read_text())
        self.assertEqual(metadata,self.manifest['approval'])
        self.assertEqual(metadata['approval_date'],'2026-10-26')
        self.assertEqual(metadata['adjudicator_identity'],'Nikta Akbarpour')
        self.assertEqual(metadata['approval_ledger_sha256'],f.core.digest(self.out/'approval_ledger.csv'))
        self.assertFalse(metadata['independent_reannotation_claimed'])
        self.assertFalse(metadata['manual_inspection_of_every_event_claimed'])
        self.assertEqual(f.scope_check(PACKAGE,self.rows),self.manifest['scope_verification'])

    def test_originals_and_statistics_unchanged(self):
        self.assertEqual(f.core.digest(self.out/'original_agreement_statistics.json'),'2e5d45b6b9705ad8f75d4b3d0a053c4e438f5e82d394a3a077fae604e088a046')
        for name,h in self.manifest['source_file_sha256'].items():self.assertEqual(f.core.digest(PACKAGE/name),h)

    def test_original_reasoning_and_approved_labels_preserved(self):
        proposed={r['adjudication_id']:r for r in f.core.readcsv(ROOT/'ai_assisted_20261026/complete_adjudication_decisions.csv')}
        for row in self.rows:
            original=proposed[row['adjudication_id']]
            self.assertEqual(row['reasoning'],original['reasoning'])
            self.assertEqual(row['evidence_measurements_json'],original['evidence_measurements_json'])
            self.assertEqual(row['proposed_label_json'],original['proposed_label_json'])
            self.assertEqual(row['final_label_json'],original['proposed_label_json'])
            self.assertEqual(row['human_approval_status'],'approved')

    def test_uncertainty_is_not_a_negative_label(self):
        requests=[json.loads(r['final_label_json']) for r in self.rows if r['table']=='uncertainty_requests']
        self.assertEqual(collections.Counter(r['resolution_status'] for r in requests),{'partially_resolved':10,'resolved_existing_evidence':1})
        orange=next(r for r in self.rows if r['case_id']=='ORANGE-014-SUPPORT-GAP')
        self.assertEqual(json.loads(orange['final_label_json'])['fall_status'],'insufficient_information')

    def test_flat_table_bytes_equal_core_finalizer(self):
        private=ROOT/'versioned-reference'/self.out.name
        if not private.exists():self.skipTest('Private core export is local-only')
        for table in f.TABLES:self.assertEqual((private/f'adjudicated_{table}.csv').read_bytes(),(self.out/f'adjudicated_{table}.csv').read_bytes())

    def test_no_hidden_negative_coverage_expansion(self):
        row=next(r for r in self.rows if r['table']=='events' and r['episode']=='episode_014' and r['object_id']=='cream_cheese_1' and r['event_family']=='negative_review')
        self.assertEqual(json.loads(row['final_label_json'])['reviewed_intervals'],[[10,269],[286,530]])

    def test_producer_hashes_current(self):
        for path,h in self.manifest['script_sha256'].items():self.assertEqual(f.core.digest(ROOT/path),h)

    def test_tampering_and_unexpected_files_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'copy';shutil.copytree(self.out,out)
            (out/'unexpected.csv').write_text('not part of this version')
            with self.assertRaises(AssertionError):f.verify(out,PACKAGE)
            (out/'unexpected.csv').unlink()
            target=out/'adjudicated_events.csv';target.write_bytes(target.read_bytes()+b'\n')
            with self.assertRaises(AssertionError):f.verify(out,PACKAGE)

    def test_exact_reproduction(self):
        private=ROOT/'ai_private_20261026'
        if not private.exists():self.skipTest('Authorized private evidence/bridge required for freeze reproduction')
        with tempfile.TemporaryDirectory() as tmp:
            result=f.build(PACKAGE,ROOT/'ai_assisted_20261026',private,self.out/'approval_ledger.csv',self.out/'approval_metadata.json',Path(tmp)/'private',Path(tmp)/'public')
            self.assertEqual(result.name,self.out.name)
            self.assertEqual({p.name:p.read_bytes() for p in result.iterdir()},{p.name:p.read_bytes() for p in self.out.iterdir()})
            again=f.build(PACKAGE,ROOT/'ai_assisted_20261026',private,self.out/'approval_ledger.csv',self.out/'approval_metadata.json',Path(tmp)/'private',Path(tmp)/'public')
            self.assertEqual(again,result)

    def test_unsupported_label_change_rejected(self):
        if not (ROOT/'ai_private_20261026').exists():self.skipTest('Private bridge required')
        with tempfile.TemporaryDirectory() as tmp:
            rows=f.core.readcsv(self.out/'approval_ledger.csv');rows[0]['label_json']='{"support_label":"unsupported"}'
            import csv
            ledger=Path(tmp)/'ledger.csv'
            with ledger.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            metadata=json.loads((self.out/'approval_metadata.json').read_text());metadata['approval_ledger_sha256']=f.core.digest(ledger)
            meta=Path(tmp)/'metadata.json';meta.write_text(json.dumps(metadata))
            with self.assertRaises(AssertionError):f.build(PACKAGE,ROOT/'ai_assisted_20261026',ROOT/'ai_private_20261026',ledger,meta,Path(tmp)/'private',Path(tmp)/'public')
