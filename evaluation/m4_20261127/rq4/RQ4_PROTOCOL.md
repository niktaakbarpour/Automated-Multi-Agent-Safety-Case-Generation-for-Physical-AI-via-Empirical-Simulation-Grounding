# RQ4 protocol: controlled evaluation of planted-defect repair

Written November 23, before any revision model output exists. This is a controlled evaluation of whether two revision methods repair planted unsupported-guarantee defects. It is not a general measure of Revision Agent effectiveness, and it does not test checked evidence, which is blocked (see RQ4_FEASIBILITY.md, section 1). If a run has to differ from what is written here, the difference goes in the run notes and the limitations. This file is not edited afterwards to fit the results.

Agreed scope (Nikta, November 23): the 3 cases below, real Qwen revisions against the existing template baseline, the same cases and criteria for both, and an independent blinded review as the primary measure.

## Cases

| Case | Source group | Planted defect | Critic finding repaired | Report source |
|---|---|---|---|---|
| P1-M1a | P1, real one-pass LIBERO execution (development-exposed) | unsupported guarantee on cream_cheese_1:G1 (goal) | rule CLAIM-ABSOLUTE-SAFETY, C12 | `critic.review` with no model |
| P1-M1b | P1 | unsupported guarantee on ketchup_1:G1 (goal) | model finding, C05 | `critic.review` replaying the saved RQ3 reply P1-M1b:R:r3 |
| P2-M1c | P2, synthetic Critic Case C | unsupported guarantee on vial_b/U1 (unresolved claim) | rule CLAIM-ABSOLUTE-SAFETY, C12 | `critic.review` with no model |

3 cases from 2 source executions, 0 independent cases, one defect type. The P1-M1b report is rebuilt from the only R repeat that detected the defect. Its input hash equals the one the RQ3 runner recorded, so the report pairs the reply with the exact input Qwen answered. Choosing that repeat is a selection. `CASE_MANIFEST.csv` records each case's hashes.

## Finding approval

The revision engine acts only on findings with a recorded human decision. The rule, fixed before any revision output: approve exactly the finding on the planted defect's node whose category is acceptable for the defect type (`rq3/mutations/gold_labels.json`). Every other finding gets no decision (or is declined), and is carried forward unchanged, never acted on and never removed.

The decisions are recorded by hand, not generated. `experiment/build_approval_form.py` writes `FINDING_APPROVALS.csv` with one row per finding of each case's Critic report, bound to that report by its digest, and with the human columns empty. The approver fills `decision`, `approver`, `approved_on` and the attestation sentence ("I read this finding and its target node myself and made this decision.") in each row they decide. The `on_planted_defect_node` column only helps locate the finding; it is not a decision. The code reads the file and refuses to build stage 1 if a row is missing, repeated, bound to another report or changed from the report, if a decision lacks the approver, an ISO date or the exact attestation, if a case does not have exactly one approved finding, or if the approved finding is not the one the fixed rule names. The form is never overwritten once a decision is recorded. The approvals were recorded by Alex Hashemi, who wrote the planted defects and their labels, so he is not an independent approver.

## The two methods

- **Template:** the existing deterministic adapter (`drafter/revision/adapters.py`), unchanged.
- **Qwen:** Qwen3-32B proposing edits through a model adapter in the same edit format. Settings are the RQ3 frozen settings (`rq3/experiment/settings.py`): temperature 0.6, top_p 0.95, top_k 20, max_tokens 8192, JSON response format, thinking off. 3 samples per case, no per-request seed. The system prompt is `experiment/revision_prompt.md` (`rq4-revision-prompt/v1`).

Both methods get the same permitted information through one wrapper (`SamePermittedInformation`): the engine's context (the argument bundle, the approved findings with their targets and allowed edits, open evidence requests) plus the evidence the Critic's model view shows (evidence records, checker admission log, retrieval context). No checker assessment is admitted for either parent. A digest of this information is recorded per output, and the tests check it is identical for both methods. Qwen's prompt contains it verbatim as JSON, apart from run bookkeeping (revision ID, round, round limit, and the revision history, which is empty here). The template does not use the evidence. It receives it anyway.

The engine checks and applies every proposed edit in the same way for both methods (`drafter/revision`, unchanged). It refuses, among other things, an edit on a node other than the finding's target, any change to frozen inputs, and assurance wording (guarantee, certified, proves, safe and related words, even negated). After applying, all of its validators must pass, or the original is kept.

## Measures

**Primary: blinded human review** of every revised argument (`REVIEW/`). Each item shows the original argument for the object, the approved finding, any other Critic finding (unchanged), the before and after of the revised node, the revised argument, and the evidence both methods were given. It does not show the method, its justification or a run ID. The reviewer, Nikta or Ryiad (not Alex), answers per item:

- defect fixed: yes, partly, no, indeterminate
- revised claim supported by evidence: yes, no, indeterminate
- new problem introduced: yes, no, indeterminate (new unsupported claim, wrong or invented evidence reference, contradiction, or a statement that no longer works)
- scope preserved: yes, no, indeterminate

A **correct repair** is defect fixed "yes", supported "yes", new problem "no" and scope preserved "yes". The review is completed and frozen before the methods are compared. `score.py` writes no comparison unless the form has exactly the expected columns and exactly one row per review item (no duplicate, missing or unexpected blind ID), every answer is an allowed value, every row names the reviewer, an ISO review date and the prior-exposure declaration, a "yes" for a new problem has a description, and all rows carry the same ISO freeze timestamp. It also checks that the sealed key lists exactly the revised outputs, is bound to their saved results by digest, and that no review item was changed after the packet was built.

**Per output status:** revised; abstained (the method declined the finding); invalid (an unparseable or malformed answer, an edit the engine refused, a revision that failed a validator, or a server reply that did not finish normally); missing or no reply. Only revised outputs are reviewed. The others count as not repaired.

**Secondary: second Critic.** The production Critic (`critic.review`, rule findings shown to the model as in production) reviews each original argument 3 times, each template revision 3 times (it is the same for every sample), and each revised Qwen output once, so each method gets 3 second reviews per case. Reported:

- **target still flagged:** a finding on the planted node with a category acceptable for the defect type.
- **new objection:** any other finding whose object, node and category appear in neither the stage 1 report nor any second review of the original argument.

Critic acceptance never counts as a successful repair on its own.

Rates are given per method over all outputs (Qwen 9, template 3) and over revised outputs, with mean and SD over the 3 Qwen samples. The template is deterministic, so it has one output per case.

## Accounting and provenance checks

All 9 Qwen requests always get a result record. A request with no attempt is `missing`, one with no server reply is `no_reply`, and both stay in the denominators with abstentions and invalid outputs. Both GPU stages are checked the same way before anything is used, and any problem stops the step with nothing written:

- every run ID must belong to the batch, and a request may be answered at most once (resends are only for attempts with no reply), with attempts numbered in order;
- each attempt must have been made for the batch's input: user and system digests, and the digest of the exact messages sent;
- each reply must match its recorded digest;
- the client settings recorded with each attempt must be the frozen ones (model, temperature, max_tokens, timeout, extra parameters, system message), all attempts of a stage must name one model revision, and scripted test replies are never accepted from the command line;
- a reply that did not finish normally or names a model other than the accepted ones is kept as `invalid_server_reply`;
- the stage 1 batch must use the frozen revision prompt and the stage 2 batch the frozen Critic prompt.

`score.py` then re-derives everything it depends on: stage 1 must equal a fresh build, the saved Qwen results and the second Critic batch must be exactly what the stage 1 responses give, each second-review request must be the original argument or the re-criticism request of its saved revision result, and each second review is rebuilt with `critic.review` and must match the input the reply was made for. `RQ4_PROVENANCE.json` records the prompts, model, settings, model revisions per stage, batch digests and the digests of the response, approval, review-form and key files.

## Protection of saved files

No builder changes a saved file silently. If a fresh build differs from what is saved, nothing is written and the differing files are listed. `build_stage1.py --rebuild` may change stage 1 only while no stage 1 response and no Qwen result exists. Saved Qwen results, the second Critic batch, the review items, the review manifest and the sealed key are never changed. The review form is written once, blank, and then left to the reviewer. `score.py` never changes an existing output file unless `--replace-outputs` is given.

## Commands

CPU steps can run anywhere. GPU steps are for Nikta only. The runner is the RQ3 runner, unchanged. Serve Qwen3-32B as for RQ3 (`--served-model-name Qwen/Qwen3-32B`, context 24,576). The largest stage 1 prompt is about 35,000 characters including the system prompt. At the 3.4 to 3.9 characters per token measured in the RQ3 run, that is at most about 10,300 tokens, so with the 8,192-token output limit a request needs at most about 18,500 of the 24,576 tokens.

```sh
export PYTHONPATH=.
E=evaluation/m4_20261127/rq4/experiment
RUN=$E/real_run_<UTC timestamp>          # new folder for this run
mkdir -p $RUN

# 0. CPU: stage 1 inputs are unchanged (and the hand-recorded approvals are valid)
python3 $E/build_stage1.py --check

# 1. GPU: Qwen revisions (9 requests)
python3 evaluation/m4_20261127/rq3/experiment/run_batch.py --batch $E/batch_stage1 \
    --out $RUN/RQ4_STAGE1_RESPONSES.jsonl --base-url http://127.0.0.1:PORT/v1 --model-revision REVISION

# 2. CPU: apply the revisions, build the second Critic batch and the review packet
python3 $E/build_stage2.py --responses $RUN/RQ4_STAGE1_RESPONSES.jsonl
python3 $E/build_review.py

# 3. GPU: second Critic (18 requests plus one per revised Qwen output, at most 27)
python3 evaluation/m4_20261127/rq3/experiment/run_batch.py --batch $E/batch_stage2 \
    --out $RUN/RQ4_STAGE2_RESPONSES.jsonl --base-url http://127.0.0.1:PORT/v1 --model-revision REVISION

# 4. Human: complete and freeze rq4/REVIEW/REVIEW_FORM.csv (Nikta or Ryiad), without opening experiment/sealed/

# 5. CPU: score (add --pre-review before step 4 for per-output facts only)
python3 $E/score.py --stage1-responses $RUN/RQ4_STAGE1_RESPONSES.jsonl \
    --stage2-responses $RUN/RQ4_STAGE2_RESPONSES.jsonl --out-dir evaluation/m4_20261127/rq4
```

Use `--retry-transport-errors` on a GPU step only for requests that got no server reply. Keep the `.meta.jsonl` files and the server launch command with the responses. Step 2 needs no GPU, so it can run right after step 1, and step 3 can follow on the same day. The review (step 4) needs only steps 1 and 2.

## Tests

```sh
PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq4/tests -p 'test_*.py' -v
```

`tests/test_rq4.py` checks that the saved stage 1 equals a fresh build, the cases, sources, prompt and settings, the recorded human approvals, the replayed report's input hash, that both methods get identical permitted information, and that no case ID, label, approval record or method name reaches the model. It also checks that findings other than the approved one are carried forward unchanged and shown to the reviewer.

Regression tests refuse, among other things: approval rows that are missing, repeated, bound to another report, changed, unsigned, undated, without the exact attestation, off the fixed rule, or with no approval at all; stage 1 responses with an unknown run ID, a request answered twice, another input, other sent messages, an altered reply, misnumbered attempts, scripted replies from the command line, other settings, another model or two model revisions; review forms that are blank, incomplete, with a bad value, a duplicate, missing or unexpected blind ID, no reviewer, no exposure declaration, a bad date, no or mixed freeze timestamps, an undescribed new problem, or wrong columns; a review item changed after the packet was built, a key bound to another result, stage 2 responses made for another input, and stage 1 responses that do not give the saved results. They also check that saved files and outputs are never overwritten without the explicit flag.

A dry run with scripted replies, which are test inputs and never results, covers every output path: a repair, assurance wording, a decline, a non-JSON reply, a malformed answer, an edit on the wrong node, a missing output and a reply from another model. It also covers the second Critic batch, the blinding of review items, the pre-review facts and the scores, which were worked out by hand.

## Limitations known before the run

- 3 cases from 2 source executions, all unsupported guarantees. No conclusion about other defect types (M2 cannot be revised under the current contract, and M3 was never detected), about checked evidence, or about new executions.
- The approver wrote the planted defects. The labels have not had an independent review (Ryiad's RQ3 review form is still blank).
- The template's fixed wording is recognisable across review items, so blinding between methods is partial. It also writes goal wording on P2-M1c, which is an unresolved claim.
- One reviewer, unless both Nikta and Ryiad review. The review is not technically sealed: the key sits in the repository, and independence rests on the reviewer's exposure declaration.
- One model, one prompt, one set of decoding settings, 3 samples. The template is deterministic, so its spread over samples is not defined.
- The P1 retrieval context mentions Phase 5 values, but the Phase 5 structured evidence is not in the Critic's model view, so neither method sees it, as in RQ3.
