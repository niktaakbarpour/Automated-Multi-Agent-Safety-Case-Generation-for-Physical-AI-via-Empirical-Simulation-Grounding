"""Machine-readable dispositions; never registers a runtime empirical profile."""
from .analyze import HERE
from evaluation.r1_v4.libero_evidence_audit.audit_sources import load,save,csvwrite,sha
from .numerical_checks import check

def rows(summary,oracle,source_validated=False):
 structural=source_validated and summary['frames']==1312 and summary['BOX_pieces']==28
 numerical=bool(oracle.get('passed')) and oracle.get('exact_rational_coordinate_checks',0)>0
 return [dict(gate_id=g,status=s,conditions=c,evidence=e,remaining=r,empirical_admission_enabled=False) for g,s,c,e,r in [
 ('G01_native_BOX_measurements','VERIFIED' if structural else 'BLOCKED_ON_EVIDENCE','Four hash-bound runs, complete native mapping and raw transforms','SOURCE_BINDINGS.json; DIAGNOSTIC_SUMMARY.json','Only this model; not load-bearing or full empirical geometry admission'),
 ('G02_numerical_corner_enclosure','VERIFIED' if numerical else 'BLOCKED_ON_EVIDENCE','Exact-rational oracle passes; computational inputs treated exact','NUMERICAL_ORACLE.json; geometry.py','Input/model/physical uncertainties remain unknown'),
 ('G03_geometry_empirical_admission','CONDITIONALLY_SUPPORTED','Identity/BOX arithmetic established; uncertainty profile incomplete','GEOMETRY_CALIBRATION.md','Independent geometry and physical uncertainty validation'),
 ('G04_initial_support_applicability','BLOCKED_ON_EVIDENCE','Need validated support/absence and t0 inference','SUPPORT_INFERENCE.md','Independent load-bearing/absence references and calibrated profile'),
 ('G05_validated_falling_witness','BLOCKED_ON_EVIDENCE','Need support origin/loss/downward/handling/boundary proof','DEVELOPMENT_REFERENCE_CANDIDATES.csv','No independent in-scope R1 positive; physical uncertainties unresolved'),
 ('G06_qualified_negative_certificate','BLOCKED_ON_EVIDENCE','Need qualified support and transition cells over requested domain','TEMPORAL_VALIDITY.md','Static-looking poses/contact alone do not qualify clear coverage'),
 ('G07_static_coverage_composition','BLOCKED_ON_EVIDENCE','Need admitted compatible cells and independently qualified joins','UNCERTAINTY_REGISTER.md','No empirical negative cell profile admitted'),
 ('G08_dynamic_coverage_composition','UNSUPPORTED','Restricted contract defers dynamic/handling/replacement composition','requirements/r1_generalized_v2/FORMAL_SEMANTICS.md','Separate approved semantics/profile required'),
 ('G09_contact_based_physical_evidence','CONDITIONALLY_SUPPORTED','Raw native contacts complete at samples; physical role unresolved','SUPPORT_INFERENCE.md','Validated load-bearing or force-free alternative; no contact-only rule'),
 ('G10_uncertainty_propagation','BLOCKED_ON_EVIDENCE','Arithmetic enclosures known, necessary physical components null','CALIBRATION_PARAMETERS.csv','Independent bounds and dependency-aware propagation'),
 ('G11_temporal_empirical_admission','BLOCKED_ON_EVIDENCE','Saved indices verified; cache/exposure bounds uncalibrated','TEMPORAL_VALIDITY.md','Source-specific boundary/phase uncertainty contract'),
 ('G12_independent_reference_validation','BLOCKED_ON_EVIDENCE','Proposals are one exposed AI analysis, no human review','REFERENCE_REVIEW_PROTOCOL.md','Independent review/adjudication and frozen prospective evaluation protocol'),
 ]]
def main():
 summary=load(HERE/'DIAGNOSTIC_SUMMARY.json');oracle=check();save(HERE/'NUMERICAL_ORACLE.json',oracle)
 bindings=load(HERE/'SOURCE_BINDINGS.json')
 for r in bindings['recordings']:assert sha(r['path'])==r['sha256']
 for n,h in bindings['prior_files'].items():assert sha(HERE.parents[2]/n)==h
 result=rows(summary,oracle,source_validated=True);csvwrite(HERE/'EVIDENCE_GATES.csv',result)
 save(HERE/'GATE_STATUS.json',dict(gates=result,empirical_admission_enabled=False,physical_judgments_issued=0,independent_reference_cases=0))
 print('Gates',len(result),'numerical checks',oracle['exact_rational_coordinate_checks'])
if __name__=='__main__':main()
