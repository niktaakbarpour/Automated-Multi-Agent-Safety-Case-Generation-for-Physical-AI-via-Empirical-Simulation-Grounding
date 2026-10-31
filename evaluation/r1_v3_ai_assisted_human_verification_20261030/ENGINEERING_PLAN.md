# Prioritized integration plan from verified repository state

## Current implementation boundary

`src/collect.py`, `src/evidence.py`, `src/facts.py`, `src/geometry.py` and
`src/identifiers.py` provide execution inventory, evidence access, native identity
and geometry infrastructure. `src/requirement_proposals.py` and
`src/queue_requirement_pilot.py` support pinned-model requirement-generation pilots.
`evaluation/r1_v3/r1_checker.py` is a frozen empirical checker with explicit evidence
windows, scope and abstentions. `src/pipeline.py` remains an inventory/access CLI;
its contract keeps `data/cases.json`, `claims.json`, `events.json` and `objections.json`
empty. These are not an implemented GSN graph, drafting agent or critic/revision loop.
No RAG index, retrieval ranker or safety-case multi-agent orchestration was found.
The root README's statement that no LLM is called is stale relative to pilot code.

## 0. Finish provenance and evaluation before performance claims

Collect the missing confirmations and domain/discrepancy decisions described in
`APPROVAL_REQUIREMENTS.md`. After authorization, reconcile the replacement AI2 commit
with main and review an AI-assisted freeze/scoring adapter. Keep the four-recording
reference and all existing V3 predictions immutable. This task makes no merge/push.

## 1. Evidence schema and deterministic retrieval — next engineering milestone

Add a versioned schema for evidence units: canonical run/object/requirement IDs,
recording and derived-artifact hashes, saved-frame intervals, coordinate/timing
semantics, source modality, coverage, uncertainty, provenance and access location.
Separate simulator observations, checker inferences, AI prose, user-reported human
acceptance, and formally approved labels. Neutral case IDs require explicit mapping.

Start with metadata/interval retrieval over a small frozen Trustworthy fixture,
using existing evidence accessors and checked path bindings. Return exact evidence
IDs/JSON pointers and deterministic results, including missing/uncertain evidence.
Do not bulk-index production recordings or alter the current empty-collection
contract. Add retrieval-specific storage/CLI separately. A text/vector index can
follow only after this provenance contract works and retrieval quality is measured.

Acceptance: queries retrieve the correct run/object/window; wrong identities and
hashes fail closed; setup/post-lift evidence and uncertain intervals stay visible;
every result resolves to a source without claiming continuous-time support.

## 2. Claim-to-evidence links and GSN-compatible graph

Define typed Goal/Strategy/Solution/Context/Assumption/Justification nodes with stable
IDs and supportedBy/inContextOf edges, plus objections and unresolved status. Link
each factual claim to evidence IDs, exact intervals, checker version and epistemic
status. Validate graph references, cycles where forbidden, and scope consistency.
Represent unknowns and defeated claims explicitly; do not infer support from a
citation's existence. Provide JSON and a small deterministic GSN/Mermaid export.

## 3. R1 checker adapter

Wrap frozen V3 output in an evidence adapter rather than changing its inference
core. Preserve applicability, abstention, negative-proof windows, physical phases,
recording/config hashes and known scope-tag inconsistency. Require applicability
gating before any event supports an R1 claim. A post-lift drop is physical evidence,
not automatically an R1 violation. Do not compose partial negative windows into a
whole-run safety claim. Validate against already sealed fixtures without rerunning
policies or silently repairing V3. Future V4 is separately versioned/evaluated.

## 4. Safety-case drafting

Use a constrained schema to draft a small argument from retrieved evidence and a
reviewed requirement. Preserve raw model outputs, prompt/model/config hashes,
source IDs and costs. Require citations for empirical claims and explicit missing
evidence. Begin with one deterministic orchestration path before agent fan-out.

## 5. Evidence-grounded critic

Give the critic the argument graph plus independently retrieved counterevidence
and checker outputs. Detect unsupported/exaggerated claims, scope violations,
wrong identity/window, ignored abstention and unresolved evidence. Return typed
objections with exact source links. A critic objection is a proposal, not ground truth.

## 6. Argument revision

Revise the graph through logged patches responding to objections; preserve the
original argument, evidence links, rejected suggestions and unresolved items.
Validate after each revision. Revise claims/arguments only; never imply that changing
an argument improves the robot policy's physical safety. Bound iterations and costs.

## 7. Baselines and end-to-end evaluation

Freeze an evaluation protocol and disjoint cases before tuning: single-pass drafting,
retrieval-only drafting, checker-grounded drafting, and critic/revision variants.
Measure citation validity, factual support, scope/uncertainty fidelity, objection
quality, revision benefit, graph validity, latency and cost. Distinguish checker
accuracy, retrieval quality and argument quality. Use independent human review for
confirmatory claims; disclose AI-assisted references wherever used. Add independently
established positive R1 violations and indirect-support cases before estimating
positive-class detection or broad generalization. No end-to-end implementation was
started in this task.
