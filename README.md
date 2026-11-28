# Trustworthy AI M4: empirical simulation grounding

This repository studies how evidence-grounded safety-case tools behave on recorded physical-AI simulation evidence. It does not certify a robot or policy as safe. The framework keeps measured source evidence, requirement checks, argument generation, criticism, revision and evaluation as separately validated steps.

## Current Milestone 4 status

The genuine R1 v3 Drafter run and bounded RQ4 Revision pilot are complete. The Drafter produced five graphs with `insufficient_information` for every protected object; the frozen request had zero graph-eligible evidence and no admitted checker assessment. The saved draft passed Drafter validation, host validation and the integrated deterministic R1 v3 Critic handoff. The supplementary human reasoning review packet is published and judgments are pending. Model-backed downstream review and end-to-end acceptance remain open.

RQ2 and RQ3 results remain development evidence with their documented admission and independent-review limitations. RQ4 is a small planted-defect pilot, not evidence of general Revision Agent effectiveness. No result establishes physical safety. See the [current M4 results](evaluation/m4_20261127/MILESTONE4_RESULTS.md), [integration status](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md), and [experiment registry](evaluation/m4_20261127/EXPERIMENT_REGISTRY.md).

## Reproduce saved results on CPU

The [experiment reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md) contains the Python 3.12 setup, manuscript table replay, individual RQ checks and saved Task 8A resumption commands.

## Repository and contributor guides

- [Repository map](docs/REPOSITORY_MAP.md) describes active components and historical result areas.
- [Cleanup audit](docs/REPOSITORY_CLEANUP_AUDIT.md) records code findings, archive candidates, and publication risks.
- [Artifact policy](docs/ARTIFACT_POLICY.md) explains frozen evidence, generated outputs, external dependencies, and restricted records.

## Research questions and architecture

- **RQ1 — Evidence retrieval:** retrieves requested evidence families and source-scoped measurements, checks obligation coverage and abstains when a request cannot be supported. Retrieval completeness is limited to the explicit request; it is not proof of R1 safety evidence sufficiency.
- **RQ2 — Requirement-aware R1 checking:** evaluates the fall-prevention requirement for specified protected non-target objects on the living-room table, under a versioned configuration and recorded monitoring interval. An unsupported decision remains an abstention. The current adjudicated sample is tiny and development-only.
- **GSN Drafter:** proposes a per-object GSN safety argument from validated configuration and supplied evidence. Its accepted structure and citations do not establish that the claims are physically true.
- **RQ3 — Critic:** checks the argument and its links, runs deterministic rules and can optionally screen model proposals. A zero-finding report is not a safety conclusion.
- **RQ4 — Revision Agent:** applies only contract-approved edits to an argument, preserving source evidence, requirement configuration and provenance. It cannot revise physical outcomes or invent evidence. The completed genuine Qwen run is a bounded pilot on three planted defects; repeated outputs are not independent cases, and the broader effectiveness study remains NO-GO.

The intended flow is:

`recorded evidence -> retrieval -> optional R1 assessment -> Drafter -> Critic -> reviewed revision -> second Critic -> scoring`

Each arrow has its own contract. The complete chain has not been demonstrated on a new, independently eligible physical execution. See [the feasibility report](evaluation/m4_20261127/integration/END_TO_END_FEASIBILITY_REPORT.md).

## Level A — CPU tests and demonstrations

Run the main CPU regression suites:

```sh
python -m unittest discover -s drafter/tests -t . -v
python -m unittest discover -s critic/tests -t . -v
python -m unittest integration.tests.test_handoff -v
python -m unittest discover -s drafter/revision/tests -t . -v
python -m drafter.revision.tools.check_examples
python -m unittest evaluation.m4_20261127.rq3.tests.test_experiment evaluation.m4_20261127.rq3.tests.test_mutations -v
python -m unittest evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_bundle evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_integrity -v
```

The RQ3 and RQ1 remediation tests are invoked by module because those test directories are not Python packages for `unittest discover -s`. These commands use scripted, synthetic or saved test inputs. The RQ3 unit tests print scripted request activity; those replies are test inputs, not new model results.

Verify the committed one-pass fixture and public RQ2 tables:

```sh
python integration/verify_saved_fixture.py
python integration/verify_saved_results.py
```

These validators make no model calls and do not read private RQ2 reviewer files. The first checks eight fixture hashes and current Critic contracts. The second recalculates the public RQ2 confusion and coverage counts from committed case rows and metrics.

Other useful CPU commands:

```sh
python -m drafter --validate-request drafter/cases/scenario_a.request.json
python -m critic --help
python -m drafter.revision --help
```

A synthetic integration or revision example demonstrates interface behavior only. It is not a physical execution or an effectiveness result.

## Level C — New inference and external evidence

New model inference requires a compatible OpenAI-style serving endpoint or local server, the specified checkpoint and tokenizer, hardware admission, environment/runtime versions, frozen input manifests and output destinations. Model weights are not included. New RQ3 inference used Qwen/Qwen3-32B revision `9216db5781bf21249d130ec9da846c4624c16137`, two L40S GPUs, BF16 and vLLM's native sampling fallback (`VLLM_USE_FLASHINFER_SAMPLER=0`); the precise recorded run notes and server launch command are in the real-run directory. Do not copy the old launch command without checking current resource admission and approvals.

A full RQ1 replay additionally requires the external retrieval database/catalogue, source recordings and pinned encoder described in its reproducibility documentation. RQ2 source-level replay requires the source HDF5 and associated recordings; external paths in result provenance are not available from GitHub. Any new human-reviewed RQ2 evaluation requires genuine independent human submissions and an authorized adjudication workflow. No model or scripted output may stand in for those labels.

The isolated RQ3 unseen-parent expansion remains blocked: PR #39 and stacked PR #41 document the unavailable HDF5 sources and zero admitted independent parent executions.

## Scientific boundaries

- RQ1 completeness is scoped to requested obligations. The three temporal cases passed corrected actual-retrieval verification; historical false-complete flags are superseded by offline adjudication, not confirmed retrieval defects.
- RQ2 has a three-variant calibration, a 20-case retrospective evaluation with 18 scored cases, and a separate expanded coverage audit. The completed retrospective comparison remains development-only.
- RQ3's 108 responses are development-only; 12 semantic cases come from two exposed parent groups. The independent mutation-label audit is pending. C is admission-status-only.
- The saved one-pass Qwen interaction shows real model calls on a development fixture and one controlled semantic miss; it does not establish physical safety or general Critic effectiveness.
- RQ4 includes a genuine Qwen Revision pilot and second-Critic outputs on three planted defects (9 Qwen outputs, 3 template outputs). Its human judgments came from one coordinator-confirmed consensus form; independent agreement metrics are unavailable. This does not demonstrate the complete Task 8A Drafter-to-Critic-to-Revision-to-second-Critic chain or general effectiveness.
- A passing schema, CPU test, source hash or component handoff proves only its checked contract, not the truth of physical claims or complete system-level performance.

## Reports

- [Milestone 4 final results](evaluation/m4_20261127/MILESTONE4_RESULTS.md)
- [Experiment registry](evaluation/m4_20261127/EXPERIMENT_REGISTRY.md)
- [Current integration status](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md)
- [End-to-end feasibility historical snapshot](evaluation/m4_20261127/integration/END_TO_END_FEASIBILITY_REPORT.md)
- [CPU reproducibility record](evaluation/m4_20261127/integration/CPU_REPRODUCIBILITY_REPORT.md)
- [RQ1-RQ4 reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md)

## Existing execution-inventory workflow

The root `pipeline.sh` provides task/run inventory and transition-inspection commands. It uses the active Python environment or the interpreter selected by `PYTHON`. Commands that read recordings require the external source location in `config/project.json`. Set `source_results` in your local copy to the root of the original recordings. The checked-in value records the original collection location. `collect` inventories existing recordings and does not run a policy. `validate` checks the saved inventory and selected trajectory bindings. These commands are separate from RQ1–RQ3 evaluation reproduction.
