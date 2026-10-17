"""Copy small evidence sources, with explicit historical-identity qualifications."""
import argparse,json,hashlib,shutil
from pathlib import Path
from targeted_investigation import load,save,sha

def main(project,out):
    project=Path(project);out=Path(out);dest=out/'source_evidence';dest.mkdir(exist_ok=True)
    parent=project/'reports/fall_review_20261016/source_evidence';base=Path('/local/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages')
    ep=Path('/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero/long/task_00/episode_000');meta=load(ep/'metadata.json');ev=load(ep/'evaluator_version.json');records=[]
    for n in ['run_oft.py','recording_base.py','semantic_scene.py']:
        p=parent/n;shutil.copy2(p,dest/n);h=sha(p);assert h==meta['source_files_sha256'][n];records.append({'copy':n,'source':str(p),'sha256':h,'historical_identity':'producer_sha256_matches'})
    for rel in ['libero/libero/envs/bddl_base_domain.py','libero/libero/envs/env_wrapper.py','libero/libero/envs/arenas/living_room_arena.py','libero/libero/envs/problems/libero_living_room_tabletop_manipulation.py','robosuite/environments/base.py','robosuite/environments/robot_env.py','robosuite/utils/observables.py','robosuite/utils/binding_utils.py','robosuite/macros.py']:
        p=base/rel;n=rel.replace('/','__');shutil.copy2(p,dest/n);h=sha(p);expected=ev['implementation_files_sha256'].get(str(p))
        if expected is not None:assert h==expected
        records.append({'copy':n,'source':str(p),'sha256':h,'producer_expected_sha256':expected,'historical_identity':'producer_sha256_matches' if expected is not None else 'current_dependency_only_historical_hash_absent'})
    shutil.copy2(ep/'simulator.xml',dest/'simulator.xml');shutil.copy2(ep/'evaluator_version.json',dest/'evaluator_version.json')
    save(out/'source_provenance.json',records)
    save(out/'external_source_references.json',{'version_matched_upstream_not_historical_binary_attestation':True,'sources':[{'url':'https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/src/engine/engine_forward.c','relevant_lines':'128–158 (kinematics/collision); 2018–2051 (forward dynamics before Euler integration)','purpose':'Interpret update ordering of the version declared by the producer; observed algebra is checked independently against recorded excerpts.'},{'url':'https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/src/xml/xml_native_writer.cc','purpose':'Versioned XML writer reference; six-digit precision explanation is established numerically by runtime-relative quaternions versus saved XML tokens.'}]})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);a=p.parse_args();main(a.project,a.output)
