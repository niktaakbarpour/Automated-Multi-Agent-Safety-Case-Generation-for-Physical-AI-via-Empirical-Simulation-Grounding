# Source-target retrieval and negative controls

New channel tests: 10,368 exact queries over all 432 executions/104 variants, at initial/middle/terminal frames and windows crossing frames 31/32. Precision@1=1.0, Recall@20=1.0, MRR=1.0. Exact channel-filtered lookup has one intended series target; these are source lookup metrics, not natural-language relevance or physical accuracy.

New negative controls: 27,488. Status counts: `{"excluded_preflight": 38, "excluded_reserved": 60, "invalid_query_scope": 5184, "no_matching_channel_record": 5184, "unindexed_profile_pending": 1470, "unknown_execution": 2592, "unsupported_channel": 2592, "unsupported_coordinate_frame": 2592, "unsupported_origin": 2592, "unsupported_temporal_domain": 2592, "unsupported_units": 2592}`. Includes wrong object/task/variant/execution, absent frames/channels, unverified units/world frames, derived-origin requests, unsupported seconds, all 60 reserved and 38 preflight IDs, and all 1,470 pending IDs. Excluded/pending tests use IDs only. No source payloads for those scopes were inspected. Cross-scope leakage: 0.

Legacy Phase 5F exact retrieval rerun on Phase 5G: 3,985 queries; Precision@1=1.0, Recall@20=1.0, MRR=1.0. Legacy negatives: 1,768; cross-scope leakage 0. Original evidence/source/selector/task/variant associations remain unchanged.

Numeric errors, contact-count consistency and saved-index alignment are reported independently in EXTRACTION_VALIDATION.md. Sparse-source and tampered-contract/source tests add cases that do not occur naturally in the selected complete recordings.
