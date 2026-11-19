# Critic-to-Revision mapping

Plan step 2. **Status: proposed, not frozen.** It becomes frozen when Ryiad
(Critic) and Alex (revision) both agree to it. The Critic report schema
(`critic-report/0.4.0`) is used exactly as it is. Nothing here asks for a
change to the Critic.

The mapping is executable: `drafter/revision/contract.py` implements every
rule below, and `python3 -m drafter.revision.tools.check_examples` checks it on
the saved examples (149 checks). The revision that consumes this mapping is
described in `README.md`.

## 1. What the revision side consumes

One wrapper, `drafter-revision-request/0.1.0`
(`schemas/revision_request.schema.json`):

| Field | Meaning |
| --- | --- |
| `schema_version` | Always `drafter-revision-request/0.1.0` |
| `critic_request`, `critic_request_sha256` | The exact `critic-request/0.3.0` object that was reviewed, and its canonical digest |
| `critic_report`, `critic_report_sha256` | The exact report returned for it, and its canonical digest |
| `finding_decisions` | Explicit decisions on findings that may not be acted on automatically |
| `synthetic_findings` | `present` and a `label`. Required when the report came from a scripted reply |
| `test_fixture` | Must equal the value in the Critic request and report |
| `round`, `max_rounds`, `history` | Bounded iteration. `history` has `round - 1` entries (section 7). Round `max_rounds + 1` is the final review and is never edited |
| `repair_invalid_evidence_links` | Optional, default false. See question 4 |
| `revision_id` | Caller's name for this revision |

Digests are `critic.contract.digest`: SHA-256 of canonical JSON, the same
function the Critic uses for `llm.request_sha256`.

Nobody converts fields by hand. The Critic request and report are embedded
unchanged and read with their own names.

## 2. Checks before any finding is read

`contract.request_issues(request)` returns every problem. Any problem means
the request is not used.

| Check | Issue code |
| --- | --- |
| Wrapper matches its schema | `schema:...` |
| Report matches `critic_report.schema.json` | `critic_report_schema:...` |
| Both digests recompute | `critic_request_digest_mismatch`, `critic_report_digest_mismatch` |
| Report was made by a compatible Critic version (`0.4.0` or `0.5.0`) | `critic_version_mismatch` |
| Report `request_id`, `execution_id`, `test_fixture` match the request | `report_request_id_mismatch`, `report_execution_mismatch`, `test_fixture_mismatch` |
| `llm.request_sha256`, when not null, equals the request digest | `report_request_hash_mismatch` |
| `input_valid` and `review_status` agree with a fresh run of the Critic input checks | `report_input_validity_mismatch`, `report_review_status_mismatch` |
| The report's `deterministic` criticisms equal a fresh rule-based run on the same request | `report_deterministic_findings_mismatch` |
| `checker_admission` equals a fresh recomputation | `report_checker_admission_mismatch` |
| A report with `llm.backend: scripted` carries the synthetic label | `scripted_report_requires_synthetic_label` |
| Every decision names a criticism in the report, once | `decision_for_unknown_criticism:...`, `duplicate_finding_decision` |
| `synthetic_test_label` decisions only under the synthetic label; `human_review` decisions name a reviewer | `synthetic_decision_without_synthetic_label:...`, `human_decision_requires_reviewer:...` |
| Round bookkeeping and history chain | `round_exceeds_max_rounds`, `history_length_must_equal_round_minus_one`, `history_round_sequence`, `history_revision_id_mismatch`, `history_chain_mismatch` |

The rule-based findings and the checker admission are recomputed, never
trusted from the report. A hand-written "deterministic" finding or a made-up
admitted checker result therefore fails here.

## 3. How each criticism field is used

| Report field | Use on the revision side |
| --- | --- |
| `criticism_id` | Key for decisions, dispositions and the diff. It is a position in one report (`CRIT-001`, ...), so it is always paired with the report digest and never compared across reports |
| `check_id` | Recorded. `LLM` marks a model-proposed finding |
| `critic_version` | Recorded |
| `phase` | `validation` findings are never revised: the input was invalid. Only `review` findings can be actionable |
| `category`, `category_name` | With `finding_source` and `check_id`, selects the kind of edit that is allowed (`README.md`) |
| `severity` | Recorded. Does not decide whether a finding is actionable |
| `blocking` | Recorded. A blocking finding that is not addressed stays in the output as unresolved |
| `object_id` | Must be a graph in the bundle. `null` with no node means the finding is about the execution conclusion |
| `node_id` | Must exist in that object's graph. With `object_id: null` it must exist in exactly one graph |
| `explanation` | Copied into the edit justification. Never parsed |
| `evidence_ids` | Each must be a registry record in the request or a checker assessment admitted by a fresh recomputation |
| `requirement_refs` | Recorded |
| `finding_source` | `deterministic` can be acted on without a decision. Anything else needs one |
| `suggested_action` | Advice for a reader. Never executed and never parsed as an instruction |
| `additional_evidence_needed` | When true, a revision may not add a Solution for it. The claim stays unresolved and the evidence request is carried forward |
| `human_review_required` | When true, the finding needs an explicit decision |

Other parts of the report:

| Report part | Use |
| --- | --- |
| `review_status` | `completed` and `completed_llm_failed` are usable. `rejected_invalid_input` and `internal_error` are not: nothing is revised |
| `rejected_llm_findings` | Never actionable. Listed in the output with the Critic's reason |
| `unresolved_concerns` | Carried to the output unchanged. Never turned into edits |
| `evidence_requests` | Carried to the output, still linked to their `criticism_id` |
| `checker_admission` | Only assessments with `admitted: true` after recomputation may support a contradiction fix |
| `structured_retrieval` | Context only |
| `summary` | Not used for decisions. In particular, `blocking_defects: false` is not read as "safe" |

## 4. When a criticism is actionable

`contract.classify(request)` gives each criticism one status, tested in this order:

| Status | When |
| --- | --- |
| `actionable_link_repair` | `phase` is `validation`, the request sets `repair_invalid_evidence_links`, and broken Solution citations are the only reason the input was rejected (question 4) |
| `not_actionable_validation_phase` | `phase` is `validation` otherwise |
| `not_actionable_report_unusable` | `review_status` is not usable |
| `not_actionable_target_missing` | The object or node does not exist, or a node without an object is in more than one graph |
| `not_actionable_unknown_evidence` | It cites an ID that is neither a record in the request nor an admitted assessment |
| `declined` | A decision says `declined` |
| `needs_human_decision` | `finding_source` is not `deterministic`, or `human_review_required` is true, and there is no decision |
| `actionable` | Everything else |

So a model-proposed finding that merely passed the Critic's screening is not
actionable. It needs a recorded `approved` decision, by a named reviewer
(`human_review`) or, in tests only, by `synthetic_test_label`.

Actionable means "a revision may try". The revision can still end with the
finding unresolved, for example when no admitted evidence supports any edit.

## 5. The examples

In `examples/`. Rebuild with `python3 -m drafter.revision.tools.build_examples`.
A scripted report records how long the scripted call took (`llm.latency_s`), so
a rebuild changes that number and the digests that depend on it. Each
`*.revision_request.json` has a `*.revision_result.json` next to it: what the
revision returns for it.

| File | What it shows | Expected classification |
| --- | --- | --- |
| `synthetic_actionable.revision_request.json` | Controlled-negative request. Since Critic 0.5.0 the rule `CLAIM-ABSOLUTE-SAFETY` raises the guarantee objection; the scripted model C12 on the same node is rejected as a duplicate. A `synthetic_test_label` decision approves the rule finding | `CRIT-001` is `actionable`, target node `cream_cheese_1:G1` |
| `synthetic_rejected_unresolved.revision_request.json` | Original request. A scripted reply with four findings, all rejected by the Critic: a node that does not exist, an invented evidence ID, a C09 that does not quote its target (kept as an unresolved concern), and a rule-only category | No criticism, 4 rejected candidates, 5 unresolved concerns, nothing actionable |
| `saved_zero_finding.revision_request.json` | The real saved Qwen report for the original request, unchanged | Nothing actionable. No change |
| `saved_zero_finding_controlled_negative.revision_request.json` | The real saved Qwen report (Critic 0.4.0) for the controlled-negative request, unchanged | Refused: `report_deterministic_findings_mismatch`, because Critic 0.5.0's rules find the guarantee the saved report missed |

The two synthetic reports are made by the real `critic.review` with
`ScriptedLLM`, so the Critic's own screening decided what was accepted. They
record `llm.backend: scripted`. They are test inputs, not model results.
The matching `*.critic_report.json` and `*.scripted_reply.json` files are the
same report and the reply text on their own, for the Critic side to load.

The last example matters most. The real Critic 0.4.0 run missed the guarantee,
and the revision still does not look for problems itself: it now refuses that
report because the current rules disagree with it. An empty report is not
evidence that R1 holds.

## 6. Questions for Ryiad

Update, Nov 18: Ryiad's completed work stays attributed to him, but he has no
new tasks, and Alex now maintains the Critic. These questions are therefore
for Alex to decide. They are kept here as they were asked.

1. **Decisions outside the report.** Approval of a model-proposed finding is
   recorded in `finding_decisions` in the revision request, so the Critic
   report schema stays untouched. Is that acceptable, or do you plan an
   approval field in the report?
2. **`evidence_grounded`.** The schema allows this `finding_source`, but no
   Critic code produces it. Until it is defined, it is treated like
   `llm_proposed` (needs a decision). Agreed?
3. **Deterministic findings marked `human_review_required`.** For example the
   C07 in case D and the C04 in case E. They need a decision before any edit.
   Agreed?
4. **Invalid input.** Evidence-link problems (`EV-MISSING`,
   `EV-WRONG-OBJECT`, ...) are `validation` phase, so the report is
   `rejected_invalid_input` and nothing is revised. The work plan also asks
   for repair of invalid evidence links. Proposal, implemented as an option
   that is off by default: "invalid input stops the revision" stays the rule.
   Only when the request sets `repair_invalid_evidence_links`, and every
   validation finding is a citation defect of one Solution node, may the
   revision remove that Solution. It never points it at another record. The
   proposed list is `contract.LINK_REPAIR_CHECKS`: `EV-MISSING`,
   `EV-WRONG-EXECUTION`, `EV-WRONG-OBJECT`, `EV-RELATED-CASE`,
   `EV-SCOPE-MISMATCH`, `EV-SOURCE-MISMATCH`, `EV-NO-INTERVAL`,
   `EV-INTERVAL-MISMATCH`, `EV-AUTHORITY`. Defects of a record itself
   (`EV-HASH`, `EV-SHAPE`, ...) are not on it. Do you accept this list?
5. **Re-criticism.** The revised request changes only `argument_bundle` and
   `request_id`. Proposed `request_id`: the first reviewed one plus
   `:rev<round>` (`engine.recriticism_request_id`). Any objection?
6. **Edited nodes.** An edited node gets revision provenance instead of the
   generation run's provenance (`edits.provenance`). Its origin is
   `unresolved_conclusion` for host template text and `llm_proposal` for text a
   model adapter proposed. The Critic input checks accept this today (the
   revision tests run them on every revised bundle). Will the Critic keep
   accepting it?
7. **Stale example.** `critic/examples/case_e_...rules_only.json` no longer
   matches a fresh run on `critic/cases/case_e_...json` (see the interface
   map, section 6). Can you regenerate it?

## 7. History and re-criticism

After a round that revised the bundle, the Critic reviews the revised request
and the next revision request carries one history item per earlier round
(`engine.history_item`, schema `$defs/history_item`):

| Field | Meaning |
| --- | --- |
| `round`, `revision_id` | Which round of which revision |
| `revision_request_sha256`, `result_sha256` | Digests of that round's request and result |
| `critic_request_sha256`, `critic_report_sha256` | What that round reviewed |
| `original_argument_bundle_sha256`, `revised_argument_bundle_sha256` | The bundle before and after |
| `recriticism_request_sha256` | Must equal `critic_request_sha256` of the next round |
| `addressed` | Check, category, object and node of every finding that round edited for |

If a later report raises a finding with the same category, object and node as
one in `addressed` of the previous round, the revision stops with
`repeated_unchanged_findings`. `criticism_id` is not used for this, because it
is only a position in one report. The check ID is not compared either, so a
model objection that repeats a rule objection at the same place counts as a
repeat (changed on Nov 18 for Critic 0.5.0, whose rule now raises the guarantee
objection that a model raised before).

The revision result and the cycle summary have their own schemas
(`revision_result.schema.json`, `revision_cycle.schema.json`). They are the
revision side's output and ask nothing of the Critic.
