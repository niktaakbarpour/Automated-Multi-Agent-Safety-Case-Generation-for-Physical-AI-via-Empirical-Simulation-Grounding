# V3 implementation and pre-execution protocol

V3 branches from preservation commit `9902c788156370df985ee936473a2c294e62ea26`.
The V2 source, evaluator, configuration and predictions remain immutable.

`r1_checker.py` is independent pure deterministic requirement reasoning; `execute.py`
reads original HDF5 evidence and uses the frozen native-ID/transform utilities.
It never loads reference labels. No episode, seed or protected-object-specific answer
branches appear in the decision code. All protected objects share the same rules.

Initial support uses frames 9, 10 and 11, the minimal adjacent stencil around the
boundary, rather than a numerical settling/carrying-duration threshold. Stable rest
requires invariant actual collision transforms and geometrically qualified upward
contacts. For a BOX upper face, native signed contact distance must equal the
separation of the actual faces; its recorded midpoint must agree, and the contact
must lie inside their horizontal footprint intersection. The lower face must be
horizontal. Only the pre-existing native-transform 512-eps scale-aware arithmetic
allowance is reused. It is not a physical contact-height or motion tolerance.
The old exploratory 0.1-mm face/descent bands and two-interval detector persistence
are not used for definitive V3 decisions; this is a separately versioned evidence
policy, not a silent tuning of V2 thresholds.

Indirect support requires a uniquely resolved, acyclic chain of upward contacts to
the table with invariant transforms at every link. Supported children are permitted
loads on a lower support object. Competing/unknown contacts and ambiguous multiple
support parents cause abstention. No force normals or load-bearing force magnitudes
are inferred. A static equilibrium interpretation from sampled geometry and contact
is explicitly an operational recorded-evidence inference, subject to empirical
validation; it is not a physical guarantee. Non-stationary supported objects or a
first-policy-step change can make this deliberately conservative stencil abstain.

Absence requires complete adjacent contact records with *no external contact*, and
geometric separation from every table collision box. Merely missing a candidate,
being above a table, or lacking a direct edge is never enough.

History runs from frame zero without reset at frame 10. Departure and first recorded
contact are separate. Downward motion requires all corresponding collision vertices
to descend at two consecutive contact-free endpoints beyond arithmetic error; this
is a difference measurement, not a minimum fall-duration/distance limit. Initial
support ancestry and any intermediate interactions remain necessary. Rotational
motion alone, a single contact gap, root-height changes, supported motion and floor
contacts cannot independently establish a fall. A later catch does not erase an
emitted fall. A bilateral exclusive robot-contact interval with rising object and
both-finger geometry after table separation supports sampled lifting; release and a
subsequent unsupported descent yield a retained outside-R1 post-lift drop. No holding
time threshold is used. Incidental/unilateral contacts do not satisfy this rule.

Every negative saved frame requires explicit consecutive invariant table-support
proof. Disjoint proof windows stay disjoint. Full-request negative requires proof
for *every* frame from 10 through the recording's own terminal snapshot. Otherwise,
an applicable case abstains, retaining partial evidence and physical events. This
conservative version does not resolve re-placement semantics after a lift.

The predeclared comparison is development evaluation under the unchanged R1 and
handoff matching rules. Binary compatibility is checked on the shared saved-frame
projection only: same recording hash, run/object/version and full requested domain,
with reference explicit negative fragments covering the full claim. No synchronized
camera or continuous-time equivalence is asserted. Partial negatives, missing frames
and unresolved outcomes abstain. Non-applicability is scored separately; it never
adds TNs. Zero reference positives means positive-class recall/F1 not estimable.
Event localization uses the frozen maximum-cardinality matcher at 0 and 1 saved-frame
tolerance, partitioned by type, phase and scope. Physical outside-R1 matching is a
separate diagnostic and never supplies R1 positives. Unknown endpoints stay unknown.

Reference facts and requested regression scenarios were already known during design.
The source/config will be committed and hashed before execution; no reference CSV
will be opened again for V3 comparison until predictions are sealed. This prevents
runtime label inputs and post-prediction tuning, but cannot remove prior development
exposure. No held-out or unbiased generalization claim is warranted.
