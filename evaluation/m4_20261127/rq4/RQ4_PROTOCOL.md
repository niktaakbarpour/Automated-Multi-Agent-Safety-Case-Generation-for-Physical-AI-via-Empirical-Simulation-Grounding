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

The revision engine acts only on findings with a recorded human decision. The rule, fixed before any revision output: approve exactly the findings on the planted defect's node whose category is acceptable for the defect type (`rq3/mutations/gold_labels.json`), and give every other finding no decision. Undecided findings are carried forward unchanged, never acted on and never removed. Each case has exactly one approved finding. The decisions are recorded as `human_review` by Alex Hashemi, who wrote the planted defects and their labels. He is not an independent approver.

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

A **correct repair** is defect fixed "yes", supported "yes", new problem "no" and scope preserved "yes". The review is completed and frozen before the methods are compared: `score.py` refuses to write the comparison until every item has a complete, frozen judgment.

**Per output status:** revised; abstained (the method declined the finding); invalid (an unparseable or malformed answer, an edit the engine refused, a revision that failed a validator, or a server reply that did not finish normally); missing or no reply. Only revised outputs are reviewed. The others count as not repaired.

**Secondary: second Critic.** The production Critic (`critic.review`, rule findings shown to the model as in production) reviews each original argument 3 times, each template revision 3 times (it is the same for every sample), and each revised Qwen output once, so each method gets 3 second reviews per case. Reported:

- **target still flagged:** a finding on the planted node with a category acceptable for the defect type.
- **new objection:** any other finding whose object, node and category appear in neither the stage 1 report nor any second review of the original argument.

Critic acceptance never counts as a successful repair on its own.

Rates are given per method over all outputs (Qwen 9, template 3) and over revised outputs, with mean and SD over the 3 Qwen samples. The template is deterministic, so it has one output per case.

## Commands

CPU steps can run anywhere. GPU steps are for Nikta only. The runner is the RQ3 runner, unchanged. Serve Qwen3-32B as for RQ3 (`--served-model-name Qwen/Qwen3-32B`, context 24,576). The largest stage 1 prompt is about 35,000 characters including the system prompt. At the 3.4 to 3.9 characters per token measured in the RQ3 run, that is at most about 10,300 tokens, so with the 8,192-token output limit a request needs at most about 18,500 of the 24,576 tokens.

```sh
export PYTHONPATH=.
E=evaluation/m4_20261127/rq4/experiment
RUN=$E/real_run_<UTC timestamp>          # new folder for this run
mkdir -p $RUN

# 0. CPU: stage 1 inputs are unchanged
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

# 5. CPU: score
python3 $E/score.py --stage2-responses $RUN/RQ4_STAGE2_RESPONSES.jsonl --out-dir evaluation/m4_20261127/rq4
```

Use `--retry-transport-errors` on a GPU step only for requests that got no server reply. Keep the `.meta.jsonl` files and the server launch command with the responses. Step 2 needs no GPU, so it can run right after step 1, and step 3 can follow on the same day. The review (step 4) needs only steps 1 and 2.

## Tests

```sh
PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq4/tests -p 'test_*.py' -v
```

`tests/test_rq4.py` checks that the saved stage 1 equals a fresh build, the cases, sources and settings, the fixed approval rule, the replayed report's input hash, that both methods get identical permitted information, and that no case ID, label or method name reaches the model. It also checks that findings other than the approved one are carried forward unchanged and shown to the reviewer. A dry run with scripted replies, which are test inputs and never results, covers every output path: a repair, assurance wording, a decline, a non-JSON reply, a malformed answer, an edit on the wrong node and a missing output. It also covers the second Critic batch, the blinding of review items, the refusal to compare before the review is complete, and the scores, which were worked out by hand.

## Limitations known before the run

- 3 cases from 2 source executions, all unsupported guarantees. No conclusion about other defect types (M2 cannot be revised under the current contract, and M3 was never detected), about checked evidence, or about new executions.
- The approver wrote the planted defects. The labels have not had an independent review (Ryiad's RQ3 review form is still blank).
- The template's fixed wording is recognisable across review items, so blinding between methods is partial. It also writes goal wording on P2-M1c, which is an unresolved claim.
- One reviewer, unless both Nikta and Ryiad review. The review is not technically sealed: the key sits in the repository, and independence rests on the reviewer's exposure declaration.
- One model, one prompt, one set of decoding settings, 3 samples. The template is deterministic, so its spread over samples is not defined.
- The P1 retrieval context mentions Phase 5 values, but the Phase 5 structured evidence is not in the Critic's model view, so neither method sees it, as in RQ3.
