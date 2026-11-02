"""Replay three synthetic bundles through the actual CLI into a new directory."""
import argparse
from pathlib import Path
import socket
import subprocess
import sys
import jsonschema
from .configuration import HERE, REPO
from .provenance import load, write_new, bytes_digest, canonical
from .runtime import assess

def main(argv=None):
    assert socket.gethostname().lower()=='hestia'
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixtures-dir',type=Path,default=HERE/'synthetic')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    expected={'three_object_violation':'violation_observed','five_object_uncertain':'invalid_measurement_contract',
              'multiple_static_surfaces':'no_violation_observed_within_validated_coverage'}
    summaries=[]
    for name,outcome in expected.items():
        source=args.fixtures_dir/(name+'.json');target=args.output_dir/(name+'.json')
        command=[sys.executable,'-m','evaluation.r1_v4','--input',str(source),'--output',str(target)]
        p=subprocess.run(command,cwd=REPO,capture_output=True,text=True)
        if p.returncode not in (0,1):raise RuntimeError(p.stderr)
        result=load(target)
        jsonschema.Draft202012Validator(load(HERE/'assessment.schema.json')).validate(result)
        assert result['execution_outcome']==outcome
        assert result['synthetic'] and result['physical_safety_conclusion'] is False
        assert target.read_bytes()==canonical(assess(load(source)))+b'\n','CLI/library replay mismatch'
        summaries.append({'name':name,'synthetic':True,'execution_outcome':outcome,
            'object_outcomes':[o['outcome'] for o in result['object_assessments']],
            'applicability':[o['applicability'] for o in result['object_assessments']],
            'complete':result['evidence_complete'],'admitted_evidence_count':len(result['admitted_evidence_ids']),
            'cli_exit_code':p.returncode,'assessment_hash':result['assessment_hash'],
            'output_sha256':bytes_digest(target.read_bytes()),'input_sha256':bytes_digest(source.read_bytes()),
            'byte_identical_cli_library_replay':True,'command':command})
    write_new(args.output_dir/'SUMMARY.json',{'synthetic_only':True,'empirical_effectiveness_claim':False,'demonstrations':summaries})
    print('\n'.join(x['name']+': '+x['execution_outcome'] for x in summaries))
if __name__=='__main__':main()
