# Abstention and uncertainty

| Mode | Required abstentions | Correct | Incorrect on positive references | Unsupported evidence returned | False assurance |
|---|---:|---:|---:|---:|---:|
| exact | 63 | 63 | 0 / 84 | 0 | 0 / 162 |
| lexical | 63 | 63 | 30 / 84 | 0 | 0 / 162 |
| semantic | 63 | 63 | 4 / 84 | 0 | 0 / 162 |

Genuine API abstention means no returned records. It is reported independently from the external rubric deciding that raw evidence is insufficient. Raw arrays returned for untyped support/calibration questions are not counted as acceptance of those interpretations when the result preserves native units, conditional/unresolved properties and false safety/synchronization flags.

False assurance is measured through explicit assurance contracts and returned flags, not generated natural-language answers: there is no answer generator. The observed zero rate does not measure hypothetical drafter hallucinations. Typed missing fields, wrong scope, unsupported transforms, unknown sensor clocks and unavailable historical attestation are evaluated separately from questions that require natural-language clarification.

Conditional cache queries require an explicit channel to use typed property filters. NL-only modes do not supply that positive channel oracle, so some fail at interface validation before ranking. Those are interface/intent coverage gaps, not evidence that the semantic embedding ranked the right field incorrectly. Untyped exact-instant ambiguity cannot be automatically resolved; the external rubric records ambiguity instead of inventing a timestamp.

All uncertainty labels and contract-status errors are retained per case. Explicit wrong-execution denial appears in the development challenge subset; final tests exercise wrong task, variant, source and temporal scopes plus cross-execution attribution. This is a final-suite coverage limitation, not a claim of final unknown-ID replication.
