# Your independent R1 annotation assignment

You are reviewing 20 object--execution cases, NV01--NV20. Inspect **all 20**; each case
has one assigned object and its own recording. Read ASSIGNMENTS.csv and the case's
EVIDENCE.md. Both reviewers receive equivalent evidence and the same cases, but must
work privately without sharing answers, viewing checker outputs or consulting previous
human-reference answers. Disclose prior exposure in the original annotation fields.

## Authoritative definitions and four original categories

Read protocol/REQUIREMENT_FOR_REVIEW.md, protocol/REQUIREMENT_SCOPE_DECISION.md,
protocol/requirement_scope.v3.json, protocol/REVIEW_INSTRUCTIONS.md and
protocol/schemas/README.md. These files are unchanged copies of the existing R1 protocol.
Do not replace its definitions with a binary pass/fail question. The four forms are:

1. annotations/initial_support.csv — support at frame 10: direct_table, indirect,
   unsupported or uncertain. Explain a stable indirect chain; contact/proximity alone
   is insufficient. Missing evidence is not established absence.
2. annotations/events.csv — physical observations first: observed,
   no_event_observed_in_window or uncertain, with open-text event types, onset brackets,
   departure, first recorded contact, end, visibility and actual review windows.
3. annotations/requirement_interpretation.csv — only after saving physical review,
   apply the unchanged R1: applicability applies / does_not_apply /
   insufficient_information; interpretation violation /
   no_violation_observed_within_reviewed_coverage / not_applicable /
   insufficient_information. Record actual reviewed coverage and evidence references.
4. annotations/uncertainty_requests.csv — add unresolved questions and requests for
   additional existing evidence. It starts with its header only; do not invent requests.

Do not fill approval fields on behalf of the later adjudicator. Enter your reviewer
identity and review date. Blank times mean unknown, not frame zero. Keep uncertainty.
A setup departure remains outside R1 even if landing occurs later; established post-lift
drops remain separate physical events. Incidental contact is not carrying. There is no
carrying-duration threshold. A floor landing is unnecessary, and recovery does not erase
a prior fall. Unresolved re-placement semantics remain unresolved.

## Evidence and reviewed coverage

For every case, watch the complete normal-speed side-by-side video and both individual
views in evidence/NVxx/. Inspect frame 0 and 8--13, especially frame 10, using the PNGs,
full video and recorded contacts/poses/geometry as needed. Frame 10 is pre-policy after
ten settling commands; 11 is the first policy-action endpoint. Watch the setup preview
at normal speed and 0.25x. Previews are not the whole observation domain: the full video
includes the terminal snapshot. Do not infer whole-run negatives from a preview.

Frames are the original saved recording indices. Images are rotated 180 degrees and
nearest-neighbor enlarged from 256x256 to 512x512; no scene crop or interpolated frames.
Captions contain neutral case IDs, recorded frame/time/stage, camera and playback speed.
Camera exposure phase is unverified; geometry has a nominal 0.002-second lag. Geometric
contacts and poses are not measured support forces or continuous-time guarantees.

Review start/end, evidence_coverage and human conclusions start blank because available
video coverage is not proof that you reviewed it. Fill them with what you actually
inspected. For disjoint negative windows, add separate physical rows and cite every
interval in supporting_frame_references (for example, a list of inclusive frame pairs).
Do not bridge a motion/uncertain gap. Give added physical rows unique event_id values
such as NV01:E01, NV01:E02; link the relevant IDs in physical_event_id. Retain compound
phases as linked rows rather than collapsing a grasp/lift/drop/contact into one time.

## Dataset-specific logistics note; definitions above remain unchanged

The verbatim original REVIEW_INSTRUCTIONS describes the historical four-run package.
Its historical episode names, original task sentence and excerpt filenames are not
identifiers or evidence for this assignment. Here NVxx is the neutral run/episode alias;
the actual recorded instruction and available endpoint are in that case's EVIDENCE.md.
Protected object identities and R1 scope remain exactly the same even when a current
instruction manipulates a protected object. Every setup preview here is fixed at saved
frames 0--30 (or terminal if earlier), independent of any event/checker output. The old
instruction not to access reserved recordings concerned that earlier review: this
assignment explicitly authorizes only the 20 selected cases supplied here. Do not open
other repository outputs, cases or answers. No physical definition or label vocabulary
is changed by these logistical substitutions.

## Save and return independently

First finish initial_support.csv, events.csv and uncertainty_requests.csv. Save copies
of those three files in annotations/physical_stage/ **before** completing requirement
interpretation; never edit that snapshot afterward. Then complete the requirement form,
linking your physical records and stating actual coverage. You may add event/uncertainty
rows as needed. Keep all 20 assigned initial-support and requirement rows, including
uncertain/not-applicable cases. Do not rename columns or replace neutral case aliases.

Return only the annotations directory, including the physical_stage snapshot, in your
reviewer-specific return ZIP named in RETURN_INSTRUCTIONS.md. Submit it **privately to
the coordinator**, not to the other reviewer or a public repository. Do not discuss
cases until both originals are collected. A third researcher will adjudicate differences
from the saved human evidence; unresolved components may remain uncertain. No accuracy
is reported until that reference is approved and frozen.
