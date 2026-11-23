# RQ2 transfer investigation: source-linked evidence

## Frozen evidence available in this repository

Use these existing files; they contain per-case and per-execution records:

- evaluation/m4_20261127/rq2/expanded_evaluation/CHECKER_CASE_RESULTS.csv
- evaluation/m4_20261127/rq2/expanded_evaluation/SOURCE_ELIGIBILITY_INVENTORY.csv
- evaluation/m4_20261127/rq2/expanded_evaluation/EXCLUSIONS.csv
- evaluation/m4_20261127/rq2/expanded_evaluation/SUMMARY_METRICS.json
- evaluation/m4_20261127/rq2/expanded_evaluation/METHODS_AND_LIMITATIONS.md
- evaluation/m4_20261127/rq2/R1_CASE_MANIFEST.csv
- evaluation/m4_20261127/rq2/R1_EVIDENCE_NOTES.md
- evaluation/m4_20261127/rq2/R1_RESULTS.csv and R1_METRICS.json

The frozen summary identifies 60 same-scene generalization executions (10 same-task reserved; 50 changed-task, same-scene), five object units per execution, 300 units total, 180 not applicable and 120 applicable. On the changed-task same-scene stratum, decision coverage is 0/100 applicable units and abstention is 100/100. Same-task coverage is 20/20 applicable units. These are coverage/abstention findings, not accuracy: the generalization cases have no independent human labels.

The work allocation calls this the task-role transfer failure. The saved results' exact partition name is cross_task_same_scene. Use that label and do not silently relabel it as a different role-transfer experiment.

The 38 cross-scene preflight executions are in EXCLUSIONS.csv and failed the frozen mapping gate; they are not checker abstentions or evaluated cases. Four earlier development executions and the three-variant, one-source-group human calibration are separate cohorts. Do not pool their confusion matrices with the generalization coverage audit. The historical 432-execution aggregate is not an identified per-execution sample.

## Analysis boundaries

Trace each row through its provenance and evidence-sufficiency fields. Distinguish eligibility/mapping rejection from checker abstention. Group related object rows by canonical execution; five objects from one execution are not five independent executions. Do not infer R1 violation from task failure or task outcome. Report only the existing frozen coverage, abstention, applicability, and gate records unless independently reviewed references are separately supplied.

No separate task-role-specific failure dataset was located in the tracked M4 tree. The changed-task same-scene case rows and eligibility/gate files above are the available source evidence; they do not establish cross-scene transfer.
