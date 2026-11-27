# Current M4 integration status

This report states current component status. The dated [end-to-end feasibility report](END_TO_END_FEASIBILITY_REPORT.md) is retained as a historical snapshot and is not the current Task 8A status report.

| Stage | Current status | What is verified | Remaining boundary |
|---|---|---|---|
| RQ1 retrieval | Planner-v2 actual replay and adjudication complete; fault suite complete | 216 attempts: 133 verified complete, 71 correct abstentions, 12 normal-run cases evaluation-unavailable because the normal replay did not run their fault fixtures; separate 12/12 fault cases rejected correctly; zero confirmed false-complete retrievals | Exposed development cohort; external retrieval store/source corpus/encoder needed for fresh raw-source reproduction; no independent held-out cases |
| RQ2 checker | Final retrospective reference scored; physical admission remains blocked | 3/3 applicability agreement; on two applicable cases TP=1, TN=1, FP=0, FN=0; one not-applicable case excluded | One canonical source group; final labels not independently verified, early event-review forms preserved with discrepancy; no physical admission or accuracy generalization |
| R1 v3 Drafter request | Frozen request and request builder available | Original request binds to the LIBERO Long/OpenVLA-OFT execution, requirement version and frame 10–257 scope | External source evidence is required for raw-source replay |
| Genuine Task 8A Drafter | Complete; one genuine generation, HTTP 200, 112.87 s, no retries | Five graphs and authoritative host validation; all outcomes `insufficient_information`; evidence admission disabled | Supplementary human reasoning review is pending; this is not safety-case approval |
| Drafter-to-Critic | Accepted R1 v3 handoff in PR #63 | Original request and accepted generation report are validated and retained losslessly; request and bundle hashes are recorded | PR #62 rejection reproduction is historical and superseded by the accepted handoff contract |
| Critic on genuine Task 8A argument | Deterministic CPU review completed in the local orchestration candidate | Genuine Task 8A draft was revalidated; Critic report has no admitted Checker assessment, keeps all five conclusions unresolved, and leaves `safety_claim_verified=false` | R1 v3 Critic model inference is not implemented; no evidence of model-based semantic review |
| Revision on genuine Task 8A chain | Not run; no actionable finding in the deterministic report | No Revision request was fabricated or run | If a later Critic produces actionable R1 v3 findings, a compatible R1 v3 Critic-to-Revision contract and validated adapter are not yet implemented |
| Second Critic on genuine Task 8A chain | Not applicable in this resume | No revision was produced | Requires a validated revision and an agreed second-Critic interface |
| End-to-end safety-case acceptance | Not demonstrated | Saved Drafter-to-deterministic-Critic resume was validated; all evidence gaps and review requirements remain visible | Requires RQ1 retrieval/source registration, an admitted Checker assessment where applicable, reasoning review, integrated Critic/Revision contracts and appropriate independent evidence review; no current result establishes physical safety |

## Reproduction from repository root

Use Python 3.12 and the CPU dependencies listed in the root installation and CI instructions. These commands do not call a model or require a GPU:

```sh
python3 -m evaluation.m4_20261127.integration.build_r1v3_request --check
python3 evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
python3 -m integration.orchestrator resume-task8a --out-dir /tmp/m4-task8a-resume
python3 -m unittest drafter.tests.test_r1v3_profile drafter.tests.test_r1v3_generation -v
python3 -m unittest integration.tests.test_orchestrator -v
python3 evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py
sha256sum -c evaluation/m4_20261127/integration/task8a_r1v3/ARTIFACT_SHA256SUMS.txt
sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt
```

`DOWNSTREAM_REPRODUCE.py` and its diagnostic report are preserved as historical PR #62 artifacts. In the combined PR #63 interface, its expected rejection is superseded: current handoff behavior is tested by `integration.tests.test_r1v3_handoff` and by the saved-run orchestration command above.

The historical feasibility report describes an earlier saved fixture. It remains preserved for provenance; use this status report and the [experiment registry](../EXPERIMENT_REGISTRY.md) for current conclusions.
