# Obligation recognition

Corrected assessment: 144 instances /72 authored formulations, two scopes each; 24 new executions /18 variants. No earlier development/final execution scope was reused. References were authored from original questions and source contracts, then validated with original HDF5/XML/JSON. No target output created labels; no human evaluation is claimed. Both freezes precede final execution. V1 used 144 different formulations and is separately preserved.

| Metric | Result |
|---|---:|
| Mandatory reference obligations retained | 902/908 |
| Micro recall | 0.993392 |
| Macro recall | 0.992923 |
| Micro precision | 0.924180 |
| Macro precision | 0.928439 |
| Exact obligation-set match | 78/144 |
| Measurement-family obligation recall | 1.000 |
| Temporal preservation | 140/144 |
| Scope/entity preservation | 144/144 |
| Conjunction preservation | 26/26 |

Six canonical obligations are missing: two 'time is T' selector forms, two frame windows expressed with 'and', two reverse-worded 'hash of ... source' requirements. All six stayed noncomplete. Their original spans and uncertainty remain visible, but that is not counted as successful canonical recognition. Extra unresolved-content markers lower precision/exact match. No labels, thresholds or exclusions changed after results. Case-level outcomes are in CASE_RESULTS.jsonl and FINAL_AUDIT.json.

The original frozen V1 scorer incorrectly counted omitted assurance defaults as None. Its 69 checked/107 baseline false-assurance counters remain archived. A separate audit of actual output assurances found zero; the corrected scorer uses the documented default. V1's strict false-complete flag remains 1/144, not retrospectively removed. V2's zero is from a genuinely new assessment.
