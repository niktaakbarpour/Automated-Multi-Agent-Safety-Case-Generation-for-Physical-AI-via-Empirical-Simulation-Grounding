"""Portable checks of submitted reviews/public proposals; no private evidence needed."""
import collections
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools'


def module(name):
    spec=importlib.util.spec_from_file_location(name,TOOLS/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


p=module('publish_proposal');core=module('adjudicate')
PACKAGE=TOOLS.parents[1]
PUBLICATION=PACKAGE/'adjudication/publication_20261026'


class Publication(unittest.TestCase):
    def copy_publication(self):
        temp=tempfile.TemporaryDirectory(prefix='r1-publication-test-');self.addCleanup(temp.cleanup)
        out=Path(temp.name)/'public';shutil.copytree(PUBLICATION,out);return out

    def rechecksum(self,out,name):
        path=out/'publication_checksums.json';sums=json.loads(path.read_text());sums[name]=p.sha(out/name);p.writejson(path,sums)

    def test_public_verification(self):
        result=p.verify(PACKAGE,PUBLICATION)
        self.assertEqual(result['pending_decisions'],90)
        self.assertFalse(result['scientific_evidence_revalidated'])

    def test_comparison_recomputed_without_private_evidence(self):
        data,_,scope,runs,byrun=core.load_sources(PACKAGE)
        expected=[(r['run_id'],o) for r in runs for o in scope['protected_objects']]
        units=core.build_alignment(data,expected,byrun)
        paired=[u for u in units if u['reviewer_1_rows'] and u['reviewer_2_rows'] and u['table']!='uncertainty_requests']
        agreements=[u for u in paired if u['classification'].endswith('_agreement')]
        diffs=[u for u in units if not u['classification'].endswith('_agreement') and u['table']!='uncertainty_requests']
        self.assertEqual((len(units),len(paired),len(agreements),len(diffs)),(90,66,41,38))
        self.assertEqual(sum(map(len,data.values())),160)

    def test_no_private_paths_or_secret_patterns(self):
        for path in PUBLICATION.iterdir():p.scan(path.read_text())

    def test_private_path_detection(self):
        with self.assertRaisesRegex(AssertionError,'private absolute'):
            p.scan('/'+'Users'+'/example/private-recording')

    def test_credential_pattern_detection(self):
        with self.assertRaisesRegex(AssertionError,'credential-shaped'):
            p.scan('gh'+'p_'+'a'*30)

    def test_scientific_artifact_hashes_preserved(self):
        manifest=json.loads((PUBLICATION/'dataset_manifest.json').read_text())
        for name in p.COPY_FILES:
            self.assertEqual(p.sha(PUBLICATION/name),manifest['original_proposal_artifact_sha256'][name])

    def test_modified_csv_rejected(self):
        out=self.copy_publication()
        with (out/'adjudication_decisions.csv').open('a') as f:f.write('\n')
        with self.assertRaisesRegex(AssertionError,'checksum mismatch'):p.verify(PACKAGE,out)

    def test_approved_status_rejected_even_with_new_checksums(self):
        out=self.copy_publication();path=out/'dataset_manifest.json';value=json.loads(path.read_text())
        value['status']='approved';p.writejson(path,value);self.rechecksum(out,path.name)
        with self.assertRaises(AssertionError):p.verify(PACKAGE,out)

    def test_private_evidence_cannot_be_undeclared(self):
        out=self.copy_publication();path=out/'dataset_manifest.json';value=json.loads(path.read_text())
        value['private_evidence_references']={};p.writejson(path,value);self.rechecksum(out,path.name)
        with self.assertRaisesRegex(AssertionError,'undeclared private evidence'):p.verify(PACKAGE,out)

    def test_binary_payload_rejected(self):
        out=self.copy_publication();(out/'extra.png').write_bytes(b'not-published')
        with self.assertRaisesRegex(AssertionError,'unexpected binary'):p.verify(PACKAGE,out)

    def test_public_snapshot_cannot_finalize(self):
        with tempfile.TemporaryDirectory(prefix='r1-no-public-freeze-') as temp:
            output=Path(temp)/'frozen'
            with self.assertRaises((AssertionError,FileNotFoundError)):
                core.finalize(PACKAGE,PUBLICATION,PUBLICATION/'approval_template.csv',output)
            self.assertFalse(output.exists())

    @unittest.skipUnless(os.environ.get('R1_PUBLIC_ONLY_TESTS')!='1' and (PACKAGE/'adjudication/proposed_20261026/proposal_checksums.json').exists(),'Private proposal is not published; public verification remains available.')
    def test_publication_transformation_reproducible(self):
        with tempfile.TemporaryDirectory(prefix='r1-publication-reproduction-') as temp:
            out=Path(temp)/'public'
            p.build(PACKAGE,PACKAGE/'adjudication/proposed_20261026',out)
            for path in PUBLICATION.iterdir():self.assertEqual(path.read_bytes(),(out/path.name).read_bytes(),path.name)


if __name__=='__main__':unittest.main()
