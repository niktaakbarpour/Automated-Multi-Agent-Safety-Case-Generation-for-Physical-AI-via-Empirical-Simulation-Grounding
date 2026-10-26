# Approved R1 human-reference dataset

This version was finalized through AI-assisted adjudication explicitly approved by third researcher Nikta Akbarpour. Read approval_metadata.json for the exact approved proposal hashes and the scope of that approval. The historical proposals remain unchanged and still describe their pre-approval state.

All 90 decisions are approved; approval does not resolve every evidence limitation. Ten requests retain unresolved components, and the episode-014 orange-juice fall classification remains insufficient_information. One request is resolved using existing evidence. Original independent-review statistics are unchanged.

Use final_label_json and human_approval_status in the four adjudicated tables. Original rows, recommendations, evidence measurements and rationale are retained alongside final labels. proposal_status, ai_recommendation_status and human_approval_required are historical proposal attributes; they do not supersede the final approval metadata. Requirement physical_event_id fields map to canonical event-group IDs; source event IDs remain in original rows and JSON provenance. Compound subevents and disjoint negative-observation intervals must be read from final_label_json; blank flat timing fields are not negative observations.

The four CSVs are byte-identical to the existing finalizer's private content-addressed outputs. This public companion has a sanitized manifest and additional ledgers, summaries and reproducibility documentation; it does not overwrite the private version. Relative excluded-evidence references do not imply those files are publicly accessible. Core manifest and approval bindings are hash-pinned. Final labels are a coverage-qualified research reference, not guarantees of physical truth.

## Reproduce and verify

From repository root, with the authorized private evidence/bridge restored, run the command in REPRODUCE.md. Outputs are content-versioned; any changed existing inventory or byte is rejected. No command infers human approval. Public verification checks available hashes, originals, approval bindings and referential integrity; it cannot independently validate inaccessible raw evidence.

The dataset version is recorded in dataset_manifest.json. SHA256SUMS.txt covers every companion artifact except itself. No source recording, source review or provisional package is overwritten. EVALUATION_HANDOFF.md in the parent adjudication directory defines the next evaluation step; no detector results are reported here.
