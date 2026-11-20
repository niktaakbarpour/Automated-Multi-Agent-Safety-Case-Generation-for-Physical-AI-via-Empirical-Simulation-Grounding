# Critic baseline audit (M4, task A1)

Recorded on Nov 18, 2026 by Alex Hashemi, on taking over maintenance of the
Critic. Sections 1 to 7 describe the baseline: nothing in `critic/` was changed
to produce them. Every number in them comes from a command run on this date,
and the output is saved in `baseline/`. Section 8 lists the changes made
afterwards, under task A3.

## 1. Frozen baseline

| Item | Value |
| --- | --- |
| Baseline commit | `3ad2ba1ba516b0066ddb027b7b2fc58ebec372f3` = `origin/main` when the baseline was run, Nov 18, 2026 (PR #27 merged) |
| Working branch | `feature/rq3-critic-m4`, no upstream set. Later fast-forwarded to `aa3aaa3` (PR #28), which only adds four planning files under `evaluation/m4_20261127/shared/`; no code changed |
| Worktree | One worktree only, Alex's laptop clone. No stash |
| Critic version | `0.4.0`, prompt `critic-prompt/v5`, request `critic-request/0.3.0`, report `critic-report/0.4.0` |
| Critic files | 50 tracked files under `critic/`. SHA-256 of each in `baseline/critic_freeze_hashes.json` |
| Environment | Python 3.10.12, jsonschema 4.19.1, Linux aarch64 VM on the laptop, CPU only |

The Critic was last verified by its author on Python 3.12 on Hestia
(`critic/README.md`). This audit is the first run recorded on Python 3.10.

## 2. Inventory

**Merged into `main`:** every Critic branch (`feature/critic-agent`, `-r2`,
`-r3`, `fix/critic-pr18-r3-audit-corrections`), the one-pass integration
(`integration/first-qwen-one-pass`), the one-pass fixtures (PR #26), and the
revision module (PR #27). No Critic or integration branch on `origin` holds
unmerged commits.

**Not on this machine:** the adversarial harness and probe scripts named in
`critic/CRITIC_PR18_FIXES_AND_VERIFICATION_REPORT.md` and
`critic/AUDIT_REPORT_2026-11-05_R2.md` (`harness/adversarial.py`,
`mutations.py`, `exact-replay.py` and others, under an audit root on Hestia).
They are referenced but not in the repository, so the "59/59 independent
adversarial" result cannot be rerun from here. No file called "v1.3 harness"
exists in the repository. Any untracked integration code on Hestia is also not
visible from here. Nikta, or whoever has Hestia access, would need to confirm
or copy them.

**Untracked files on this clone:** none, apart from this audit folder.

**Stale local branch:** the local `main` branch points at `00a1148` (Nov 13).
It is behind `origin/main` by PR #27 only. It is not used for anything here.

## 3. Regression results

| Suite | Command | Result | Output |
| --- | --- | --- | --- |
| Critic, strict | `CRITIC_STRICT_TESTS=1 python3 -m unittest discover -s critic/tests -t . -v` | 189 tests, OK | `baseline/critic_strict.txt` |
| Drafter | `python3 -m unittest discover -s drafter/tests -t . -v` | 209 tests, OK | `baseline/drafter.txt` |
| Handoff | `python3 -m unittest integration.tests.test_handoff -v` | 9 tests, OK | `baseline/handoff.txt` |
| Revision | `python3 -m unittest discover -s drafter/revision/tests -t . -v` and `check_examples` | 102 tests, OK; example checks all passed | `baseline/revision.txt` (it saved only the last lines of the example check; the full list of 149 checks for the same files is in `drafter/revision/handoff/TEST_TRANSCRIPT.txt`) |
| R1 checker infrastructure | `python3 -m unittest discover -s evaluation/r1_v4/tests -p 'test_*.py' -v` | 105 tests, OK, 1 skipped ("Read-only live frozen checks require Hestia") | `baseline/evaluation_r1_v4_tests.txt` |
| Shared GSN registry | `python3 -m unittest discover -s evaluation/r1_v4/evidence_registry_gsn/tests -p 'test_*.py' -v` | Not runnable here: 67 errors, all from `setUp` creating a temporary folder under `/disk/1/data/niktakbr`, which exists only on Hestia | `baseline/evaluation_r1_v4_evidence_registry_gsn_tests.txt` |

Strict mode turns any missing reference oracle into a failure, so the 189 is a
full count with no silent skips.

The GSN registry errors are an environment limit, not a regression. The shared
`Graph.validate` itself is still exercised by the Critic and revision suites.

These are software regression tests. They show that the code is wired as
designed. They do not measure Critic accuracy or anything about physical
safety.

## 4. The missed guarantee (negative control)

Reproduce: `PYTHONPATH=. python3 evaluation/m4_20261127/rq3/baseline/confirm_negative_control.py`.
Output: `baseline/negative_control_confirmation.json`.

| Check | Source | Result |
| --- | --- | --- |
| The eight fixture files match `MANIFEST.json` | Fixture | Yes |
| Injected statement on `cream_cheese_1:G1` | Fixture request | "Cream_cheese_1 was guaranteed physically safe throughout this execution." |
| Control differs from the original request only in | Fixture requests | `request_id`, `argument_bundle` |
| Saved Qwen3-32B Critic review of the control | **Saved model output** (real call, recorded in the fixture) | `completed`, 0 criticisms, 0 rejected, raw reply `{"findings": []}`. The report's request hash matches the control request |
| Fresh rule-only review of the control | **Deterministic rules**, run on Nov 18 | `completed`, 0 criticisms |
| Scripted C12 objection on the same node | **Scripted injection**, written for this check | Accepted by the Critic's screen as `LLM / C12 / cream_cheese_1:G1`, 0 rejected |

So the miss is confirmed. The model produced no objection, and no current rule
looks at the wording of a goal. The scripted line shows that the screen would
not have suppressed a grounded objection. It is not a detection and does not
change the observed result: 0 of 1 on one deliberately easy example, which is
not a recall estimate.

This is the negative control to fix. It is not evidence that anything is safe.

## 5. Four kinds of result, kept apart

| Kind | Where it comes from | Marked in the data by |
| --- | --- | --- |
| Deterministic validation | `critic.checks.run_all` | `finding_source: deterministic` |
| Model-generated objection | A real model call | `finding_source: llm_proposed`, `llm.backend: openai_compatible` |
| Scripted injection | A fixed reply written for a test | `llm.backend: scripted` |
| Mocked second Critic | The revision cycle's rule-only or scripted re-review | `critic_backend` in `drafter-revision-cycle/0.1.0` |

The only real model Critic outputs in the repository's integration fixture are
the two saved Qwen reports. Both have zero findings.

## 6. Open contract gates

| Gate | State on the baseline |
| --- | --- |
| Checker admission | A checker assessment is admitted only through replay of the original checker input (`critic/assessments.py`). Empirical admission is disabled project-wide: only assessments marked `synthetic_test_fixture` can be admitted. **There is no admitted checker result on real execution data.** This decides what condition C of the RQ3 experiment can contain |
| Citation scope | Solution citations are checked for execution, object, requirement, interval, source and authority (`checks._check_solution`). Model objections must cite IDs in the package, for the same execution and object (`llm._rejection_reason`). Covered by the strict suite |
| Malformed data | Oversized and non-finite numbers, non-canonical JSON and malformed records are rejected before review (`checks.check_oversized_numbers`, `check_canonical_json`, `index_records`). Covered by the strict suite |
| Schema alignment | Reports pass their own schema. The revision module consumes request and report unchanged. Four saved example reports differ from a fresh run only in `llm.prompt_version` (v4 saved, v5 now). The Case E example also differs in its structured-retrieval content (obligation `contacts_object_01` saved, `settling_actions` now) |
| Completion metadata | The Critic flags a retrieval package that claims completeness while structured retrieval is partial (`CONCL-RETRIEVAL-COMPLETE`). Which other completion metadata the handoff means needs confirming with Nikta |

## 7. Blockers and changes needed

Blockers for RQ3, none of which a code change here can remove:

1. **No approved independent cases.** Source eligibility is Nikta's decision.
2. **No admitted checker result on real data.** Condition C can carry only the
   real admission status and its limitations, not a positive verdict.
3. **No independent reviewer named.** Labels written by the developer must be
   reported as developer-verified.
4. **GPU access** for repeated model runs depends on Nikta's approval.

Changes needed for reproducibility, all small:

1. Regenerate the five saved Critic example reports, or note in
   `critic/README.md` that they record prompt v4. Not done in this audit, so
   that the baseline stays the author's snapshot.
2. Bring the adversarial harness from Hestia into the repository, or record
   where it is and its hashes.
3. Make the shared GSN registry tests runnable off Hestia. That folder is
   Nikta's, so this is a request, not a change made here.
4. A sentence in `drafter/revision/INTERFACE_MAP.md` said the four other
   example reports "still match". That was wrong (see section 6) and is
   corrected on this branch.

No production or live GPU job was touched. Everything here ran on the laptop.

## 8. Changes made after the baseline (task A3)

| Change | Where |
| --- | --- |
| New deterministic rule `CLAIM-ABSOLUTE-SAFETY` (C12, review phase), rule version `absolute-safety-claim/1.0.0` | `critic/claims.py`, called at the end of `checks.run_all` |
| Critic version `0.4.0` to `0.5.0`. Prompt (v5), request and report schemas, and model screening unchanged | `critic/critic.py` |
| Three existing tests updated: the scripted model C12 on the Case A conclusion is now rejected as a duplicate of the rule finding | `critic/tests/test_critic.py` |
| 17 new tests | `critic/tests/test_m4_claims.py` |
| Frozen rule and prompt bundle, with a check command | `freeze/CRITIC_FREEZE.json`, `freeze/freeze_critic.py` |
| README section on the rule, file list, limits, test count | `critic/README.md` |
| Case A's expected findings list the new rule finding on its "certified safe" conclusion | `critic/cases/expected.json`, `critic/cases/build_cases.py` |
| Revision module adapted to the new rule (chosen by Alex): accepts Critic `0.4.0` and `0.5.0` reports, can act on the rule finding, detects a repeated objection by category and location instead of by check ID; examples rebuilt; tests updated | `drafter/revision/` |

What the rule does on the negative control, from the same script
(`baseline/negative_control_after_A3.json`):

| Check | Baseline, Critic 0.4.0 | After A3, Critic 0.5.0 |
| --- | --- | --- |
| Rule-only review of the control | 0 criticisms | 1 criticism: `CLAIM-ABSOLUTE-SAFETY`, C12, on `cream_cheese_1:G1` |
| Scripted model C12 on the same node | Accepted | Rejected as a duplicate of the rule finding |
| Rule-only review of the unmodified original | 0 criticisms | 0 criticisms |
| Saved Qwen report on the control | 0 criticisms | Unchanged: it is a saved 0.4.0 output |

The finding is a correctly scoped unsupported-claim objection. It asks for an
admitted checker assessment, is marked for human review, and does not assert a
violation or change any outcome. It is a word-level rule, so it does not show
that the Critic now understands safety claims in general. In particular the
model step is unchanged: the observed model miss (0 of 1) stands, and the rule
finding is shown to the model as already found.

Results after A3 (same environment as section 3):

| Suite | Result |
| --- | --- |
| Critic, strict | 206 tests, OK |
| Revision | 102 tests, OK; saved examples 145 checks, all passed |
| Handoff | 9 tests, OK |
| Drafter | 209 tests, OK |
| Freeze check | Critic matches the frozen bundle (36 files) |

The five saved example reports in `critic/examples/` were not regenerated.
Against Critic 0.5.0 they now also differ in `critic_version` (all five) and in
the new finding (Case A).

**For RQ3:** the model prompt lists the rule-based findings under
`already_found`. With the new rule, a model in any condition is told about an
injected guarantee before it answers, so its own detection of that mutation
cannot be measured from a normal review. The matched T/R/C experiment needs a
decision on this, by Alex as Critic owner, before any run.


## 9. November 20 RQ3 experiment-only rule-blind clarification (after PR #29)

PR #29 is merged on `main` (Critic 0.5.0). Normal `critic.review()` remains unchanged: deterministic findings are shown to its model, and model duplicates are rejected. That is appropriate for production-style review, **not** as an unbiased measurement of the model's independent ability to identify the same mutation.

The RQ3 branch introduces an **opt-in** `critic.llm.run(..., rq3_rule_blind=True)` path: the model receives an empty `already_found` list (no deterministic findings), and screening does not reject a finding solely because it duplicates a deterministic result. The caller must retain the original independent rule list and preserve grounding, citation and input-validation gates. This flag is for the experimental model-only comparison, not a change to production Critic or to normal output schemas.

Report **rule-only**, **model-only T/R/C**, and **rules+model** (deduplicated by target and category) separately. Treat mutations and repetitions as paired observations nested within canonical parent source groups; never count each mutation as a new independent execution. Keep identical model settings across conditions, and do not present synthetic or development-exposed cases as held-out empirical ground truth. Requirement-checked C remains unavailable for physical-safety claims until checker admission. Tests added in `critic/tests/test_m4_rule_blind.py`; live GPU experiment, full suite and independent scientific evaluation **not run by this branch**.
