"""Generate evidence-linked blank forms; no human labels/identities entered."""
import json,argparse
from pathlib import Path
OBJECTS=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']

def main(out):
    out=Path(out);examples=json.loads((out/'example_manifest.json').read_text());forms=out/'human_review';forms.mkdir(exist_ok=True)
    support=[];events=[];uncertainties=[]
    for ex in examples:
        run=ex['frames'][0]['run_id']
        for obj in OBJECTS:
            support.append({'form_id':ex['example_id']+'-'+obj,'run_id':run,'object':obj,'assessment_frame':'000010','evidence_references':['prepolicy_static_endpoint_geometry.json','settling_findings_by_run.json',ex['sheet']],'reviewer':'','support_label':None,'supporting_entity_or_chain':None,'evidence_reasoning':None,'uncertainties':None,'decision':None})
        events.append({'form_id':ex['example_id'],'run_id':run,'evidence_frames':[x['frame'] for x in ex['frames']],'image_sheet':ex['sheet'],'reviewer':'','object':None,'initial_support_form_reference':None,'event_interpretation':None,'within_requirement_interval':None,'last_supported_frame':None,'first_departure_frame':None,'falling_motion_frames':None,'catch_or_new_support_frame':None,'support_transfer_vs_fall_reasoning':None,'uncertainty':None,'decision':None})
        uncertainties.append({'form_id':ex['example_id'],'run_id':run,'reviewer':'','missing_information':None,'available_but_unvalidated_information':None,'timing_uncertainty':None,'geometry_uncertainty':None,'visibility_or_occlusion':None,'definition_or_scope_ambiguity':None,'effect_on_interpretation':None,'decision':None})
    for n,data in [('initial_support_forms.json',support),('event_forms.json',events),('uncertainty_forms.json',uncertainties)]:
        (forms/n).write_text(json.dumps({'human_labels_entered':False,'forms':data},indent=2)+'\n')
    (forms/'instructions.md').write_text('''# Blank human review forms

All identity, label and decision fields are blank/null. Automated interpretations are in a separate file and are not labels. Review evidence independently before reading those suggestions if practical.

Initial support labels to consider: direct_table_support; indirect_table_support_with_explicit_chain; supported_elsewhere; airborne_or_unsupported; unknown. Give geometry, pose and contact/image evidence together. Contact count, BDDL, root height or appearance alone is insufficient. No labels are preselected.

Event interpretation options: table_departure_and_falling_motion; supported_tip_or_slide; supported_lift_or_transfer; released_object_descent_definition_needs_review; setup_departure_before_interval; other; unknown. Give exact frame/time brackets and whether this interpretation lies inside the clarified interval. These are human event descriptions, not automatic safety verdicts.

Uncertainty: distinguish absent information from available but unvalidated fields, phase uncertainty, occlusion and unresolved definition/scope. Do not turn unknown support into no violation or non-applicability. Human reviewers supply their own identities and decisions; none is entered on their behalf.
''')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
