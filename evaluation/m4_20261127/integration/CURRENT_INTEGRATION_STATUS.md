# Current M4 integration status

This report states current component status. The dated [end-to-end feasibility report](END_TO_END_FEASIBILITY_REPORT.md) is retained as a historical snapshot and is not the current Task 8A status report.

| Stage | Current status | What is verified | Remaining boundary |
|---|---|---|---|
| RQ1 retrieval | Saved analyses complete; fresh raw-source replay limited | Historical and Phase 5K saved results; known temporal false-complete cases | External retrieval store, source corpus/HDF5 and pinned encoder needed for full replay; held-out expansion has zero eligible independent cases |
| RQ2 checker | Descriptive calibration/coverage outputs complete; physical admission blocked | Saved row-level counts and applicability/coverage validation | No suitable independent physical reference set; do not call metrics physical accuracy |
| R1 v3 Drafter request | Frozen request and request builder available | Original request binds to the LIBERO Long/OpenVLA-OFT execution, requirement version and frame 10–257 scope | External source evidence is required for raw-source replay |
| Genuine Task 8A Drafter | Complete; one genuine generation, HTTP 200, 112.87 s, no retries | Five graphs and authoritative host validation; all outcomes `insufficient_information`; evidence admission disabled | Supplementary human reasoning review is pending; this is not safety-case approval |
| Drafter-to-Critic | Known contract rejection reproduced and preserved | PR #62 adds a specific `ContractError` reproduction, five expected diagnostic markers, original argument validation, and CPU CI checks | Adapter schema/interface must be reviewed and updated by Alex to preserve R1 v3 evidence/provenance fields |
| Critic on genuine Task 8A argument | Not run | No fabricated Critic request is used | Requires accepted adapter contract and Alex’s integration work |
| Revision on genuine Task 8A chain | Not run | Separate RQ4 pilot is complete and remains bounded | Do not conflate RQ4 pilot with Task 8A end-to-end flow |
| Second Critic on genuine Task 8A chain | Not run | RQ4 pilot has separate second-Critic outputs | No real end-to-end revised Task 8A argument has been re-criticized |
| End-to-end safety-case acceptance | Not demonstrated | Individual components and saved CPU interfaces have scoped checks | Requires adapter integration, reasoning review, downstream stages and appropriate independent evidence review; no current result establishes physical safety |

## Reproduction from repository root

Use Python 3.12 and the CPU dependencies listed in the root installation and CI instructions. These commands do not call a model or require a GPU:

```sh
python3 -m evaluation.m4_20261127.integration.build_r1v3_request --check
python3 evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
python3 -m unittest drafter.tests.test_r1v3_profile drafter.tests.test_r1v3_generation -v
python3 evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py
sha256sum -c evaluation/m4_20261127/integration/task8a_r1v3/ARTIFACT_SHA256SUMS.txt
sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt
```

To reproduce the known adapter rejection without inference, run the documented `DOWNSTREAM_REPRODUCE.py`; exit 2 with its expected `ContractError` diagnostics is the expected result, while other exit codes indicate a failure. The report and exact expected diagnostics are in `task8a_r1v3/DOWNSTREAM_INTERFACE_DIAGNOSTICS.md`.

The historical feasibility report describes an earlier saved fixture. It remains preserved for provenance; use this status report and the [experiment registry](../EXPERIMENT_REGISTRY.md) for current conclusions.
