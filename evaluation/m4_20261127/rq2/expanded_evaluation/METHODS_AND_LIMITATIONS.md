# Methods and limitations - expanded RQ2

## Sources and deduplication
This report uses frozen committed files only. The inventory contains 102 unique execution identities: 60 same-scene candidates, 4 earlier development executions, and 38 cross-scene preflight executions. The 60-run checker output is taken row by row from evaluation/r1_v3_generalization/execution/predictions.json (300 object units). Earlier references are from evaluation/r1_v3/results.json (20 object units). Finalized calibration rows remain separate in evaluation/m4_20261127/rq2/R1_RESULTS.csv; all three variants share one canonical source ID. The 432 historical pool is not materialized per execution and is excluded.

## Coverage
Coverage and abstention are recomputed from the 300 frozen prediction rows. Not-applicable units do not enter applicable-decision denominators; insufficient_information is an abstention. These are operational coverage measures, not accuracy. Mapping-gate exclusions are not checker abstentions. No task outcome is used as a reference label.

## Limitations
The selected source manifest says producer-manifest and byte-size checks were performed, but full HDF5 hashes were not independently recomputed. The 38 cross-scene runs fail the frozen mapping gate. The 60-run cohort has no independent human labels. Earlier references are development-exposed and have no positive cases. The three-case calibration is from one canonical source group. Thus no independent held-out accuracy estimate is available. No checker execution, simulation, or human judgment was added.
