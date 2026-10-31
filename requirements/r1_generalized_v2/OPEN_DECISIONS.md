# Scientific approval gates before V4 implementation

No decision below is approved by this Phase 1 commit. The proposal supplies defaults
for coherent review; it does not fabricate authorization. Approvals should identify
the decision ID, chosen alternative, rationale, requirement/profile version, approver
and actual date in a new record. An earlier R1 scope selection does not approve these
extensions. Unknown calibration cannot be resolved by accepting this document.

| ID | Decision requiring approval | Proposed default / alternatives and consequence |
|---|---|---|
| D01 | Protected-object selection and verified object absence | Arbitrary explicit predeclared set, including task targets; verified absence => NA with reason; empty set => empty_scope excluded from metrics. Alternative: absent configured object invalidates intended experiment scope. Must not confuse missing detection with absence. |
| D02 | Multiple surfaces, movement and indirect support | Designated union per object, any qualified initial root; allow only capability-validated supported handoffs/dynamic chains. Alternative: fixed initial root or separate object/surface requirements. These change which departures count. |
| D03 | Exact hazard/temporal witness | Unsupported downward falling departure; no causation/floor/intention requirement; gravity-frame translational witness and interval-qualified onset. Approve whether the retained post-lift exclusion still defines this requirement. Surface containment/any departure/retention should be separate IDs if desired. |
| D04 | Handling episode end, re-placement and non-designated handoff | Retain uncertainty after unresolved re-placement/handoff; no automatic restart. Alternative: explicit new applicability epoch, or permanent post-lift scope termination. Requires separate formal semantics/version and fixtures before use. |
| D05 | Multi-object execution aggregation | Preserve vector/counts; any valid violation dominates, then invalid contract, unknown, qualified negative, NA; report incomplete execution validity alongside a valid violation. Alternative: scalar IC precedence over all violation claims, while retaining verified object violations separately. Approve how empty/absent scope affects study eligibility. |
| D06 | Initial V4 capability/evidence and boundary-inference profile | Start with audited passive rigid-body/state-based profiles; camera optional unless witness needs it; direct/indirect support is an explicit validated inference. Decide required forces/normals, boundary context/look-ahead after the first action, alternate vision-only contract, moving surfaces and multiple-parent support. Unsupported capabilities must fail explicitly. |
| D07 | Calibration, tolerances, persistence and alignment | No invented physical defaults. Establish independent uncertainty/calibration and clock/geometry phase bounds. Any hysteresis/persistence is an evidence limitation, never an unreported hazard exemption. Approve calibration data and acceptance criteria before implementing physical thresholds. |
| D08 | Negative-domain composition and partial reporting | Full requested-domain qualification required; partial windows emitted with whole-domain U. Approve whether/how verified support motion, carry and excluded post-lift phases compose negative claim coverage. Do not broaden eligibility solely to improve the existing 4/5 coverage. |
| D09 | Mapping failures and missing-versus-invalid precedence | Verified absence can be NA; ambiguity/temporary missing evidence U; unsupported essential contract IC; malformed config rejected before assessment. Approve claim-specific invalidity isolation and positive-witness survival across unrelated gaps. |
| D10 | Empirical validation/reference design | Keep old AI-only results immutable and exploratory. Preregister new disjoint tasks/scenes/seeds and independently verified positives/negatives, with explicit reference provenance, unit of analysis, clustering, metrics and abstention handling. Decide acceptable use of AI-only versus human-confirmatory references. |
| D11 | Configuration and adapter certification | Approve schema 2.0.0 and versioned capability/certificate process. JSON conformance is not validation; third-party adapters need model/frame/clock/source binding. Approve whether additional representations/benchmarks enter the first V4 scope or later releases. |

## Approval scope

All D01–D11 must receive an explicit disposition before V4 implementation begins.
Some may be approved as **deferred/not supported in the first release** (e.g. moving
surfaces, deformables, vision-only evidence), with required IC behavior documented.
This is a valid bounded scope; silence is not approval. D07 additionally requires
actual calibration evidence before numerical values are enabled; D10 requires a
separately authorized empirical protocol before new experiments. No new simulation,
dataset expansion, generalized labels, RAG or multi-agent code is authorized here.

Review [R1_V2_SPECIFICATION.md](R1_V2_SPECIFICATION.md) and
[FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md) together, then record the decisions. Any
selected alternative that changes their meaning requires a coherent revision and
revalidation before beginning the [V4 plan](V4_IMPLEMENTATION_PLAN.md).
