# AI-assisted human review, evaluator 1

Open REPORT.md, then fill HUMAN_REVIEW.csv after checking the supplied evidence.
All decisions are AI-generated drafts; human decision fields are blank.
This bundle includes only the reviewer-1 neutral evidence, protocol, AI observations,
AI R1 interpretations, uncertainty requests and audit records. Predictions and
coordinator mapping are excluded. Keep it private from anyone still performing
an independent review of these cases.

The original study required two independent human-first annotations and third-human
adjudication. The user requested a changed method: AI proposals with human accept/reject
verification. Report that method explicitly. Do not use this AI bundle as a human
reviewer return ZIP or pass it to the original collect/freeze scripts. No original
workflow safeguards have been modified. Accept/reject verification and final reference
approval are separate steps; no approval, scoring, or accuracy estimate was generated.

The AI reviewed complete saved measurements and sampled frame sheets, not complete
normal-speed and quarter-speed video playback. Exact coverage is in COVERAGE.json.
Humans should verify the full source evidence required by the existing protocol and
record actual coverage, corrections, reasons, identity and date. They may reject,
accept, or retain uncertainty for each proposed component.

Files in annotations/ are AI proposals identified as ai_evaluator_1. Human-only
approval fields remain empty. annotations/physical_stage/ preserves the first
physical snapshot; annotations/physical_stage_v2/ is the separately sealed correction
saved before requirement interpretation. See PHYSICAL_STAGE_V2_SEAL.json.

After review, return HUMAN_REVIEW.csv and any correction notes privately to the
coordinator, keeping the original AI draft unchanged. No automatic acceptance or
conversion into approved reference labels is provided.
