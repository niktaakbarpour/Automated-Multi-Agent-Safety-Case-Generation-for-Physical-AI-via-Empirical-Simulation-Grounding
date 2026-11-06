# Drafter fixes for Nikta's audit

Base: main `f7de24a86a8b1565bb0ee204635d724bb90ada7d`.
Local branch: `fix/drafter-audit-and-phase5`.

## What changed

| Finding | Repair | Main regression coverage |
| --- | --- | --- |
| Prose can contradict unresolved outcomes | Summary, limitations and execution conclusion are host-controlled. Model summary/limitations live in `reasoning_review`, and all non-Solution node prose carries a mandatory review marker. Rendered reviews display the warning. Arbitrary prose is not declared scientifically validated. | `test_validation_regressions.py` |
| Standalone graphs use weaker validation | Generation and standalone checks share graph-shape rules. Root, strategy, context, connectivity, subclaims, scope, original Solution references and available evidence are enforced, alongside the unchanged shared `Graph.validate`. | `test_validation_regressions.py`, `test_contracts.py` |
| Missing checkpoint crashes | Required checkpoint is checked before indexing. Malformed inputs and deep JSON are rejected; CLI rejection reports can be saved without a traceback or model call. | `test_input_rejection.py` |
| Original configuration only | New supplied-registry and structured profiles accept validated alternative configurations. The original archived-fixture route retains its strict source verification. | `test_input_profiles.py`, `test_adapter_generation.py` |
| Archived evidence only | `adapt_phase5_request` preserves exact request/bundle pairs and a citation ledger. It composes the current Critic's consumer validation; raw channels/table/native robot data remain context. Only directly source-bound original registry records become Solution references. | `test_phase5_adapter.py`, `test_adapter_generation.py` |
| Single-character constrained text | Decoder text uses length constraints without the incompatible substring regex. Unsupported decoder `uniqueItems` was removed, with uniqueness enforced by the host. Degenerate prose is rejected separately. | `test_decoder_regressions.py` |
| Evidence IDs used as edge endpoints; empty Solution citations | Generated IDs use configured object namespaces. Decoder alternatives require non-null eligible evidence on Solutions and null evidence elsewhere. Prompt examples distinguish node IDs from evidence IDs; declared endpoints and evidence scope remain strict host checks. | `test_decoder_regressions.py` |

Accepted structured-profile outputs carry `evidence_context`, checked for exact equality with the validated input context. Complete retrieval never becomes a verified safety conclusion. The adapter checks consistency rather than independently authenticating database/source bytes. Missing mandatory/optional evidence, noncomplete statuses, source attribution and assumptions remain explicit.

The adapter supports inclusive saved-frame monitoring intervals. Unmapped clocks and indirect registry lineage are rejected clearly instead of guessed. Table and native robot identities remain separately scoped context; they are not silently mapped to protected objects.

## Local verification

The final Drafter suite passed: **183 tests, zero failures** (70 additional tests relative to the merged 113-test suite). All model responses in those tests are scripted; no model, GPU or database was called. The adapter supplies registry records to the current Critic consumer so its new crosswalk checks are enforced.

```sh
python3 -m pip install -r drafter/requirements.txt
python3 -m unittest discover -s drafter/tests -t .
```

The regenerated labelled mock passes the shared graph validator and produces five graphs, 40 nodes and 35 edges. It remains a deterministic software demonstration. The original archived registry/configuration bytes and all frozen RAG/checker/evaluation files are unchanged.

## GPU and real-database checks still required

No updated-code Qwen inference has been performed locally. Nikta's prior actual response remains a rejected result; it was not repaired or presented as accepted. Tests reconstruct its failure patterns because the raw Hestia trace and diagnostic JSON were not published with the two reports.

First run the CPU-only EOS-aware check in the existing XGrammar 0.1.25 serving environment:

```sh
python3 drafter/tools/check_xgrammar_compatibility.py \
  --out /path/to/new-xgrammar-compatibility.json
```

It compiles the corrected full plan schema and tests sentence acceptance. The check uses a tiny ASCII tokenizer, not the Qwen tokenizer, so actual server generation is still required. This compiler check was not run on the Mac because XGrammar is unavailable there.

Use the already working SGLang 0.5.4.post3/XGrammar 0.1.25 setup and the full pinned Qwen checkpoint. `config/qwen3_32b_sglang.example.json` records the prior checkpoint revision; a client setting does not authenticate the server's actual loaded weights. Retain server configuration and loading metadata. SGLang's per-request seed limitation remains; do not claim bitwise reproducibility.

Save discovery, the fixed JSON probe, corrected-code generation, exact prompt/schema, raw output, validation results, model/tokenizer revision, package versions and runtime. Choose fresh output names; retain the previous rejected attempt. Then test the adapter against the actual Phase 5 retriever and its source closure on Hestia.

See README.md for CLI preparation and generation commands. No Critic, RAG database, checker, recordings or frozen evaluation code was changed.
