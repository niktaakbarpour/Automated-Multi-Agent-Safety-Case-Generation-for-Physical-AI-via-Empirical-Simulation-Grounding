# End-to-end feasibility audit

This audit used the committed repository, component contracts and saved artifacts. No inference, simulation or source recovery was performed. Private RQ2 submissions, adjudication records and coordinator mappings were not opened.

## Transition assessment

| Transition | Interface and authority | What has actually been tested | Feasibility |
|---|---|---|---|
| RQ1 retrieval to R1 checker | Phase 5 query/bundle schemas and provenance/obligation checks; R1 configuration, assessment and checker contracts under `evaluation/r1_v4/` | CPU tests cover synthetic bundles and checker validation. No source-compatible admitted checker result is included in the saved one-pass fixture. | Components/contracts exist; fresh-clone empirical retrieval-to-checker replay is blocked by external DB, corpus and source recordings. |
| Evidence/checker to Drafter | Drafter request profiles, Phase 5 adapter, request/plan/argument schemas and `drafter/validation.py` | Drafter CPU suite covers constructed, saved and scripted requests. The real one-pass report records a Qwen Drafter call, but the original request and generation report are not in Git; no admitted checker data was supplied. | Implemented and tested; model interaction exists in a development run, but its input-side gates cannot be replayed from this checkout. |
| Accepted Drafter to Critic | `integration/handoff.py:build_critic_request`; Critic request, GSN, registry, configuration and retrieval validators | Nine integration handoff tests pass. Saved Critic requests pass current schema and Critic-input validation and bind to their saved reports. | CPU-tested interface plus one real-model development fixture. The fixture omits the accepted Drafter run report required to replay the handoff adapter. |
| Critic findings to Revision Agent | `drafter/revision/contract.py`, `engine.py`, schemas and explicit finding decisions | Revision tests and saved examples cover no-change, invalid input and scripted actionable cases. Current rules detect the guarantee in the controlled negative; a stale old zero-finding controlled report is rejected. | Implemented and CPU-tested. No real model-generated revised argument is available. |
| Revised argument to second Critic | `drafter/revision/engine.py:recriticism_request` and cycle runner | A synthetic/scripted two-round cycle validates and replays. | Interface exists; no real Qwen revision followed by a second real Critic pass. |
| Final outputs to scoring | RQ3 `experiment/score.py`/`make_tables.py`; RQ2 `integration/verify_saved_results.py` | RQ3 saved-response scoring reproduces per-case/summary CSVs and table. RQ2 public CSV/JSON and generalization row counts agree. | Saved RQ2/RQ3 analysis is CPU-reproducible. Full RQ1 replay remains external-data dependent. |

## Saved Qwen artifacts

`integration/fixtures/one_pass_20261113/` includes a saved Qwen Drafter argument, Critic requests, and Qwen reports/messages for the original argument and a controlled unsupported-guarantee edit. Eight manifest-listed files pass byte and SHA-256 verification. Both requests and reports pass current schemas and Critic request checks, and report identity matches request identity. Both historical Qwen reports completed with zero criticisms.

The controlled edit is one development example, not a second independently generated argument. Current deterministic Critic rules flag the guarantee, but that later rule finding does not rewrite the saved Qwen result. The fixture is `test_fixture=true`. It lacks the original Drafter request/run envelope and full source recordings, so current code cannot replay all original Drafter and handoff validation gates.

## Longest genuine chain and limits

The longest saved actual model chain is a real Qwen Drafter argument followed by a real Qwen Critic response, plus a separate Qwen Critic call on the controlled prose edit. The Qwen Critic missed the explicit guarantee in that controlled case. No automatic revision or real second Critic on a revised argument occurred. Separately, the Revision Agent correctly produces no change for a saved real zero-finding report. The full two-round change cycle uses synthetic/scripted findings.

External blockers: RQ1 requires its retrieval database/catalogue, original corpus/HDF5 and local encoder. Source-bound R1 checking requires compatible admitted source inputs. The fixture has no original Drafter request/run report. The new RQ3 independent-parent expansion remains blocked as documented in PRs #39 and #41. None of the CPU contract checks establish physical safety or system-level empirical effectiveness.
