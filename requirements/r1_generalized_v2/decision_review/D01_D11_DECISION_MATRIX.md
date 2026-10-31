# D01–D11 decision review matrix

Status: recommendations only; no decision is APPROVED. Review baseline: `3d235bc69d2c23bf16803cd417f51deb7bbd2d94`. Questions below reproduce the actual Phase 1 register. Each primary disposition is expanded into independently actionable, deferred or evidence-blocked subdecisions. “After approval” is not permission to implement during Phase 1.5.

The CSV contains the same fields verbatim. Sources are Phase 1 files in the parent directory; test IDs refer to its planned V4 matrix, not executed tests.

## D01 — Protected-object selection and verified object absence

**Alternatives:** Explicit predeclared sets including targets; distractor-only sets; automatic selection. Verified absence as NA versus invalid intended scope. Empty set rejected versus explicit empty scope.

**Recommended alternative:** Explicit finite canonical set, no count restriction or LLM selection; reject duplicate IDs/aliases resolving to the same instance. Empty scope retained and excluded from metrics. Closed-roster absence yields object NA plus scope-mismatch flag; exclusion never silently repairs a study protocol.

**Disposition:** RECOMMEND_APPROVAL

**Subdecisions:** D01.a RECOMMEND_APPROVAL: selection, duplicate rejection, empty-scope accounting. D01.b RECOMMEND_APPROVAL: absence policy with separate experiment eligibility. D01.c BLOCKED_ON_EVIDENCE: actual closed-roster/alias certificate.

**Scientific justification:** Requirement quantification must be fixed before outcomes are known; nonexistence differs from failed detection. Scope mistakes cannot create safety evidence.

**Engineering justification:** Canonical identity resolution and protocol eligibility are separate from object outcome; deterministic validation avoids name/count-dependent logic.

**Safety definition consequence:** Targets may be protected if predeclared. Verified absent rows remain NA, not safe instances; all configured rows retained.

**V4 consequence:** Configuration handles 0/1/3/5/other counts; duplicate canonical config IDs rejected before assessment; duplicate resolved aliases fail binding. Unknown presence stays U.

**V3 compatibility:** Historical five-member set and denominators unchanged. New absence exemption and empty-scope reporting require separate V4 condition.

**Evidence required:** Source-bound scene roster complete at t0, canonical/native alias map, geometry/model identity and frozen selection manifest; preregister absence eligibility.

**Risks:** Cherry-picked scope, roster incompleteness and alias collisions; absence exemption can inflate apparent coverage if eligibility is hidden.

**Implementation readiness:** Specify now; structural implementation after approval. Empirical absence cannot be enabled merely by schema success.

**Source documents:** OPEN_DECISIONS.md; R1_V2_SPECIFICATION.md R1-G01; APPLICABILITY_RULES.md; R1_V2_CONFIG_SCHEMA.json protected_objects

**Test ids:** C00 C01 C03 C05 C06 C07 A03

## D02 — Multiple surfaces, movement and indirect support

**Alternatives:** Fixed initial root; explicitly designated union; separate per-surface requirements. Static-only versus moving/articulated surfaces. Direct support versus certified indirect or multiple-parent support.

**Recommended alternative:** Initial scope: multiple independently bound static surfaces across an execution; explicit S(o), with designated static union as the requirement meaning. No inferred surface addition. Implement direct and finite acyclic single-parent indirect chains only through admitted profiles. Defer handoff/dynamic/multiple-parent inference.

**Disposition:** RECOMMEND_REVISIONS

**Subdecisions:** D02.a RECOMMEND_APPROVAL: static surfaces and declared union. D02.b RECOMMEND_APPROVAL: capability-gated single-parent indirect support. D02.c DEFER: moving/articulated roots, dynamic handoff and multiple-parent inference. D02.d BLOCKED_ON_EVIDENCE: staticness and each chain inference profile.

**Scientific justification:** Union semantics distinguish leaving one designated surface from leaving the designated support system. Staticness and load bearing must be demonstrated, not inferred from an ID.

**Engineering justification:** Separate semantic capability declaration from adapter capability admission; support multiple roots without needing general dynamic load solving.

**Safety definition consequence:** Continuous qualified support within the designated union is not a fall. A handoff not evaluable by the initial profile remains unknown, never an implicit safe transfer.

**V4 consequence:** Resolve each root and all collision pieces, verify static transform evidence on the relevant domain; unsupported root motion => IC for affected claims; unresolvable local transitions => U. No world-wide IC for unrelated objects.

**V3 compatibility:** Singleton table mappings preserve intent, not output equivalence. Historical omitted ID15 and table binding remain untouched; corrected V4 mapping separately evaluated.

**Evidence required:** Per-root model hashes, collision geometry, transforms/staticness evidence; admissible contact semantics and chain validation; separate analytical union fixtures.

**Risks:** Unobserved surface motion, unseen alternative supports, cycles, incomplete geometry and hidden dynamic load redistribution.

**Implementation readiness:** Revise release scope now, then implement static structural resolution after approval; empirical support admission remains gated.

**Source documents:** OPEN_DECISIONS.md; R1_V2_SPECIFICATION.md R1-G02/G04; FORMAL_SEMANTICS.md Sup; EXAMPLE_CONFIGS/C_SYNTHETIC_MULTIPLE_SURFACES.json

**Test ids:** A04 A05 G03 S01 S02 S03

## D03 — Exact hazard/temporal witness

**Alternatives:** Any departure; any unsupported flight; unsupported downward falling departure; robot-caused fall; include versus exclude post-lift drops.

**Recommended alternative:** Keep verified unsupported downward falling departure from initial designated support, without a cause/intention/floor requirement. Retain established lift/carry exclusion. Separate containment and post-grasp drop/release requirements; no new implementation of those requirements here.

**Disposition:** RECOMMEND_APPROVAL

**Subdecisions:** D03.a RECOMMEND_APPROVAL: narrow hazard and handling exclusion. D03.b RECOMMEND_REVISIONS: explicit interval-boundary/censored-episode language in amendment A03. D03.c BLOCKED_ON_EVIDENCE: gravity-relative translation, origin and load-bearing handling witnesses.

**Scientific justification:** Different hazards need different labels and denominators. Intent does not determine mechanics: established carrying excludes a later drop, but intentional pushing could still cause an R1 fall.

**Engineering justification:** Keep physical episodes separate from applicability and scope tags. Avoid root-height or descending-vertex shortcuts that mistake rotation for falling.

**Safety definition consequence:** A later catch cannot erase an admitted in-scope fall. Loss before t0 is not a new in-interval departure. Onset or falling evidence straddling a boundary is qualified/U, not negative.

**V4 consequence:** Track loss, downward phase, handling and origin brackets separately. Do not require ballistic acceleration or a landing. An uncertain handling exclusion cannot suppress or confirm a fall.

**V3 compatibility:** Preserves historical hazard intent and lift exclusion; gravity/translation witnesses differ from world-z all-vertex inference, so V4 labels need new versions.

**Evidence required:** Identity-continuous poses, validated gravity/transforms and reference point, geometry/support-loss evidence, handling evidence when exclusion applies, clock uncertainty and interval brackets.

**Risks:** Narrow R1 misses harmful post-lift drops by design; temporal association cannot establish causation; sparse observations can conceal a short fall.

**Implementation readiness:** Approve semantics now with A03; implement analytical scope logic only after approval. Empirical positive claims blocked until witness profiles validated.

**Source documents:** OPEN_DECISIONS.md; R1_V2_SPECIFICATION.md R1-G03/G05; FORMAL_SEMANTICS.md F/InInterval; FALL_DEFINITION.md

**Test ids:** F01 F02 F03 F04 F05 F06 F07 F08 F09 G02

## D04 — Handling episode end, re-placement and non-designated handoff

**Alternatives:** Permanent post-lift termination; automatic re-arming; explicit new applicability epoch; conservative unresolved suffix.

**Recommended alternative:** Retain initial applicability and never auto-rearm. Preserve a verified excluded carry/drop episode. At verified re-placement or non-designated supported handoff, subsequent unresolved R1 scope stays U unless an earlier admitted violation already determines the object result. Defer new epochs and complex handoffs.

**Disposition:** RECOMMEND_REVISIONS

**Subdecisions:** D04.a RECOMMEND_REVISIONS: distinguish known excluded drop from unresolved post-replacement suffix (A04). D04.b RECOMMEND_APPROVAL: no automatic restart and positive preservation. D04.c DEFER: re-arming, permanent termination alternatives, complex handoff/re-support logic.

**Scientific justification:** Excluding a specific established handling episode does not prove all later motion outside the requirement. Re-placement introduces an origin/scope question, not renewed initial support by fiat.

**Engineering justification:** Use scope states and explicit unresolved intervals; do not reset a detector on every recontact or erase a previously established fall.

**Safety definition consequence:** An initially unsupported object stays NA under this execution requirement even if later placed. An initially applicable object may become unresolved after re-placement, not retroactively NA.

**V4 consequence:** Output initial applicability, excluded episodes, re-placement evidence and unresolved suffix independently; whole-domain negative fails when the suffix is unresolved.

**V3 compatibility:** Historical abstention for unresolved re-placement preserved. Permanent exclusion or re-arming would change claim scope and require another version.

**Evidence required:** Evidence for the handling episode, recontact/re-placement and scope boundary; do not assume contact alone establishes new stable support.

**Risks:** Conservative loss of coverage; falsely declaring episode termination can hide a later fall; catches must not erase earlier violations.

**Implementation readiness:** Amend text before implementation; exclusion/unknown bookkeeping can follow approval. Complex resupport remains deferred.

**Source documents:** OPEN_DECISIONS.md; R1_V2_SPECIFICATION.md R1-G06; FORMAL_SEMANTICS.md coverage; FALL_DEFINITION.md cases

**Test ids:** A01 S03 F04 F06 O01

## D05 — Multi-object execution aggregation

**Alternatives:** Any valid violation first versus global IC first; any-object applicability versus all-object shortcut; scalar-only versus full vector.

**Recommended alternative:** Preserve complete object vector and counts. Primary outcome: admissible violation, else affected essential IC, else U, else qualified negative over applicable objects with others NA, else NA. Empty scope explicit/excluded. Configuration-invalid input has no assessed result.

**Disposition:** RECOMMEND_APPROVAL

**Subdecisions:** D05.a RECOMMEND_APPROVAL: vector, precedence, empty eligibility. D05.b RECOMMEND_REVISIONS: distinguish input rejection from object IC (A01). D05.c RECOMMEND_APPROVAL: report evidence completeness independently of primary violation.

**Scientific justification:** R1 is universal prevention: one sound counterexample refutes it even if another object is unknown. Unknown unrelated objects cannot turn a sound violation into safety, nor may they support a negative.

**Engineering justification:** Deterministic precedence with scoped invalidity and separate completeness avoids hiding object findings in a global scalar.

**Safety definition consequence:** One NA never exempts other objects. A positive is local evidence of a violation, not complete knowledge of all objects. Unknown can change a negative to a violation and therefore prevents full negative.

**V4 consequence:** Aggregate only admitted object outcomes; global identity/time foundations that invalidate a positive remove its admission before precedence. Report counts and eligibility alongside scalar.

**V3 compatibility:** V3 had per-object outputs; execution-level aggregates have no historical accuracy baseline. Never substitute execution denominators for old per-object metrics.

**Evidence required:** Analytical truth tables for mixed outcomes plus source-dependency isolation proof/tests; no new physical calibration for aggregation itself.

**Risks:** Users may mistake violation-plus-incomplete for complete execution evaluation; invalidity isolation can be wrong if shared foundations are overlooked.

**Implementation readiness:** Can finalize now with A01 and approved dependency rule; implement pure aggregation after approval, no empirical performance claim.

**Source documents:** OPEN_DECISIONS.md; FORMAL_SEMANTICS.md Execution aggregation; APPLICABILITY_RULES.md Cardinality

**Test ids:** C00 C03 C05 O02 O03 O04 E01

## D06 — Initial V4 capability/evidence and boundary-inference profile

**Alternatives:** All LIBERO/benchmarks versus explicit recorder/model/task bindings; BOX/static versus general geometry; state-first versus vision-only; direct-only versus certified chains; snapshot versus boundary-context inference.

**Recommended alternative:** Start with existing LIBERO recorded-state schema, hash-bound rigid BOX geometry and static horizontal support roots, direct and admitted single-parent chains. Known task00/01 evidence is development provenance, not validated all-task coverage. Saved-frame domain only. Cameras conditional. Boundary context cannot move t0 or erase early events.

**Disposition:** RECOMMEND_REVISIONS

**Subdecisions:** D06.a RECOMMEND_APPROVAL: bounded initial capability declaration. D06.b RECOMMEND_REVISIONS: distinguish mathematical fixture mode, legacy comparison and empirical profile (A06). D06.c BLOCKED_ON_EVIDENCE: recorder state/contact phase and support-profile validity. D06.d DEFER: vision-only, other benchmarks, generalized shapes/dynamics.

**Scientific justification:** Configurable names do not establish recorder semantics or new-scene validity. V3 static-equilibrium reasoning is an inference with assumptions, not measured support force.

**Engineering justification:** Versioned adapter admission prevents inherited table/native-ID defaults. Metadata resolves per-execution settling and time; no fixed count10 in the new core.

**Safety definition consequence:** Narrow evidence capability, not narrower abstract object-count semantics. Unsupported essential geometry => IC; missing data under a supported profile => U.

**V4 consequence:** Separate validated facts from inference profiles; new model/XML IDs require fresh binding. Legacy stencil -1/0/+1 allowed only as explicitly exposed comparison/development profile until admitted for empirical use.

**V3 compatibility:** Reuse schema knowledge without editing V3 or treating its nominal lag and arithmetic allowance as calibration. Prior cohort remains exposed development regression only.

**Evidence required:** Producer/recorder version, XML and complete geometry inventories, state/transition timing, contact producer semantics/completeness, boundary phase and independent profile checks; raw restoration only if required fields unavailable.

**Risks:** Missing HDF5, camera exposure unknown, cached state/contact phase, omitted geometry and inference leakage from NV cases.

**Implementation readiness:** Contracts/fixture mode may begin after approval/amendments; no general empirical adapter certification yet.

**Source documents:** OPEN_DECISIONS.md; CURRENT_R1_AUDIT.md; EVIDENCE_CONTRACT.md; V4_IMPLEMENTATION_PLAN.md adapters/geometry/temporal

**Test ids:** A02 A04 G01 G03 G04 T01 T02 T03 T04 P01

## D07 — Calibration, tolerances, persistence and alignment

**Alternatives:** Invent fixed thresholds; inherit V3 roundoff/lag as physical calibration; independently bound uncertainty; defer claims requiring missing calibration.

**Recommended alternative:** No empirical numerical defaults. Preserve null as unknown. Use justified uncertainty bounds and explicit alignment dependencies; threshold-overlap yields U, unsupported essential calibration model IC. Separate arithmetic error from physical/recorder error. No minimum fall duration/distance exemption.

**Disposition:** BLOCKED_ON_EVIDENCE

**Subdecisions:** D07.a RECOMMEND_APPROVAL: no-default/fail-closed policy and separate arithmetic uncertainty. D07.b BLOCKED_ON_EVIDENCE: geometric, pose, state/contact phase and camera calibration where required. D07.c DEFER: empirical hysteresis/persistence policy until sensitivity/detection-limit evidence exists.

**Scientific justification:** A tolerance changes which observations are distinguishable; it must not silently redefine the physical hazard or be tuned to improve the exposed cohort.

**Engineering justification:** Carry calibration provenance/validity by channel and interval. Unknown optional camera phase does not block an independent valid state witness; essential unknown phase does.

**Safety definition consequence:** Short or small falls remain hazards even when the detector cannot resolve them. Unresolved evidence produces abstention, not semantic exemption.

**V4 consequence:** Do not enable empirical witness profiles without their required calibrated bounds or a justified exact recorded-state contract. Analytical exact inputs may test logic, not certify simulator physics.

**V3 compatibility:** Do not reinterpret 512-epsilon arithmetic bounds, nominal 0.002-s lag or 0.05-s cadence as new validated physical settings. Frozen V3 unchanged.

**Evidence required:** Recorder code/order and tests, event/state phase bounds, units/transforms/gravity/shape uncertainty, independent calibration protocol and held-out checks; camera exposure only for claims using images temporally.

**Risks:** Unbounded physical uncertainty, false precision, cohort-tuned thresholds, persistence suppressing true short events; restoration cannot recover never-recorded timing.

**Implementation readiness:** Policy can be approved now. Empirical parameters and profiles remain blocked; infrastructure and symbolic fixtures do not require fabricated calibration.

**Source documents:** OPEN_DECISIONS.md; FALL_DEFINITION.md Time/tolerances; EVIDENCE_CONTRACT.md Temporal alignment; R1_V2_CONFIG_SCHEMA.json numeric_policy

**Test ids:** G04 T02 T04 N01 N02 P01

## D08 — Negative-domain composition and partial reporting

**Alternatives:** No detected fall as negative; mandatory single modality; union of any available data; claim-qualified witness cover with bridge/transition obligations.

**Recommended alternative:** Require explicit negative/exclusion certificates over the requested saved-state domain. Union only admitted same-claim cells with compatible identities, clocks, profiles and scope; overlaps neither double count nor provide independent corroboration by themselves. No gap filling. Initial release static-negative profile only; defer dynamic/handling negative composition.

**Disposition:** RECOMMEND_REVISIONS

**Subdecisions:** D08.a RECOMMEND_APPROVAL: claim-specific coverage algebra and whole-domain U for holes. D08.b RECOMMEND_REVISIONS: make cross-source compatibility/contradiction checks explicit (A08). D08.c DEFER: moving-support and carry/post-lift negative composition. D08.d BLOCKED_ON_EVIDENCE: admission of actual negative certificates.

**Scientific justification:** Absence of a candidate is not evidence of absence. Two sources copied from one simulator cache are dependent; even independent sensors need temporal compatibility before their evidence composes.

**Engineering justification:** Represent cells and provenance dependencies instead of merging numeric intervals blindly. A boundary between qualified windows must itself be covered if the domain includes that transition.

**Safety definition consequence:** Saved-frame negatives claim only that projection, never continuous safety. Partial clear windows retained but whole claim U. A valid positive needs no full negative coverage.

**V4 consequence:** Available/decoded/inspected/admitted/negative domains separate. A known carry exclusion can be recorded without certifying the whole domain as negative.

**V3 compatibility:** V3 static negative windows remain as sealed. Broader compositional coverage is a new V4 condition, not improvement on historical 4/5 without separate evaluation.

**Evidence required:** Per-cell certificate, shared clock/identity/phase bounds, source dependency graph and overlap conflict tests; admitted support profiles for every negative cell.

**Risks:** Smooth plots and overlapping indices hide transitions; falsely independent derived exports inflate confidence; coverage-driven cohort tuning.

**Implementation readiness:** Coverage algebra ready after proposed revision/approval; empirical qualification blocked; dynamic/exclusion coverage deferred.

**Source documents:** OPEN_DECISIONS.md; R1_V2_SPECIFICATION.md R1-G08; FORMAL_SEMANTICS.md ClearCover; EVIDENCE_CONTRACT.md Coverage

**Test ids:** T03 T04 O01 O02 F09 E01

## D09 — Mapping failures and missing-versus-invalid precedence

**Alternatives:** Single unknown class; IC erases all findings; any positive signal wins; dependency-scoped admission with distinct missing/contradictory/invalid records.

**Recommended alternative:** Distinguish missing observations U, unresolved admissible conflicts U, and foundational unsupported/incompatible contract IC. Isolate invalidity by evidence dependency. Only a positive surviving its own identity/applicability/scope/contract checks enters aggregation; common-foundation contradiction suspends admission.

**Disposition:** RECOMMEND_REVISIONS

**Subdecisions:** D09.a RECOMMEND_APPROVAL: dependency-scoped validity and strong positive admission. D09.b RECOMMEND_REVISIONS: formalize unresolved conflicts and diagnostic-only input rejection (A01/A09). D09.c BLOCKED_ON_EVIDENCE: resolution of actual contradictory sources.

**Scientific justification:** A positive counterexample is decisive only if sound. Majority agreement or a weak visual cue cannot repair a broken identity, clock or geometry foundation.

**Engineering justification:** Persist all conflicting records and adjudication status, with explicit affected-claim edges; do not delete a sensor or choose a favorable label to remove conflict.

**Safety definition consequence:** An unrelated missing optional camera cannot erase a sound measured fall. A credible same-event contradiction can challenge witness admission and must not be dismissed by positive-first aggregation.

**V4 consequence:** Perform contract/conflict admission before object outcome and aggregation; configuration failure rejected with assessed=false and null assessed outcome. Preserve U/IC distinctions and reasons.

**V3 compatibility:** V3 merged several failures into insufficient information; new distinctions change accounting and require versioned comparison, never relabeling old outputs.

**Evidence required:** Dependency graph, producer/hash/clock identity checks, analytic contradictory-witness fixtures and documented investigation criteria for empirical conflicts.

**Risks:** Incorrectly calling a correlated conflict unrelated can create false positives; overbroad invalidation causes avoidable abstention; hash failure is not evidence of physical absence.

**Implementation readiness:** Amend before implementation. Pure precedence/conflict state machine can follow approval; unresolved real conflicts remain blocked.

**Source documents:** OPEN_DECISIONS.md; FORMAL_SEMANTICS.md V/Ev/outcome; EVIDENCE_CONTRACT.md Layered validity

**Test ids:** O02 O03 O04 G04 P01

## D10 — Empirical validation/reference design

**Alternatives:** Reuse exposed NV cohort for confirmation; natural-only evaluation; controlled-only evaluation; separate natural and controlled strata with disjoint development and held-out sets. AI-only versus independent human-confirmatory references.

**Recommended alternative:** Plan two separately reported strata: untouched natural executions and controlled, provenance-bound falsification scenarios. Predeclare object/support/interval scopes and split by source execution/seed/task/scene families to prevent sibling leakage. Include independently verified applicable positives, negatives, NA and uncertain cases.

**Disposition:** BLOCKED_ON_EVIDENCE

**Subdecisions:** D10.a RECOMMEND_APPROVAL: separate strata and honest reference provenance. D10.b RECOMMEND_REVISIONS: prospective sample/split/metric protocol before data acquisition. D10.c BLOCKED_ON_EVIDENCE: positive/negative references and independent review. D10.d DEFER: any new experiment execution in this task.

**Scientific justification:** Natural prevalence and controlled detection sensitivity answer different questions. No confirmed positive in the old cohort means no empirical recall estimate; AI consensus is not independent human truth.

**Engineering justification:** Freeze inference/profile versions before opening held-out references; link all object rows from a run to one partition and disclose cross-scene versus same-scene holdout.

**Safety definition consequence:** Dataset labels must use this versioned R1, including initial applicability, handling and coverage; task failure or a post-lift drop is not automatically an R1 positive.

**V4 consequence:** Later evaluation reports applicability, conditional outcome agreement, abstention/coverage, class confusion, localization only where identifiable, and clustered uncertainty. Report undefined denominators as null.

**V3 compatibility:** NV01-NV20 stay exposed exploratory/development material with their old seals and counts. Do not tune thresholds on them and claim a fresh held-out test.

**Evidence required:** Separately authorized natural-candidate audit/controlled protocol; preserved originals, independent physical evidence review, adjudication, locked splits, sample-size/precision targets and reference provenance.

**Risks:** Simulated perturbations alter construct/ecology; spectrum and selection bias, correlated objects/runs, reviewer/model dependence, leakage and positive scarcity.

**Implementation readiness:** Approve study principles now; protocol details and new experiments require separate approval. Empirical validation is not ready.

**Source documents:** OPEN_DECISIONS.md; VALIDITY_THREATS.md; V3_COMPATIBILITY.md; V4_TEST_MATRIX.md E01/E02

**Test ids:** E01 E02 P01 P02

## D11 — Configuration and adapter certification

**Alternatives:** JSON conformance as certification; ad hoc adapter acceptance; versioned structural plus capability/empirical admission. Single version versus separate requirement/evidence/adapter/checker/profile identities.

**Recommended alternative:** Keep independent versions and hashes for requirement, configuration schema, evidence schema, adapter, inference profile, checker and calibration. Capability tests establish bounded conformance only. Empirical validation scope/status is separately documented, not a self-asserted validated_contract flag.

**Disposition:** RECOMMEND_REVISIONS

**Subdecisions:** D11.a RECOMMEND_APPROVAL: independent version/provenance and capability gates. D11.b RECOMMEND_REVISIONS: proposed schema amendment A11 before runtime use. D11.c BLOCKED_ON_EVIDENCE: empirical capability records. D11.d DEFER: additional benchmarks, vision-only and unsupported geometry certification.

**Scientific justification:** Structural admissibility and physical validity are different claims; a hash authenticates bytes, not truth or generalization.

**Engineering justification:** Runtime resolves and verifies external capability/calibration records and scope, not merely nonempty certificate strings. Deterministic refusal for unknown versions/essential capabilities.

**Safety definition consequence:** Abstract arbitrary objects/counts do not certify their dynamics, materials or observation contract. Declarations never bypass abstention/IC.

**V4 consequence:** Add reviewed profile/evidence/checker version fields in a future revised schema or signed manifest binding; reject release-incompatible modes; retain immutable comparison namespaces.

**V3 compatibility:** Historical schema/config and seals unchanged. New version separation is additive and separately evaluated, not a migration of historical approval.

**Evidence required:** Analytical capability matrix, source/model/frame/clock binding tests, replay/tamper tests, scoped validation records with evidence links and calibration validity.

**Risks:** Certificate laundering, inconsistent version combinations, parser acceptance mistaken for certification, unsupported cross-benchmark claims.

**Implementation readiness:** Contract design ready after amendment/approval; runtime conformance infrastructure may follow. Empirical certification remains blocked.

**Source documents:** OPEN_DECISIONS.md; R1_V2_CONFIG_SCHEMA.json validation_record/benchmark; V4_IMPLEMENTATION_PLAN.md provenance/adapters; EVIDENCE_CONTRACT.md

**Test ids:** C07 C08 G01 G03 T02 P01 P02
