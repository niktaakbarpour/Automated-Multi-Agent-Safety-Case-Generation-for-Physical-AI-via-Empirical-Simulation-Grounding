# RQ4 error analysis

The frozen correct-repair criterion requires all four: defect_fixed=yes, revised_claim_supported_by_evidence=yes, new_problem_introduced=no, and scope_preserved=yes. There is one unsuccessful output.

## Unsuccessful repair

- **P2-M1c:template (template; P2-M1c; one of the frozen pilot cases):** Revision was successfully applied and the original defect was judged fixed. The assessment marked evidence support **no**, a new problem **yes**, and scope preservation **no**. The recorded issue was a GSN role mismatch: a node structurally typed as an `unresolved_claim` was described using a different GSN role, changing node meaning and introducing a semantic/evidence/scope problem after successful application. This was not a failure to remove the planted guarantee.

## Second-Critic comparison

Second-Critic results are secondary signals, not correctness labels. No second review reflagged the planted target for either method. For the P2-M1c template output, 2 of 3 second reviews raised new objections; the remaining one did not. For Qwen on P2-M1c, 2 of 3 second reviews raised new objections; the remaining one did not. Across all outputs: template 2/9 and Qwen 2/9 second reviews raised new objections. This does not override the human result: template P2-M1c was unsuccessful, whereas all Qwen outputs met the human criterion. “No target reflagging” does not establish a correct repair.

## Successful outputs and unavailable failure types

All 9 Qwen outputs and 2 template outputs were successful repairs under the prespecified human rule. All 12 outputs had status revised; there were no abstentions, invalid outputs, or missing outputs. No failure-to-remove-original-defect case occurred. No indeterminate human judgments occurred.
