# Phase 5E database coverage

Validated release: `5d3eb7589ddbf564cf29189af3264fd9861df44780e65e3246b62bbe74bc9934` at `/disk/1/data/niktakbr/trustworthy-phase5e-working/final-validated/corpus-285.sqlite` (401,522,688 bytes). The release contains 285 executions, 67,053 evidence records and 45,157 saved frames. The 2,000 historical catalog entries remain metadata-only for unindexed cases. This is 285/2,000 (14.25%) execution measurement coverage, not complete LIBERO coverage.

| New task | Executions | Frames | Records | Native geoms |
|---|---|---|---|---|
| object/task_01 | 49 | 6901 | 11389 | 139 |
| object/task_03 | 49 | 7034 | 11557 | 137 |
| object/task_05 | 49 | 6889 | 11389 | 121 |
| object/task_09 | 49 | 6500 | 10927 | 120 |

All 21,791 baseline IDs and 89 baseline executions are retained. Stratum counts: `{'corpus_expansion': 55223, 'development': 11830}`. Original 40 development executions remain separate from database-only expansion. Full source provenance and frame scopes are in the manifests. Six raw measurement types cover every configured object and saved-frame window; this is snapshot availability, never continuous physical coverage.

| Evidence type | Records |
|---|---|
| ai_reference_interpretation | 10 |
| calibration_provenance | 285 |
| camera_reference | 10298 |
| contact | 10298 |
| evidence_limitations | 285 |
| execution_metadata | 285 |
| native_geometry | 10298 |
| object_identity | 1915 |
| object_pose | 10298 |
| requirement_definition | 285 |
| robot_state | 10298 |
| support_surface_identity | 1915 |
| task_instruction | 285 |
| timestamp | 10298 |

No physical event labels are added. Baseline AI interpretations remain provisional; no human ground truth is created. All 60 reserved evaluations and 38 historical preflight executions are excluded from the new measurement corpus.
