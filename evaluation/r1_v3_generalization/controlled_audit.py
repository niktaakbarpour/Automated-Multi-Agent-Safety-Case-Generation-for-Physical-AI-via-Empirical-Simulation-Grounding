"""Controlled logic probes, NOT independently labelled empirical examples."""
import importlib.util
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
V3=HERE.parent/'r1_v3'
sys.path.insert(0,str(V3))
from r1_checker import evaluate,initial_support
spec=importlib.util.spec_from_file_location('frozen_v3_fixture_helpers',V3/'tests/test_checker.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def probes():
    results=[]
    # A supported object with a tiny represented motion is not invariant under
    # the exact-rest policy; this tests conservatism, not physical truth.
    fs=f.series();moved=fs[11]['objects']['object']
    for vertex in moved['vertices']:vertex[0]+=1e-10
    moved['pose']=[x for vertex in moved['vertices'] for x in vertex]
    for bound in moved['bounds']:bound[0]+=1e-10
    p=initial_support(fs,'object',f.CONFIG)
    results.append(dict(case='tiny_represented_pose_change',change_m=1e-10,applicability=p['applicability'],reason=p['reason'],interpretation='Conservative exact-rest sensitivity; not an empirical misclassification count.'))
    # Requirement applicability is established absent at 10. Later table support
    # does not make an initially unsupported object an R1-applicable unit.
    fs=[f.frame(i,2.-i*.01,None) for i in range(12)]
    fs += [f.frame(12),f.frame(13),f.frame(14,1.5,None),f.frame(15,1.4,None),f.frame(16,1.3,None)]
    p=evaluate(fs,'object','controlled-absent-then-placed',f.CONFIG)
    contradictions=[dict(type=e['type'],scope=e['scope'],interval=e['interval']) for e in p['events'] if e['type']=='r1_fall' and e['scope']=='in_scope']
    results.append(dict(case='initial_absence_then_later_table_departure',applicability=p['applicability'],outcome=p['outcome'],contradictory_event_tags=contradictions,interpretation='Run-level non-applicability is preserved, but the physical event is tagged r1_fall/in_scope. Consumers must not use those tags without the initial-applicability gate. V4 consistency fix proposed; v3 unchanged.'))
    # No cream-cheese special case is needed by the same frozen post-lift logic.
    fs=f.series();fs[12]=f.frame(12,1.1,'robot');fs[13]=f.frame(13,1.2,'robot');fs[14]=f.frame(14,1.25,None);fs[15]=f.frame(15,1.15,None)
    for frame in fs:frame['objects']['renamed_box']=frame['objects'].pop('object')
    p=evaluate(fs,'renamed_box','controlled-renaming',f.CONFIG)
    results.append(dict(case='post_lift_identity_renaming',post_lift_drops=sum(e['type']=='post_lift_drop' for e in p['events']),R1_outcome=p['outcome'],interpretation='Event predicates are name-independent once qualified facts exist. Scene-specific extraction/configuration remains a separate limitation.'))
    return results

if __name__=='__main__':
    p=HERE/'controlled_audit_results.json'
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(dict(synthetic_only=True,empirical_accuracy_examples=0,probes=probes()),indent=2)+'\n')
    print(p.read_text())
