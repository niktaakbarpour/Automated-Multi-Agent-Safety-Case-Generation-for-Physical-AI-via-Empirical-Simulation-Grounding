# Revision interface map

Plan step 1. Written against `main` at `00a1148` (fixture PR #26 merged), on
branch `feature/drafter-revision`. Checked with Python 3.10.12 and
jsonschema 4.19.1. Every entrypoint, count and digest below was read from the
code or produced by running it, not copied from another report.

## 1. The existing path, from Drafter input to Critic report

| Step | Entrypoint | Where |
| --- | --- | --- |
| Validate a Drafter request | `drafter.validation.validate_request(request)` | `drafter/validation.py:160` |
| Generate one draft | `drafter.generation.generate_argument(request, config)` | `drafter/generation.py:169` |
| Turn the model plan into GSN | `drafter.generation._serialize_plan(plan, request, provenance)` | `drafter/generation.py:67` |
| Validate a draft envelope | `drafter.validation.validate_argument(argument, request)` | `drafter/validation.py:289` |
| Validate the argument bundle | `drafter.validation.validate_argument_bundle(bundle, request)` | `drafter/validation.py:349` |
| Drafter structural rules | `drafter.argument_checks.graph_structure_issues(graph, object_id)` | `drafter/argument_checks.py:67` |
| Shared GSN rules | `gsn.Graph.validate(registry)` | `evaluation/r1_v4/evidence_registry_gsn/gsn.py:33` |
| Drafter to Critic handoff | `integration.handoff.build_critic_request(draft_request, generation_report)` | `integration/handoff.py:9` |
| Critic input checks | `critic.checks.run_all(req)` returns `(findings, info)` | `critic/checks.py:1099` |
| Critic review | `critic.review(request, llm=None)` returns a report | `critic/critic.py:16` |

Command lines: `python3 -m drafter` (`--validate-request`, `--mock-demo`,
`--generate`, `--adapt-phase5`, `--prepare-registry`) and
`python3 -m critic --request FILE [--backend none|openai|scripted]`.

`generate_argument` makes one model attempt, with no retry and no repair.
`build_critic_request` copies the bundle, the full R1 configuration, the
registry records, the checker entries and the Phase 5 pairs without changing
them, then runs the Critic input checks. Its sidecar says
`automatic_revision: false`. No revision code exists on `main`.

## 2. What the current validators guarantee

Versions in force: R1 `2.0.0`, configuration schema `2.0.1`, shared GSN `1.0.0`,
registry record `1.0.0`, `drafter-request/0.1.0`, `draft-argument/0.1.0`,
Drafter prompt `0.2.2`, serializer `graph-plan-to-gsn/0.2.0`,
`critic-request/0.3.0`, `critic-report/0.4.0`, Critic `0.4.0`, Critic prompt `v5`.

`Graph.validate` (shared, reusable without a Drafter request):

- node types, origins and statuses come from fixed lists; every node needs
  provenance and a requirement, version, execution and object scope
- a goal or unresolved claim can only be `proposed` or `unresolved`, and a
  physical claim must be `unresolved`
- a Solution must cite a registered record and copy its source path, hash,
  selector, interval, clock, scope, origin and status
- an evidence ID is allowed only on a Solution
- edges must join existing nodes of the right types, stay in one scope and
  inside the parent interval, with no duplicate and no cycle

`graph_structure_issues` (Drafter, reusable without a Drafter request): one
unparented physical root goal, every node reachable from it, node IDs prefixed
with the object ID, a strategy and a context, each strategy supporting a
subclaim, and usable prose (8 to 1600 characters, at least two distinct words).

`validate_argument` and `validate_argument_bundle` (need the Drafter request):
they bind the envelope to the request, configuration and evidence digests,
require the exact object roster and order, require every outcome to be
`insufficient_information`, require every reasoning node to span the full
monitoring interval, and require each non-Solution node to carry exactly the
provenance of the generation run (`run_id`, `prompt_sha256`, `request_sha256`,
serializer version, role, `prose_review: required`) with origin `llm_proposal`.

Passing these checks is structural acceptance only. None of them shows that a
statement is true or that R1 holds.

## 3. The saved fixture

Folder: `integration/fixtures/one_pass_20261113/artifacts/models/`. All eight
files match the SHA-256 and size in `MANIFEST.json`.

| Fact | Value |
| --- | --- |
| Execution | `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db` |
| Task / variant | `2448c758145ae5ad500f` / `xmlenv:574b783c...321148e` |
| Requirement | `R1` version `2.0.0` |
| Configuration digest | `8128b52d4292a5730bc5ce4f980dabf3047e1255f046274fd24287f8b1e8016c` |
| Protected objects, in order | `cream_cheese_1`, `ketchup_1`, `orange_juice_1`, `milk_1`, `butter_1` |
| Monitoring interval | frames `[10, 257]` on `saved_frame_index` |
| Graphs | 5, each with 4 nodes (`G1` goal, `S1` strategy, `C1` context, `U1` unresolved claim) and 3 edges: 20 nodes and 15 edges in total |
| Solution nodes | none |
| Registry records / checker assessments / Phase 5 pairs | 0 / 0 / 1 |
| Outcomes | `insufficient_information` for the execution and all five objects |
| Argument bundle digest | `b22e2b7fdf7ef21aaf8332af0c078434366a81eb6eadc473b1781eacad02d222` |
| Critic request digest | `34f6f8f003a0ab57b5e5a221bf9f6b4dc8c8a678d0d317978598f20a10f7a95e` |
| Controlled-negative request digest | `4c06acd245b5039902331af35aae8f48a9c615026f7dea09eba3f79c63e68b3f` |

Checked by running the code:

- Both Critic requests pass the Critic input checks. A fresh rule-only review
  of each returns `completed` with zero criticisms.
- Both saved Qwen reports pass `critic_report.schema.json`, have
  `criticisms: []`, and record the digest of the request they reviewed.
- The controlled-negative request differs from the original in exactly two
  places: `request_id`, and the statement of `cream_cheese_1:G1`, which reads
  "Cream_cheese_1 was guaranteed physically safe throughout this execution."
- The argument bundle in `drafter.argument.json` equals the bundle inside
  `critic.request.json`.

**Gap:** the Drafter request for this run (`request_id` `PR20-complete`, digest
`939d2bed...49d40c90`) is not in the repository. So `validate_argument` and
`build_critic_request` cannot be re-run on the fixture. The Critic request is
the only complete, validated input the fixture provides.

## 4. Proposed extension point

A new package, `drafter/revision/`, that reads the existing contracts and
changes none of them.

**Input:** the unchanged Critic request, the unchanged Critic report for it,
and explicit decisions on findings. The Critic request already holds
everything a revision needs: the argument bundle, the full R1 configuration and
its digest, execution, task, variant, object roster, monitoring interval,
registry records, checker assessments and Phase 5 pairs. It is also what the
Critic actually reviewed, and it is in the fixture.

**Output (implemented, see `README.md`):** a revised bundle or an explicit no-change or unresolved
result, a node-level diff, a disposition for every finding ID, validator
results and a stop reason. Re-criticism is then an ordinary
`critic.review` call on a request that differs from the reviewed one only in
`argument_bundle` and `request_id`, the same two places in which the
controlled-negative fixture differs from the original.

**Validators to reuse:** `critic.checks.run_all`, `gsn.Graph.validate`,
`graph_structure_issues`, and `validate_argument` whenever the caller also
supplies the Drafter request.

**Never changed by a revision:** the R1 configuration and its digest, the
requirement version, execution, task and variant, the object roster and its
order, the monitoring interval, registry records, checker assessments, Phase 5
pairs, any Solution node's copied record, and the stored original inputs.

**One point to agree: provenance of an edited node.**
`validate_argument` requires every reasoning node to carry the generation
run's provenance and origin `llm_proposal`. A node whose text a revision has
rewritten was not written by that run, so keeping that provenance would be
false. The proposal is to give an edited node revision provenance (revision ID,
round, finding IDs, digest of the node it replaces), with origin
`unresolved_conclusion` for host template text and `llm_proposal` for text a
model adapter proposed. The revision tests show this is accepted by the shared
GSN rules, the Drafter structural rules and the Critic input checks. It is, by design, not accepted by `validate_argument`, which stays the
validator for unrevised drafts.

## 5. Test results on this branch

| Suite | Command | Result |
| --- | --- | --- |
| Drafter (existing) | `python3 -m unittest discover -s drafter/tests -t .` | 209 tests, OK |
| Handoff (existing) | `python3 -m unittest integration.tests.test_handoff` | 9 tests, OK |
| Critic (existing) | `python3 -m unittest discover -s critic/tests -t .` | 189 tests, OK |
| Revision (new) | `python3 -m unittest discover -s drafter/revision/tests -t .` | 102 tests, OK |

The three existing suites gave the same counts before any revision code was
added.

## 6. Things found on the way

1. The fixture lacks the Drafter request (section 3). Ask Nikta whether the
   handoff sidecar from the run, which contains it, can be added.
2. `critic/examples/case_e_partial_structured_retrieval.report.rules_only.json`
   no longer matches what the Critic returns for
   `critic/cases/case_e_partial_structured_retrieval.json`. The saved report
   names obligation `contacts_object_01`; a fresh run names `settling_actions`.
   The other four saved example reports still match. This is the Critic
   owner's to regenerate.
3. `finding_source` allows `evidence_grounded`, but no Critic code produces it.
4. A report from a rule-only run has `llm.request_sha256: null`, so such a
   report does not record which request it reviewed. The revision request
   therefore carries its own request digest (see the mapping).
