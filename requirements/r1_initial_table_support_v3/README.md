# R1 v3 Drafter configuration

`R1_V3_DRAFTER_CONFIG_SCHEMA.json` (`r1-v3-drafter-config/1.0.0`) is the R1 v3 requirement as the Drafter consumes
it. It is not a new requirement: `drafter/r1v3_profile.py` derives the configuration from the frozen v3 files and
binds it to each by SHA-256.

| Frozen source | Path |
|---|---|
| Checker configuration (support, applicability, event and negative-decision policies) | `evaluation/r1_v3/config.json` |
| Selected requirement scope | `evaluation/r1_v3_generalization/blinded_review/requirement_scope.v3.json` |
| Scope decisions and semantics | `evaluation/r1_v3_generalization/blinded_review/REQUIREMENT_SCOPE_DECISION.md` |

The review-scope schema under `evaluation/r1_v3_ai_assisted_human_verification_20261030/` describes a review record,
not a Drafter configuration, and is not used here. See `drafter/CONTRACT.md`, section "R1 v3 source-package profile".
