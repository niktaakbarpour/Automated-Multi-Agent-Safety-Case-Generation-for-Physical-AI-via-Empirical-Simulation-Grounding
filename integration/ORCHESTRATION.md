# M4 orchestration candidate

The candidate runner coordinates existing validated interfaces; it does not
replace Drafter, Critic, RegistryV3, Checker, or Revision implementations.
Runner version: `m4-orchestrator/0.1.0`.

## CPU resume of the genuine Task 8A draft

Use Python 3.12 with the repository CPU dependencies installed. From the
repository root:

```sh
python -m evaluation.m4_20261127.integration.build_r1v3_request --check
python evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
python -m integration.orchestrator resume-task8a --out-dir /tmp/m4-task8a-resume
```

The resume command binds and validates the immutable request, generation report,
argument and original evidence package; checks their hashes; rebuilds the R1 v3
Critic request with the existing adapter; and runs the deterministic CPU Critic.
It writes `CRITIC_REQUEST.json`, `CRITIC_REPORT.json`,
`HANDOFF_PROVENANCE.json`, and `RUN_MANIFEST.json` only to the requested output
directory. It never rewrites the source artifacts. Repeating the command is
allowed only when any existing output bytes are identical. A mismatched output
or manifest causes a fail-closed collision error.

Library callers may pass `checker_assessments`, `checker_source_root`, an open
`RegistryV3` instance, `trusted_review_hashes`, and `task_id` to
`run_saved_task8a`. The existing Critic independently replays each assessment
and its admission contract. Missing verifier context or failed gates remain
blocked; supplying an assessment or hash alone cannot declare admission. No
Checker assessment is included in the default genuine Task 8A resume.

This is a resumed downstream run, not a fresh end-to-end execution. It does not
repeat retrieval, Checker execution, or Drafter inference. The genuine request
contains no admitted Checker assessment and has zero graph-eligible evidence.
The deterministic Critic report keeps the five outcomes unresolved, does not
verify a safety claim, and leaves reasoning review required. No R1 v3 Critic
model route is currently implemented. The downstream Revision interface still
does not accept the R1 v3 Critic contract; do not translate it by dropping or
inventing fields.

The legacy `task8a_r1v3/DOWNSTREAM_REPRODUCE.py` is retained as a historical
PR #62 reproduction. Its expected pre-PR #63 rejection no longer describes the
current combined interface. Current adapter behavior is exercised by the R1 v3
handoff test and `resume-task8a`.

## Fresh genuine generation

`generate-r1v3` provides an explicit model-backed entry point using the existing
Drafter generation function. It only calls the already configured endpoint; it
does not launch a server. The caller must provide the approved config file and
explicitly authorize the attempt:

```sh
python -m integration.orchestrator generate-r1v3 \
  --request evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json \
  --model-config /path/to/approved-local-model-config.json \
  --out-dir /path/to/new-empty-run-directory \
  --authorize-model-execution
```

This command is intentionally not used in CPU CI or by the resume command.
GPU/server availability, the frozen model configuration, and authorization
must be checked before invoking it. A successful generation is only a Drafter
accepted draft; it is not a Critic verdict or safety-case approval.

## Versioned RQ1 retrieval

The programmatic `run_rq1_v2_retrieval` helper explicitly constructs
`RequestedObligationsRetriever` from `bundle_v2.py`, requiring a caller-supplied
pinned index path and SHA-256. It returns planner-v2 interpretation, unresolved
obligations and retrieval status, and forces physical eligibility and safety
sufficiency to `NOT_EVALUATED`. It fails if planner v2 was not actually selected
or an incomplete plan is paired with a complete retrieval status.

Example from the repository root on a host with the authorized pinned index and
its recorded runtime available:

```python
from integration.orchestrator import run_rq1_v2_retrieval

result = run_rq1_v2_retrieval(
    index_path="/authorized/path/catalogue.sqlite",
    expected_index_sha256="<approved-index-sha256>",
    query="Joint positions at frame 20.",
    execution_id="<indexed-execution-id>",
    task_id="<exact-task-id>",
    variant_id="<exact-variant-id>",
    frame_interval=(20, 20),
)
```

The external Phase 5K catalogue, source files and associated dependencies are
not in this checkout, so no actual retrieval replay is claimed here. Planner
unit and development tests are distinct from retrieval execution. Complete
retrieval never establishes physical evidence admission or safety sufficiency.

## Current integration boundaries

| Stage | Candidate behavior | Boundary |
|---|---|---|
| Source/evidence | Validates the source package bound into the saved R1 v3 request | Does not reopen HDF5 or re-register source measurements |
| RQ1 | Selects planner v2 through the actual retriever API | Requires authorized external pinned database and sources |
| Checker | Missing assessment remains unavailable | No Checker result is inferred from video or retrieval |
| Admission | No assessment is admitted by this runner | Existing independent-review and physical admission gates remain authoritative |
| Drafter | Genuine saved run is host-validated; fresh mode is explicitly gated | No generation during resume or CPU CI |
| Critic | Current handoff plus deterministic R1 v3 CPU route | No R1 v3 Critic model route |
| Revision | Runs only after an actionable finding and a matching reviewed contract | R1 v3-to-Revision contract is unresolved; no fabricated translation |
| Second Critic | Only after an accepted revision | Depends on the Revision interface and an agreed report contract |
| Final status | Draft pending reasoning review | Never promotes successful stages to safety approval |

This orchestration change is stacked on PR #63's accepted R1 v3 handoff and is
reviewable against that branch without copying its implementation. It uses the
existing Task 8A saved request, argument, and accepted generation report. The
PR #62 argument-validation and artifact checks remain compatible; the resume
command independently validates the bound request and argument before handoff.
The historical PR #62 rejection script remains a record of the pre-PR #63
contract and is not used as a current acceptance test.

The CPU workflow adds the saved-resume and orchestration regressions while
retaining the base branch's current checks. When stacked with PR #62 and the
other M4 PRs, keep their validation steps and combine the additive workflow
checks. No Drafter, Critic, Checker, Revision, or RegistryV3 implementation is
copied into this branch.

CPU integration tests use synthetic state fixtures for policy transitions.
The separate resume command validates the preserved genuine Task 8A artifacts;
synthetic tests are not model inference or empirical evidence. An actionable
Critic finding with no supported Revision adapter is explicitly reported as
`blocked_contract_unavailable`; the runner does not invent a Revision call or
substitute model output.
