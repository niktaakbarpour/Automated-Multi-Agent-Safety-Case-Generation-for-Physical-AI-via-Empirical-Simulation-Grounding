# RQ1 independent query/reference authoring guide

## Your task

Author and independently source-check retrieval questions in the 60 rows of BLANK_QUERY_REFERENCE_FORM.csv. The 60 rows represent two authoring slots for each of 30 canonical executions; they are not 60 independent executions or 60 completed cases. Do not write retrieval scores or predictions into the form. No questions, expected answers, or human judgments have been prefilled.

The three known false-complete development cases (KH2-C2-02, KH2-C2-10, KH2-C2-18) are not in the 30 selected executions. Keep those failures as development examples only; do not reproduce them as new held-out cases.

## Offline evidence to use

Start with SOURCE_CAPABILITIES.csv for canonical execution, task, suite, variant, environment, objects, and saved-frame interval. Use SOURCE_EVIDENCE_INDEX.csv to find evidence IDs and the original record scope. Use OFFLINE_EVIDENCE/TASK_CONTEXT.csv for recorded task text and task metadata. Use OFFLINE_EVIDENCE/EVIDENCE_SAMPLES.jsonl.gz to inspect actual recorded values. Each JSONL sample ties a canonical execution, evidence ID, object/type, frame, original selector, resolved selector, and source trajectory SHA-256. The full indexed record envelope is in OFFLINE_EVIDENCE/EVIDENCE_RECORDS.jsonl.gz.

Read the schema before parsing values. For local inspection, use Python's standard-library gzip and json modules. Filter by execution_id, evidence_id, measurement_type, object_id, and frame_index. Compare original_selector with the matching row in SOURCE_EVIDENCE_INDEX.csv. Verify bundled checksums by running verify_offline_handoff.py.

Arrays are JSON arrays. Empty strings in the CSV form mean not authored; null or a missing dataset in an evidence sample means that source value was not available in that sample. An empty recorded contact group is not a verified no-contact observation.

## Fill one case carefully

1. Select a canonical execution and record its exact execution ID, task ID, and variant ID in the assigned blank slot.
2. Write a new question formulation yourself. Record whether it is linguistically distinct from prior templates; do not describe rephrasing alone as new source-execution evidence.
3. Break the request into atomic obligations. For each one, identify the exact requested object, evidence family, field, source/execution, temporal interval, and selector.
4. In SOURCE_EVIDENCE_INDEX.csv, find the exact evidence ID and determine whether its inclusive saved-frame interval covers the requested frame(s). Inspect actual values in EVIDENCE_SAMPLES.jsonl.gz using the resolved selector.
5. Record all required families and evidence IDs. For a multi-family question, account for every measurement-bearing clause. A relevant first retrieved family is not evidence of complete coverage.
6. Verify source identity, object, interval, field, and value using the bundled checksum manifest. Keep simulator frame labels distinct from wall-clock time.
7. Record absent, ambiguous, unsupported, or out-of-coverage obligations. Mark expected abstention when a requested obligation cannot be supported. Do not infer a physical event from task success, failure, reward, contact count, or a value's appearance.
8. Independently re-check the complete obligation-to-evidence mapping. Only then mark the reference-author verification field complete.

Do not change any source evidence, source/evidence IDs, extract values, hashes, or original selectors. If a value or interpretation cannot be independently checked from the bundled extracts, leave the relevant field pending and describe the limitation. Do not use retriever outputs to create the reference.

## Exact interpretation limits

The extract contains recorded simulator and observation values, not physical truth labels. It preserves raw values without interpolation, normalization, unit conversion, or physical interpretation. The simulator contact count is a count, not object-specific proof of physical contact. Contact-group records can be empty; that is not a no-contact verdict. Object pose and geometry fields are recorded simulator values; source mapping and geometry/cache phase uncertainties remain. Sparse saved frames do not establish continuous motion or coverage. Image pixels and MP4 videos are not included, so visual-event questions cannot be verified from this package. The source evidence does not establish fall, support-loss, or safety outcomes.

The selected task metadata includes a recorded policy instruction and a separate environment BDDL description. Some records mark an exact mismatch. Preserve both fields and do not silently substitute one for the other.

## Deliverable

Return the completed query/reference CSV with your authored question text, full required-obligation map, source/evidence IDs and selectors, coverage and missingness notes, expected-abstention rationale, and your independent source-check status. Leave unsupported cases incomplete. Do not report retrieval scores until the references are frozen and the baseline is run.
