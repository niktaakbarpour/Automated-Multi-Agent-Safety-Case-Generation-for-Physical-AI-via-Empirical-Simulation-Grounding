# R1 v3 genuine Drafter handoff

## Run and result

This is the genuine single-request Task 8A run, executed with merged source commit `bf62fe8338d40807c6ff7e6a5b331df557aaf632` (tree `b747e100471f697b3aab7174c0ed129456d24d4d`). The approved model was Qwen3-32B BF16, revision `9216db5781bf21249d130ec9da846c4624c16137`, served by vLLM 0.31.0 with Outlines structured output and tensor parallel size 2. One request returned HTTP 200 and completed in 112.87 seconds, with no retry. The exact generation settings and content hashes that are safe to publish are in `RUN_METADATA_PUBLIC.json`.

The accepted draft has exactly five graphs, in frozen protected-object order: `cream_cheese_1`, `ketchup_1`, `orange_juice_1`, `milk_1`, and `butter_1`. Every conclusion is `insufficient_information`. There are zero graph-eligible evidence records and zero admitted checker assessments. `safety_claim_verified` is false and `reasoning_review.status` is `required`. The Drafter accepted the draft against the full host schema; this is not an independently approved safety case.

## Load and validate locally

From the repository root, load `evaluation/m4_20261127/integration/task8a_r1v3/DRAFTER_ARGUMENT.json` and `GENERATED_GSN_GRAPHS.json`. The original immutable request and execution evidence package are already in the repository at:

- `evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json` (SHA-256 `2e264891305919e201f9e5614aebbdcc68de4e4fe10f40eda5007a336753a291`)
- `evaluation/m4_20261127/integration/ORIGINAL_EXECUTION_EVIDENCE_PACKAGE.json` (SHA-256 `9bef4ae3cb669f9de661059820e09cae8274528fd6d746496481171836ed5d27`)

Run request regeneration check and authoritative host validation from the repository root with the approved project CPU environment active (Python 3.12 and repository CPU dependencies installed):

```sh
python3 -m evaluation.m4_20261127.integration.build_r1v3_request --check
python3 - <<'PY'
import json
from pathlib import Path
from drafter.r1v3_profile import validate_argument, validate_request
root = Path('evaluation/m4_20261127')
request = json.loads((root/'integration/DRAFTER_R1V3_REQUEST.json').read_text())
argument = json.loads((root/'integration/task8a_r1v3/DRAFTER_ARGUMENT.json').read_text())
validate_request(request)
validate_argument(argument, request)
print('request and accepted argument valid')
PY
```

The same argument check is available directly:

```sh
python3 evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
```

`FULL_HOST_SCHEMA.json` is the authoritative validation schema; `DECODER_SCHEMA.json` is only the relaxed generation-time decoder schema. The exact tokenizer-specific CPU compatibility measurement is in `OUTLINES_COMPATIBILITY_PUBLIC.json`: decoder compilation took 7.91 seconds within the 60-second limit. Host validation is still required after constrained generation.

## Reproduce the downstream rejection without inference

With the project CPU dependencies installed, run:

```sh
python3 evaluation/m4_20261127/integration/task8a_r1v3/DOWNSTREAM_REPRODUCE.py
```

Exit status 2 and the concise expected `ContractError` diagnostics are the expected current-main result. Other nonzero exit statuses indicate script or environment errors. The script calls only `integration.handoff.build_critic_request` using the original repository request and genuine accepted generation report; it does not invoke any model. The diagnostics are summarized in `DOWNSTREAM_INTERFACE_DIAGNOSTICS.md` and `DOWNSTREAM_INTERFACE_COMPATIBILITY_PUBLIC.json`.

The adapter contract currently needs an explicit reviewed update for `outcome_backing`, the R1 v3 prompt and serializer versions, `decoder_relaxation`, and `validation_schema_sha256`. Preserve evidence grounding, unresolved outcomes, scope, and run provenance. Do not strip fields or fabricate a Critic request. Critic and Revision stages have not been run on this genuine draft.

## Integrity and publication notes

The authoritative Hestia SHA manifest was checked before staging. Core immutable hashes: argument `3fad406df87af383b93739f0840e0b972adf91090337c330e9b6ee5eb85d54dd`; graphs `4e24a19f4bc43e2ee40d7d0cb03520604a18c963f23cfb57058cba54b4006e48`; generation report `0a8ecb88dd090ca2b5de91ccac2fe06eb063f09c4e2f97e25b81cacc6c82933a`; raw response `970698f86d5f32dc1210d83390469347b3bc4cfa1382f02ddc17584ce1299552`. All are recorded again in `ARTIFACT_SHA256SUMS.txt`.

Public metadata and diagnostics are explicitly sanitized derivatives; they omit absolute host paths, PIDs, service commands, and caches. Raw server logs, launch record, command log, and raw host metadata remain in private run storage and are excluded from this public repository handoff. The request and evidence package are not duplicated because their byte-identical authoritative copies already exist in the repository.

The generated argument supports only the conservative unresolved conclusion under the frozen admission state. It does not support a claim that the objects were safe or unsafe, or an independently reviewed physical safety claim. Reasoning review, Critic and Revision integration, and end-to-end acceptance remain incomplete.
