# Revision track: handoff manifest (M4 milestone A0)

Closes the Nov 13 to 16 individual assignment with evidence. Recorded on
Nov 16, 2026 (Nov 17 UTC). Everything below was read from the repository or
produced by running it on that date.

## 1. Where the work is

| Item | Value |
| --- | --- |
| Branch | `feature/drafter-revision` (pushed to `origin`) |
| Delivered commit | `597851114c92de51f63db84306b09ada857ad99e`, Nov 14, 2026, "Add bounded GSN revision module with tests, schemas and examples" |
| Based on | `main` at `00a1148` (fixture PR #26 merged) |
| Changed files in that commit | 44 added, 0 modified, 0 deleted. All under `drafter/revision/` (18,367 lines, most of them saved JSON examples) |
| Added after that commit | This `handoff/` folder, `examples/invalid/` (5 invalid payloads with results), one new test class, and the `--invalid-only` option of the example builder |
| Pull request | Not opened when this was recorded. Add the link here |

The M4 handoff names `integration/revision.py` and
`integration/tests/test_revision.py`. Those files do not exist on `main` at
`00a1148`. The revision code is the package `drafter/revision/`. If the team
wants it under `integration/`, that is a move of one package and a change of
import paths, with no change of behaviour.

`00a1148` is `main` as last fetched on Nov 14. Later changes to `main` were not
visible when this was recorded.

## 2. Test commands and results

CPU only. No model, no network. Python 3.10.12, jsonschema 4.19.1. Run from the
repository root. Full output is in `TEST_TRANSCRIPT.txt`.

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s drafter/revision/tests -t . -v` | 102 tests, OK |
| `python3 -m drafter.revision.tools.check_examples` | 149 checks, all passed, exit code 0 |
| `python3 -m unittest integration.tests.test_handoff -v` | 9 tests, OK |
| `python3 -m unittest discover -s drafter/tests -t . -v` | 209 tests, OK |
| `python3 -m unittest discover -s critic/tests -t . -v` | 189 tests, OK |

No test failed, errored or was skipped in any of the five runs.

## 3. One reproducible example

Original GSN, accepted Critic finding, proposal, validated revision, node-level
diff and stop reason, on saved inputs:

```bash
python3 -m drafter.revision revise \
  --request drafter/revision/examples/synthetic_actionable.revision_request.json \
  --out /tmp/revision_result.json \
  --out-bundle /tmp/revised_bundle.json \
  --out-diff /tmp/revision_diff.json
python3 -m drafter.revision verify \
  --request drafter/revision/examples/synthetic_actionable.revision_request.json \
  --result /tmp/revision_result.json
```

| Part | Where |
| --- | --- |
| Original GSN | The fixture's `critic.controlled-negative.request.json`, embedded unchanged in the request |
| Critic finding | One C12 finding on `cream_cheese_1:G1`. It is a **labelled synthetic** finding: the real Critic screened a scripted reply. It is not a model result |
| Decision | `synthetic_test_label` approval, recorded in `finding_decisions` |
| Proposal | From the deterministic template adapter (`proposal` in the result) |
| Revised graph | `revised_argument_bundle` in the result. 1 of 20 nodes changed |
| Diff | `diff`: one `node_replaced` entry with the node before and after and both digests |
| Validators | 8, all passed |
| Stop reason | `null` for the round, because the next step is re-criticism. The full cycle ends with `no_actionable_findings` |

The saved result is `examples/synthetic_actionable.revision_result.json`. The
commands above reproduce it exactly.

The other outcomes, on saved inputs:

| Outcome | Request |
| --- | --- |
| No change (real saved Qwen report, zero findings) | `examples/saved_zero_finding_controlled_negative.revision_request.json` |
| Unresolved (finding names a node that does not exist) | `examples/invalid/unknown_node.revision_request.json` |
| Rejected (foreign execution) | `examples/invalid/foreign_execution.revision_request.json` |
| Two-round cycle | `python3 -m drafter.revision cycle --request drafter/revision/examples/synthetic_actionable.revision_request.json --out-dir /tmp/revision_cycle`, and the saved `examples/two_round_cycle/` |

No command writes to the fixture or to any frozen evidence.
`check_examples` confirms the eight fixture files still match `MANIFEST.json`.

## 4. Where proposals come from

| Source | Used here | Label in the data |
| --- | --- | --- |
| Deterministic host templates | Yes. The default adapter | `adapter.kind: deterministic` |
| Scripted proposal (fixed reply written for a test) | Yes, in tests only | `adapter.kind: scripted` |
| Saved LLM response | No | |
| Live model | No. Not run for anything in this track | `adapter.kind: model` is reserved for it |

Critic findings come from three sources, also kept apart in the data:

| Source | Used here | Label |
| --- | --- | --- |
| Critic rule checks | Yes | `finding_source: deterministic`, `llm.backend: none` |
| Scripted Critic reply, screened by the real Critic | Yes, for every positive revision example | `llm.backend: scripted` and `synthetic_findings.present: true` |
| Real saved Qwen report | Yes. Zero findings, so no change | `llm.backend: openai_compatible`, `synthetic_findings.present: false` |

This is a CPU-validated revision workflow with template and scripted
proposals. It is not a live autonomous Revision Agent, and nothing here
measures model revision quality.

## 5. Status of each subfeature

**Implemented and tested**

- Revision request contract: schema, digests, report-to-request binding, rule
  findings and checker admission recomputed instead of trusted
- Classification of every finding (actionable, needs decision, declined,
  target missing, unknown evidence, validation phase, report unusable)
- Five kinds of edit: replace a statement, add an unresolved claim, remove a
  broken Solution, set an object outcome, recompute the execution outcome
- Deterministic template adapter and scripted adapter
- Seven post-edit validators, including the shared `gsn.Graph.validate` and the
  Critic input checks. A failed validator discards the bundle
- Node-level diff, disposition for every finding, edit justification, metrics
- Bounded cycle with eight stop reasons, digest-chained history, resumable
- Replay of a saved result (`verify`)
- Command line, three JSON schemas, saved examples (valid, no-change, rejected
  candidates, two-round cycle, five invalid payloads)

**Implemented, tested only with stand-ins**

- The adapter interface for a model. Tested with scripted proposals, including
  malformed and hostile ones. No model was attached
- The hook for live re-criticism (`run_cycle(review=...)`). Tested with the
  Critic rules, scripted replies, and a failing function

**Designed, not implemented**

- RQ4 metric definitions and scorer (M4 milestone A4). A draft specification
  exists outside the repository
- Moving the package under `integration/`, if the team wants that

**Proposed, waiting for agreement**

- The Critic-to-Revision mapping. `CRITIC_TO_REVISION_MAPPING.md` has seven
  questions for Ryiad in section 6. No signoff is recorded in the repository

**Not implemented, by decision**

- Pointing a Solution at a different admitted record, or adding any evidence
  link. The module only removes a broken citation
- Resolving conflicting admitted checker assessments
- Re-issuing a `draft-argument/0.1.0` envelope for a revised bundle

**Blocked on others**

- Model-generated proposals and live re-criticism: need approved inference
- `drafter.validation.validate_argument` on the saved argument: the fixture
  does not contain the Drafter request of that run
- Any measured revision correctness: needs independent human labels and
  approved, held-out cases

## 6. Compatibility notes

- Consumes `critic-request/0.3.0` and `critic-report/0.4.0` unchanged, with
  Critic `0.4.0`. A report from another Critic version is refused
  (`critic_version_mismatch`).
- The re-criticism request differs from the reviewed one only in
  `argument_bundle` and `request_id`. The real Critic command line accepts it.
- A bundle revised from Drafter output still matches the Drafter's bundle
  schema. A bundle whose outcome was corrected to an admitted checker result
  does not, because that schema allows only `insufficient_information`.
- An edited node carries revision provenance, so
  `drafter.validation.validate_argument` would not accept it. That validator
  stays the one for unrevised drafts.
- Python 3.10 or later, because the shared `gsn.py` needs it.

## 7. Bug and limitation register

Open bugs known in the revision code: none.

Found and fixed before the delivered commit:

| # | Problem | Found by | Fix |
| --- | --- | --- | --- |
| 1 | `revise` raised for an adapter that declares no name, version or kind | Test | Returns a `failed` result. Test added |
| 2 | The host-written execution statement could be false when only some outcomes were corrected | Review of host texts | All host texts now describe only the argument. Tests updated |
| 3 | Tests did not notice three guards being switched off | Switching off 24 guards one at a time | Ten tests added. All 24 are now caught |

Found in other components, not changed:

| # | Problem | Owner |
| --- | --- | --- |
| 4 | `critic/examples/case_e_partial_structured_retrieval.report.rules_only.json` does not match a fresh Critic run on its case | Critic |
| 5 | The one-pass fixture lacks the Drafter request (`PR20-complete`) | Integration |

Limitations are listed in `README.md`, section "Known limitations". The ones
that matter most for claims:

- No live model was used. Positive behaviour is shown on labelled synthetic
  findings only.
- New text is screened by a word list, not by meaning. A sentence such as "it
  never fell" would pass the screen. Text from a model adapter is marked
  `prose_review: required` and needs review.
- A rule-only second review cannot raise a model-proposed finding, so its
  silence does not show that such a finding is fixed.
- Passing every validator is structural acceptance. It does not show that a
  statement is true or that R1 holds.
