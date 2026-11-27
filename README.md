# Phase 5K retrieval remediation

**Frozen assessment preserved; versioned requested-obligation correction available for development.** The frozen v1 planner and its historical outputs remain unchanged. The three documented temporal-label cases exposed one query-intent coverage defect. `requested_obligations_v2.py` now retains the joint-position request beside its separate recorded-time obligation, and `bundle_v2.py` prevents incomplete interpretation or plans from being reported as complete. V2 remains a deterministic reviewed-lexicon development implementation, not a general natural-language completeness claim or a physical-safety assessment.

The final assurance-guard-1 assessment has 216 question-scope instances on 24 fresh executions / 18 variants, nine categories, 72 authored templates. P@1=1.000; R@20=0.989 on 136 eligible cases. Multi-source completeness=24/24; required family coverage=84/84; critical abstentions=80/80. Source-value/scope/unsupported-assurance errors observed=0. See REMAINING_LIMITATIONS.md for the three false-complete plans.

The first frozen assessment is preserved in evaluation_v1/ and external work outputs. A metadata-only assurance defect invalidated V1 as a release candidate. A narrow fail-closed guard, four tests and a second freeze preceded V2. V2 uses new scopes but the same question-template bank; it is not an untouched linguistic holdout. No ranking or vocabulary changes followed either holdout.

Database: `/disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite` (unchanged SHA-256 `f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8`). Additive catalogue: `/disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite` (2,572,288 bytes; `ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e`). Reports and code: this directory. Complete machine results are referenced and hashed in ARTIFACT_MANIFEST.json; case-level summaries are in HOLDOUT_RETRIEVAL_RESULTS.jsonl. No copied corpus/database is in Git.

Read BASELINE_VERIFICATION.md, FAILURE_TAXONOMY.md, RETRIEVAL_DESIGN.md, EVIDENCE_BUNDLE_CONTRACT.md, ABLATION_RESULTS.md, MULTISOURCE_COMPLETENESS.md, ABSTENTION_AND_INTEGRITY.md, REPRODUCIBILITY.md, and REQUESTED_OBLIGATIONS_V2.md. The new implementation is compared only on the exposed frozen corpus; it does not replace or rewrite historical outputs. The independent authoring package still contains 60 blank slots and zero completed independent query references. V2 introduces no new execution, measurement channel, checker decision, empirical admission, or safety agent.


The separately versioned offline assessment for saved planner-v2 actual retrieval is documented in [OFFLINE_ADJUDICATION_V3.md](OFFLINE_ADJUDICATION_V3.md). It does not rewrite v1/v2 results or invoke retrieval.


The final publication-safe actual-retrieval adjudication and targeted source-integrity fault-injection results are in [publication_v1/RQ1_FINAL_RESULTS.md](publication_v1/RQ1_FINAL_RESULTS.md), with per-case tables and checksums alongside it. The fault cases are supplemental and do not change the normal replay results.
