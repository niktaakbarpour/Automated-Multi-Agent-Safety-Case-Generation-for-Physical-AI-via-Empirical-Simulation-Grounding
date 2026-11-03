# Blocking: query intent can be dropped while the interpreted plan is complete

Observed on frozen V1 and V2: the standalone phrase “joint configuration at simulator label” resolves only to recorded_time. V2 cases KH2-C2-02, KH2-C2-10 and KH2-C2-18 omit raw.robot0_joint_pos but report COMPLETE WITHIN VERIFIED CONTRACT. These are three source-scope instances of one formulation, not three independent linguistic failures.

The time labels returned are correct. No numeric/source/scope/assurance corruption was observed. The problem is intent coverage before per-family execution. Fixing only the observed phrase would not establish general coverage.

Proposed focused correction: explicitly account for every measurement request in the query proposal, expose unresolved spans/obligations, and abstain or mark ambiguity when a measurement-bearing clause is not resolved. Extend the development lexicon from independently reviewed schema terminology. Add regression cases for the now-exposed failures. Freeze new questions before evaluating the correction; do not reuse these cases as independent evidence of generalization.

No production patch is applied after the final assessment. Aggregate gates passed, but this violates the pre-existing requirement that completeness refer to requested evidence obligations. General natural-language completeness must remain experimental until corrected.
