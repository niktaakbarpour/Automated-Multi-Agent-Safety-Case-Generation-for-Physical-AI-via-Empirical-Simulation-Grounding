# Validation report — 2026-10-30

**Artifact validation passes. Formal approval, freezing and V3 scoring remain pending.**

- All 20 case IDs and assigned objects verified; no missing or duplicate case rows.
- All 66 copied non-media source files match their original remote SHA256 values.
- Both complete source inventories (644 + 74 files) were rehashed on Hestia after preparation and match intake fingerprints; all 718 original files remain unchanged.
- Source reports, all annotations, physical snapshots and uncertainties retain exact bytes, original AI identities and dates. Separate metadata records user-reported acceptance.
- The replacement blinded AI2 is the only second-evaluator source used.
- Proposed labels: 12 not applicable, 8 no violation observed within reviewed coverage, 0 insufficient information; NV12 exact AI2 rationale and physical rows retained.
- Every source annotation field is compared; 1,700 comparisons include complete case coverage objects. All 155 physical rows appear exactly once in candidate navigation groups.
- All 28 uncertainty requests are preserved; global requests are attached explicitly, not lost on neutral-ID joins.
- No checker predictions were parsed or scored by the preparation/validation pathway. A separate SHA256-only preservation check confirmed the original prediction hash.
- Original independent workflow, frozen references, evaluations, recordings and all pre-existing tracked repository files are unchanged (`git diff 87a8221` outside this new directory is empty).

## Tests

| Suite | Result |
|---|---|
| New integrity/approval tests | 11 passed |
| Existing human-validation suite on working checkout | 26 passed; 1 pre-existing missing-file error |
| Same existing suite from isolated unmodified `87a8221` Git archive | Same 26 passed; same missing-file error |

The error is `test_all_original_protected_bytes_unchanged`, whose first missing input is `human_review_package/adjudication/test_results_final_baseline_20261026.txt`. The historical protected inventory includes 397 entries: 339 available files match and 58 are absent from the base Git tree, including excluded/private historical artifacts. Zero available-file hash mismatches were found. No historical file was invented, restored from guesses, or altered to make the suite pass. See `baseline-87a8221-tests.log` and `historical_protected_inventory_check.json`.

New tests detect source tampering, dropped uncertainty/cases, invented human metadata, incomplete discrepancy reporting and blank approvals. Synthetic declarations exist only in temporary test directories and cannot create a reference seal or scoring result. `verification-tests.log` retains results.

## Source hashes

| Source | File | SHA256 |
|---|---|---|
| AI1 | `REPORT.md` | `db681e8f03453f706518b464eba98cf8c526f4dc54d729b5b7e910d6cade39b4` |
| AI1 | `annotations/initial_support.csv` | `2b59b74510bebc7421dbdb53de8fcd7a372d22c06c40588794870c05e480510b` |
| AI1 | `annotations/events.csv` | `eab5cbfa3a87eb786d1e68bdcb1acc9e729dad93e8f469083dd8d02ea55bc205` |
| AI1 | `annotations/requirement_interpretation.csv` | `9d6be6cd91ca21f461e396f1706fd052d6dca397d52daf69586f38d68ebff5a1` |
| AI1 | `annotations/uncertainty_requests.csv` | `0985acd42b24bf3a5279bc031ca5c95ce717b1d7d51ec1e3917840f7448e76e0` |
| AI2 | `REPORT.md` | `0099865d0e463bfb82282993c23e25eed0f8265ed6bfc14109267b3361337843` |
| AI2 | `annotations/initial_support.csv` | `a67459b635207d86c50cb8cab7776624b762a336b60b3116b2b5411043eae73a` |
| AI2 | `annotations/events.csv` | `132e8ccf76367fcdb8892b54fb9e948c155ceb5a17c51afdd84d6aba85409087` |
| AI2 | `annotations/requirement_interpretation.csv` | `ff598cd62a34e0769fd76117467eef146f23246a9b3625728231c4ca52e46dbe` |
| AI2 | `annotations/uncertainty_requests.csv` | `83592e194ea5cd1c0d01e94572001df29ea4549f99ab3fb8aba8bb90cd32ab18` |

Full file-level hashes and sizes: `human_evaluator_1/SOURCE_MANIFEST.json` and `human_evaluator_2/SOURCE_MANIFEST.json`. Separate acceptance metadata pins every copied file. `remote_preservation.json` records the final remote manifest fingerprints and SHA256-only prediction preservation check.

## Approval boundary

The blank `APPROVAL_TEMPLATE.json` is deliberately unapproved. `check-approval` rejects it before any prediction access. Missing reviewer confirmations, actual inspection declarations, third-human confirmation, authorized approval and approved comparison domains are enumerated in `APPROVAL_REQUIREMENTS.md`. No independent-human receipt or reference seal has been forged.
