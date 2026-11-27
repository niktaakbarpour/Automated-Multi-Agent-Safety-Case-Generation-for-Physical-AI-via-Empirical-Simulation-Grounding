# Task 8A CPU readiness and runtime verification

This report preserves results from the approved exact-commit CPU readiness run before genuine inference. The request builder reported that the committed request matched a fresh rebuild; request and argument validation passed. Recorded test results were: Drafter test suite 237 passed; focused R1 v3 generation/profile suite 28 passed; evidence registry/admission/integration suite 50 passed. No readiness failure preceded GPU inference.

Tokenizer-specific Outlines check used the approved Qwen3-32B tokenizer at revision `9216db5781bf21249d130ec9da846c4624c16137`, without model calls or GPU use. The decoder schema compiled in 7.91 seconds (8,753 regex characters; vocabulary 150,332) within its configured 60-second limit. The full plan schema did not finish compiling within 60 seconds; it remains the authoritative host-side validation schema. See `OUTLINES_COMPATIBILITY_PUBLIC.json`.

The genuine run then completed one request: HTTP 200, 112.867345 seconds, no retries. Host validation passed with five graphs and all five object outcomes `insufficient_information`. The full host schema and decoder schema hashes are in `RUN_METADATA_PUBLIC.json` and `HOST_VALIDATION_REPORT.json`.

These test counts are recorded from the preserved exact-commit runtime logs, not re-run in this publishing checkout. Its available Python is 3.9 without `jsonschema`, and this checkout cannot execute the project suite without a suitable CPU environment. This publication operation performed independent JSON/hash and RQ4 aggregate checks; it did not install dependencies or rerun inference.
