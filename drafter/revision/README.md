# Drafter revision

A bounded, auditable revision step for the GSN argument. It takes the Critic
request that was reviewed, the Critic report for it, and explicit decisions on
findings. It returns a validated revised argument bundle, or an explicit
no-change, unresolved or rejected result.

It revises arguments, not physical reality. It never changes the R1
configuration, the evidence, the checker results or the stored inputs, and it
never adds a Solution. It acts only on findings the contract calls actionable.
It does not look for problems itself, so an empty Critic report gives "no
change", which is not evidence that R1 holds.

Status: the Critic-to-Revision mapping is proposed and waits for Ryiad's
confirmation (see `CRITIC_TO_REVISION_MAPPING.md`, section 6). The code runs
against that proposal. Nothing in `drafter/`, `critic/`, `integration/` or the
shared GSN code was changed.

## Run it

CPU only. No model, no network. Python 3.10 with `jsonschema` (already in
`drafter/requirements.txt`). All commands run from the repository root.

One round on the labelled synthetic finding, with the revised graph and the
diff written out:

```bash
python3 -m drafter.revision revise \
  --request drafter/revision/examples/synthetic_actionable.revision_request.json \
  --out /tmp/revision_result.json \
  --out-bundle /tmp/revised_bundle.json \
  --out-diff /tmp/revision_diff.json
```

The real saved zero-finding Qwen report, which must give no change:

```bash
python3 -m drafter.revision revise \
  --request drafter/revision/examples/saved_zero_finding_controlled_negative.revision_request.json
```

A full cycle (revise, re-criticise with the Critic rules, repeat):

```bash
python3 -m drafter.revision cycle \
  --request drafter/revision/examples/synthetic_actionable.revision_request.json \
  --out-dir /tmp/revision_cycle
```

Build a request from your own Critic request and report, then check a saved
result:

```bash
python3 -m drafter.revision build-request --critic-request REQUEST.json \
  --critic-report REPORT.json --revision-id my-run --out /tmp/revision_request.json
python3 -m drafter.revision verify --request /tmp/revision_request.json --result /tmp/revision_result.json
```

Exit codes: 0 revised or no change, 1 unresolved (nothing changed), 3 request
not usable, 5 adapter or module failure, 6 unreadable file.

## Tests

```bash
python3 -m unittest discover -s drafter/revision/tests -t . -v     # 102 tests
python3 -m drafter.revision.tools.check_examples                   # 149 checks on the saved examples
python3 -m unittest discover -s drafter/tests -t . -v              # existing Drafter suite, 209 tests
python3 -m unittest integration.tests.test_handoff -v              # existing handoff suite, 9 tests
```

Core scenarios in `tests/test_core.py` and `tests/test_cycle.py`:

| # | Scenario | Test class |
| --- | --- | --- |
| 1 | Unsupported guarantee is replaced by the unresolved wording | `UnsupportedGuarantee` |
| 2 | Missing support gets an explicit unresolved claim, never a Solution | `MissingSupport` |
| 3 | Invalid evidence link is removed, only when asked | `InvalidEvidenceLink` |
| 4 | Outcome that contradicts an admitted synthetic checker result is corrected to that result | `CheckerContradiction` |
| 5 | Cautious no-change on the real saved zero-finding reports | `CautiousNoChange` |
| 6 | Claim beyond the evidence becomes `insufficient_information`; evidence requests stay open | `InsufficientInformation` |
| 7 | Repeated finding stops the cycle | `Cycles.test_repeated_finding_stops_the_cycle` |
| 8 | Two-round cycle with complete history | `Cycles.test_two_round_synthetic_cycle_ends_with_complete_history` |

Invalid-input cases are in `tests/test_invalid.py`: wrong object, foreign
execution and variant, altered R1 version, fabricated Solution, nonexistent
node, malformed schema, attempted loss of provenance, fabricated checker
verdict and more. Each is tried at three layers: as input, as an adapter
proposal, and as a revised bundle or saved result changed by hand.

## Contracts

| What | Version | Schema |
| --- | --- | --- |
| Request | `drafter-revision-request/0.1.0` | `schemas/revision_request.schema.json` |
| Result of one round | `drafter-revision-result/0.1.0` | `schemas/revision_result.schema.json` |
| Cycle summary | `drafter-revision-cycle/0.1.0` | `schemas/revision_cycle.schema.json` |

Consumed unchanged: `critic-request/0.3.0`, `critic-report/0.4.0`, GSN `1.0.0`.

Python entry points (`drafter.revision.engine`):

```python
from drafter.revision import contract, engine

request = contract.build_request('my-run', critic_request, critic_report,
                                 finding_decisions=[...], max_rounds=2)
result = engine.revise(request)                      # one round, never raises
next_critic_request = engine.recriticism_request(request, result)   # when result['outcome'] == 'revised'
run = engine.run_cycle(request, review=my_review)    # rounds with re-criticism
issues = engine.verify_result(request, result)       # [] when the saved result holds
```

## What one result contains

- `outcome`: `revised`, `no_change`, `unresolved`, `rejected_invalid_input` or `failed`
- `stop_reason`: why nothing more happens; `null` only when revised (next step: re-criticism)
- `revised_argument_bundle` and its digest, only when revised
- `edits`: the applied edits, each with its finding IDs and a justification
- `diff`: node-level, with the whole node before and after and both digests
- `dispositions`: one entry for every criticism: `edited`, `unresolved` or `not_actionable`, with the reason
- `carried_forward`: rejected candidates, evidence requests and unresolved concerns, unchanged
- `validators`: every check that ran and its issues
- `manual_review_decisions` and `metrics` (nodes changed, findings addressed and remaining,
  evidence links removed, new rule findings, iteration)
- `proposal`: exactly what the adapter answered, so the result can be replayed

## What a revision may change

An adapter proposes edits. The host checks each one and writes the nodes and
their provenance itself. There are five kinds of edit and nothing else:

| Edit | Allowed for | Effect |
| --- | --- | --- |
| `replace_statement` | An approved model-proposed finding (C05 to C10, C12, C13) on a node that is not a Solution | New statement. Type, scope, interval, status and evidence ID stay |
| `add_unresolved_claim` | Rule finding `GSN-UNSUPPORTED-GOAL` | An unresolved claim under that goal or strategy, with the parent's scope |
| `remove_solution` | Broken citations, only with `repair_invalid_evidence_links: true` | The Solution and its edges are removed. Nothing is cited instead. A parent left without support gets an unresolved claim |
| `set_object_outcome` | Rule findings about one object's claimed outcome (`CONCL-...`) | `insufficient_information`, or the outcome of a freshly admitted checker assessment. An admitted violation cannot be replaced |
| `recompute_execution_outcome` | Rule finding `CONCL-AGGREGATION` | R1 aggregation of the object outcomes |

When an outcome changes, the host recomputes the execution outcome and writes
the conclusion statement itself.

An edited node keeps its ID, type, scope and status. It gets revision
provenance (revision ID, round, finding IDs, Critic report digest, adapter, and
the digest of the node it replaces) instead of the generation run's
provenance, because the generation run did not write the new text. The
original node stays in the diff.

## What is checked

Before anything is read from the report (`contract.request_issues`): schemas,
digests, that the report belongs to the request, and that its rule findings
and checker admission equal a fresh run. A forged "deterministic" finding fails
here.

After the edits are applied, all of these must pass or the bundle is discarded
and the original is kept:

| Validator | What it shows |
| --- | --- |
| `frozen_inputs` | R1 configuration and digest, requirement version, execution, task, variant, object order, interval, evidence, checker results and retrieval context are untouched |
| `diff_rules` | Every change is traced to an edit with a finding and a justification, and is a kind of change a revision may make |
| `critic_input_checks` | The revised request passes the Critic input checks |
| `no_new_rule_findings` | The revised bundle has no rule finding the original did not have |
| `cited_rule_findings_cleared` | Every rule finding an edit cites is gone |
| `shared_gsn_validator` | `gsn.Graph.validate` accepts every revised graph |
| `drafter_structure_rules` | No new issue from `drafter.argument_checks.graph_structure_issues` |

Passing these checks is structural acceptance. None of them shows that a
statement is true or that R1 holds.

## Stop reasons

| Stop reason | When |
| --- | --- |
| `no_actionable_findings` | The report has no criticism, or none that may be acted on |
| `awaiting_decision` | A finding needs an explicit decision and has none |
| `no_justified_improvement` | Actionable findings exist, but no edit could be justified, or an edit was refused, or the edited bundle failed validation |
| `insufficient_evidence` | The adapter declined for lack of evidence, or a finding cites evidence that is not in the package |
| `invalid_input` | The request or the Critic report is not usable |
| `repeated_unchanged_findings` | The Critic raised again a finding the previous round edited for |
| `round_limit` | Actionable findings remain after `max_rounds` revision rounds |
| `execution_failure` | The adapter, the re-criticism or this module failed. Nothing was applied |

`max_rounds` defaults to 2. That is an engineering choice for the pilot, not a
scientific requirement. Round `max_rounds + 1` is the final review of the last
revised bundle: it is reported and never edited.

One refused edit means no edit of that round is applied.

## Live inference

`run_cycle(request, review=...)` takes any function that maps a Critic request
to a Critic report, so live re-criticism is one argument. The default is the
Critic rules only. A rule-only review cannot raise a model-proposed finding, so
it also cannot show that one is gone. `critic_backend` in the cycle summary
says how each report was made.

A model that proposes edits is an adapter: an object with `name`, `version`,
`kind = 'model'` and `propose(context)` returning `{'edits': [...], 'declined':
[...]}` (see `adapters.py`). The host treats it as untrusted, like the scripted
adapter in the tests.

## Examples

`examples/` is rebuilt by `python3 -m drafter.revision.tools.build_examples`. A full
rebuild changes the digests that depend on the scripted call time, so rebuild
only `invalid/` (`--invalid-only`) unless the valid examples must change.
The handoff manifest and the test transcript are in `handoff/`.

| File | What it shows |
| --- | --- |
| `synthetic_actionable.*` | The complete example: original argument, labelled synthetic C12 finding, revised graph, validator results and edit log (`.revision_result.json`) |
| `synthetic_rejected_unresolved.*` | Four candidates the Critic rejected: no change, all carried forward |
| `saved_zero_finding.*`, `saved_zero_finding_controlled_negative.*` | The real saved Qwen reports: no change. Not labelled synthetic |
| `two_round_cycle/` | A two-round synthetic cycle. Request 1 and its result are the `synthetic_actionable` files |
| `invalid/` | Five invalid payloads with the result each must give (`EXPECTED.json`): foreign execution, unknown node, non-admitted assessment, malformed history, schema-invalid report |

## Known limitations

- The mapping to the Critic report is proposed, not frozen. Open points:
  where decisions are recorded, provenance of edited nodes, the re-criticism
  request ID, and the list of citation defects that link repair may act on
  (`contract.LINK_REPAIR_CHECKS`).
- Link repair only removes a broken citation. It does not point a Solution at
  another record, because nothing in a report says which record would be the
  right one.
- The deterministic adapter rewords only goals and unresolved claims with
  overclaim findings (C05, C06, C12). Other approved wording findings stay
  unresolved unless a model adapter proposes text.
- New text is screened for assurance words (guarantee, certified, proves,
  safe). This is a word list, not a check of meaning. It also refuses negated
  uses.
- Conflicting admitted checker assessments are never resolved here. The outcome
  can only become `insufficient_information`, or stays a reported violation.
- The output is a revised argument bundle and a Critic request for it. It is
  not a new `draft-argument/0.1.0` envelope: `drafter.validation.validate_argument`
  requires every reasoning node to carry the generation run's provenance, which
  an edited node must not claim. The fixture also lacks the Drafter request, so
  that validator could not be run on the saved argument.
- The Drafter's bundle schema (`draft_argument.schema.json`) allows only
  `insufficient_information` as an outcome. A bundle revised from Drafter
  output still matches it. A bundle whose outcome was corrected to an admitted
  checker result (core case 4) cannot, so that schema is not one of the
  blocking validators. The team should decide where a checker-based outcome
  may be reported.
- `gsn.Graph.validate` is run with read-only views of the request's records
  rather than `Record.parse`, which refuses the synthetic source paths of
  labelled test fixtures. The records are validated by the Critic input checks.
  Graphs above 24 nodes or 80 edges are not sent to the shared validator, the
  same bound the Drafter uses.
- A repeated finding stops the cycle even if other new findings could still be
  answered.
- No live model was used for anything here. Positive revision behaviour is
  shown on labelled synthetic findings only.
