# Requested-obligation planner v2

`requested_obligations_v2.py` and `bundle_v2.py` add a versioned, conservative
query path. The frozen v1 planner, frozen evaluation outputs, and retrieval
database are unchanged. This is a deterministic reviewed-lexicon planner, not
unrestricted natural-language understanding.

## Contract

The response separates four questions:

1. `query_interpretation_status`: whether requested concepts and scope were
   understood without ambiguity.
2. `obligation_plan_status`: whether every recognized measurement-bearing
   request has a reviewed mapping or explicit unresolved/unsupported status.
3. `retrieval_completeness_status`: whether the original verified retrieval
   engine returned each planned obligation under its existing source, frame,
   provenance, and uncertainty rules.
4. `physical_evidence_eligibility`: always `NOT_EVALUATED` by this pathway.

Only a resolved query with a complete obligation plan is sent to the frozen
retrieval engine. The wrapper supplies the complete family list as an explicit
plan. Unsupported or ambiguous clauses are not silently omitted; incomplete
plans do not run retrieval and cannot be reported complete. Retrieved evidence
does not establish physical safety or admission eligibility.

## Reviewed mappings

- Finger/finger aperture/opening positions, displacement, and gripper
  configuration map to `raw.robot0_gripper_qpos`.
- Finger/gripper speed, velocity, or rate maps to
  `raw.robot0_gripper_qvel`.
- Joint/arm positions, configurations, angles, posture, or bend map to
  `raw.robot0_joint_pos`.
- Joint/arm speed, velocity, or rate maps to `raw.robot0_joint_vel`.
- A gripper-state request requires both recorded gripper position and
  velocity. `joint state` remains ambiguous.
- The explicitly reviewed phrase “opening mechanism displacement” maps to
  gripper position.
- Gripper aperture/displacement terminology maps to gripper position; a
  gripper-state request requires both position and velocity measurements.
- An explicit simulator label/time is a temporal qualifier and creates a
  separate `recorded_time` obligation. It does not replace the requested
  measurement family.
- Existing reviewed metadata/reference families and unsupported physical
  interpretations continue to use the frozen planner's mappings.

Multiple measurement subjects in a clause, generic joint readings/state, and
unmapped measurement-bearing spans remain ambiguous or unresolved. Unsupported
physical claims, synchronization, world transforms, and calibration requests
remain unsupported under the existing evidence contract. Query object,
execution, task, variant, and temporal scope checks remain authoritative in the
existing retrieval path. The adapter also verifies that a purported complete
retrieval contains every planned family with an `AVAILABLE` status.

## Development-only comparison

Reproduce planner-only counts on the exposed frozen corpus (the dataset and
references have already been exposed; this is not independent evaluation):

```sh
python -m evaluation.r1_v4.rag_evidence_database.retrieval_remediation.evaluate_obligations_v2
```

Run the planner regression suite:

```sh
python -m unittest evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_requested_obligations_v2 -v
```

The wrapper contract test uses synthetic fixtures. It requires the repository's
standard CPU dependencies and runs in the M4 CPU CI workflow:

```sh
python -m unittest evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_bundle_v2_contract -v
```

The above commands do not reproduce the historical actual retrieval run or
reopen the frozen experiment. Actual retrieval replay still requires the
authorized private evidence database and source artifacts; the committed
historical result file is read-only evidence of that earlier execution.

## Evaluation boundary

The corrected planner is tested against exposed development/frozen cases to
address a known implementation defect. These results do not estimate
generalization. Independent evaluation requires a frozen corrected build,
independently authored query formulations, independently authored obligation
references, eligible sources, and a blind protocol. The current authoring
package has blank slots rather than completed references, so no independent
evaluation is reported here.
