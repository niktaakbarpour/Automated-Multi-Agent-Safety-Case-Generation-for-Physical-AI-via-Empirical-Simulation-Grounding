# Multi-source completeness and remaining boundary

C4: 24/24 complete required sets; 84/84 required-family obligations retrieved. Eight authored combinations repeat across three disjoint scopes: two robot fields; gripper state/action/time; joint/inference/geometry; actuator/count/source; velocity/camera/time; joint/contact/source; all six arrays; action/inference/execution/source metadata. Per-source temporal coverage stays separate. No shared physical instant is inferred.

Descriptive Wilson 95% interval for 24/24 is [0.8620237953250198, 1.0]; authored formulations are not a random linguistic population. Only eight distinct C4 templates were tested, not 24 independent linguistic cases.

Per-category final bundle metrics:

| Category | Eligible | P@1 | R@20 | Required-set failures |
|---|---:|---:|---:|---:|
| C1 | 24 | 1.0 | 1.0 | 0 |
| C2 | 24 | 1.0 | 0.9375 | 3 |
| C3 | 22 | 1.0 | 1.0 | 0 |
| C4 | 24 | 1.0 | 1.0 | 0 |
| C5 | 0 | N/A | N/A | 0 |
| C6 | 6 | 1.0 | 1.0 | 0 |
| C7 | 12 | 1.0 | 1.0 | 0 |
| C8 | 0 | N/A | N/A | 0 |
| C9 | 24 | 1.0 | 1.0 | 0 |

Three C2 instances of one formulation omit raw.robot0_joint_pos while returning correct recorded_time and marking the reduced plan complete. This is a genuine query-to-plan completeness defect, not a missing source or corrected reference. Exact cases are in FINAL_ASSESSMENT.json and issue 001. The external audit identifies it; the production bundle cannot currently detect it. No safety-sufficiency classifier was added. Aggregate gates pass, but the requested-obligation contract does not yet justify freezing the general interface.
