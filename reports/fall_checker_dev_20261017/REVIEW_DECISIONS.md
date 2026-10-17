# Decisions requiring review

Implementation is authorized; all choices below remain proposed and unapproved. Requirement approval, independent human labels, and detector validation are separate decisions.

| Decision | Proposed development behavior | Limitation / next review |
|---|---|---|
| Interval and setup | Frame 10 pre-policy boundary through terminal snapshot; inspect settling separately | Approve interval wording; decide treatment of runs with setup anomalies. Do not exclude runs silently. Last derived geometry/contact phase precedes endpoint by ~2 ms. |
| Five-object scope | Retain every object and run. Initially airborne objects have table support not established, never pass | Review applicability object-wise, especially ketchup, orange juice and milk in all development runs and cream cheese in episode 002. Unknown support cannot be verified non-applicability. |
| Initial/direct support | Native upper-table face contact plus geometric compatibility is a candidate | Missing normals/forces and uncertain endpoint timing prevent verified support. Review candidates independently. |
| Indirect support | Any possible supporting contact remains unresolved, including chains through another object | Force direction/load bearing cannot be inferred from contact graph. Return insufficient information pending reviewed evidence. |
| Direct departure vs lifting | Track possible bilateral grip lift separately; post-lift drop is not an automatic original-requirement violation | Review episode 014 and choose whether broader drops belong to a separately scoped requirement. Do not infer intent or causation. |
| Event definition | Consecutive unsupported-descent candidate after table departure; no floor requirement; catches/recovery preserve evidence | Short events, rotation-induced AABB motion, inter-sample contacts and controlled support transfers need reviewed labels. Ambiguous contact history is a separate candidate class. |
| Physical parameters | Explicit base plus two sensitivity profiles; no 6.50 mm threshold | Review ranges in PARAMETERS.md. They are exploratory candidate filters, not validated fall definitions or safety tolerances. |
| Human examples | Eight consecutive clips, both cameras; blank forms | Independently label support, event type and interval/uncertainty before viewing suggested interpretations where possible. Camera exposure phase remains unverified. |
| Validation | Synthetic tests separated from 40-run provisional outputs; held-out untouched | No measured precision/recall. Freeze reviewed rules and labels before later held-out evaluation. No genuine positive labels have been supplied or invented. |
