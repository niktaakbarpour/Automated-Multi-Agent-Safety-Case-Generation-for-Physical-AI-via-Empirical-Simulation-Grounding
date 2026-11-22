# RQ3 GSN input handoff

This CPU fixture pack gives Alex and Nikta two validated clean parent requests and a check for controlled changes against those parents. It uses the two parent groups described in Alex's November 20 draft mutation protocol (PR #31, commit `9b674b8eb1d894596ac7e0687fef7308b9c681a6`). Both are development sources. The pack contains zero approved independent RQ3 groups.

| Parent | Source and exposure | Scope and evidence |
| --- | --- | --- |
| P1 | [Saved November 13 one-pass request](../../../integration/fixtures/one_pass_20261113/README.md), a prior Qwen run on the original reviewed LIBERO task-00 trial. Previously exposed to review and Critic testing. | Five objects, saved frames 10–257, one preserved Phase 5 retrieval pair and zero registry Solutions. The retrieval pair fulfills two explicit obligations. Whole-scope completeness is false. |
| P2 | [Critic Case C](../../../critic/cases/case_c_correct_unresolved.json), a synthetic execution used during Critic development. | Three fictional objects, saved frames 8–120, and nine synthetic registry-shaped records. The three graphs exercise scoped pose, contact and camera references. |

Both parents leave every object and execution outcome at `insufficient_information` and carry no admitted checker assessment. Clean means the saved graph and its references pass the checks and the current rules produce no findings. The parent roster, object and node IDs, time bounds, evidence IDs, and evidence provenance are retained. P2 reuses node IDs across object graphs, so match a finding to a target by the pair `(object_id, node_id)`. The [clean fixture manifest](gsn_inputs/CLEAN_FIXTURE_MANIFEST.json) records source paths, hashes, exposure and scope. The builder replays the saved baseline requests by emitting exact copies from the pinned source paths in that manifest.

## Run the pack

Run with Python 3.12 and the repository's `critic/requirements.txt` dependencies from the repository root. The shell variable below points to a new output directory.

```sh
export PYTHONPATH=.
pack_dir="$(mktemp -d)"
handoff_dir=evaluation/m4_20261127/rq3/gsn_inputs
python3 evaluation/m4_20261127/rq3/gsn_inputs/build_inputs.py --out "$pack_dir"
python3 evaluation/m4_20261127/rq3/gsn_inputs/build_inputs.py --check "$pack_dir"
python3 evaluation/m4_20261127/rq3/gsn_inputs/validate_controlled_inputs.py \
  --out "$pack_dir/controlled_inputs.json"
python3 evaluation/m4_20261127/rq3/gsn_inputs/audit_contracts.py \
  > "$pack_dir/contract_audit.json"
cmp "$pack_dir/CLEAN_FIXTURE_MANIFEST.json" "$handoff_dir/CLEAN_FIXTURE_MANIFEST.json"
cmp "$pack_dir/controlled_inputs.json" "$handoff_dir/CONTROLLED_INPUT_VALIDATION.json"
cmp "$pack_dir/contract_audit.json" "$handoff_dir/CPU_CONTRACT_AUDIT.json"
```

The clean builder writes the two Critic requests and their manifest. The controlled-input check exercises one scoped change per case. M1 changes a safety statement. M2 changes a statement or redirects a citation to another same-scope record, with the corresponding source fields on the Solution. M3 changes the stated scope while keeping the authoritative configuration and graph scope fixed. Invalid evidence links are tested separately. The check runs the shared GSN validator and Critic input checks, and compares the rest of the request with the parent. A structurally valid controlled case is eligible for the development comparison. The check alone gives no verdict on independent semantic labels, model detection or physical safety.

To check Alex's engineering cases, fetch the PR head if the pinned commit is missing locally, then verify the exact revision. This needs GitHub access to the team repository. The validator reads the explicitly named engineering requests from that Git revision. Neutral review files and the review key are outside this pack.

```sh
if ! git cat-file -e '9b674b8eb1d894596ac7e0687fef7308b9c681a6^{commit}' 2>/dev/null; then
  git fetch origin refs/pull/31/head
fi
git cat-file -e '9b674b8eb1d894596ac7e0687fef7308b9c681a6^{commit}' &&
python3 evaluation/m4_20261127/rq3/gsn_inputs/validate_controlled_inputs.py \
  --alex-ref 9b674b8eb1d894596ac7e0687fef7308b9c681a6 \
  --out "$pack_dir/alex_controlled_inputs.json"
cmp "$pack_dir/alex_controlled_inputs.json" "$handoff_dir/PR31_ENGINEERING_VALIDATION.json"
```

The [standalone receipt](gsn_inputs/CONTROLLED_INPUT_VALIDATION.json) covers six local controls. The [PR #31 engineering receipt](gsn_inputs/PR31_ENGINEERING_VALIDATION.json) covers all 15 cases. Eight semantic mutations and four clean controls passed input validation. The three invalid link controls failed the input gate for their declared violations. A second pass through the production Critic with the model disabled confirmed 12 completed reviews and three input rejections. Deterministic objections raised during review are recorded separately from that gate.

## Contract and source checks

- The two requests use Critic request 0.3.0, shared GSN 1.0.0 and registry record 1.0.0. Their configurations use generalized R1 2.0.0 and configuration schema 2.0.1. P1 preserves the saved Phase 5 query and result without converting them to registry evidence.
- The separate frozen current-v3 study scope uses five protected objects and the frame-10-to-terminal boundary. The audit checks the scope decision and all six hashes in the frozen v3 implementation manifest. P1 retains its original v2 envelope and stated 10–257 interval. P2 is a synthetic v2 control with a different roster and interval. Neither is an empirical v3 label.
- P2 uses synthetic records with `/synthetic/` references. The Critic development fixture supports those references. The production evidence registry rejects those paths. Graph validation uses a read-only view of the already validated fixture records, and the pack preserves the original records rather than importing them into the registry.
- The production Drafter-to-Critic adapter expects a validated accepted generation report bound to its original request. The saved P1 request is preserved after that projection. A standalone Drafter mock has a distinct contract. Revision example checks exercise saved inputs and scripted changes, including refusal of a historical controlled report whose deterministic findings have since changed.
- The [contract audit](gsn_inputs/CPU_CONTRACT_AUDIT.json) records the checked versions and hashes. Its exit status covers the CPU baseline and frozen v3 hashes. The separate Critic experiment freeze predates the rule-blind change and differs for `critic/llm.py`. The CPU comparison uses main at `20cec80bd44d19c6f58168132f366cbe38bd74e9`. Alex and Nikta need to confirm the experiment configuration and update its freeze before relying on it for formal RQ3 runs.

## CPU verification

Executed with Python 3.12 and `jsonschema==4.19.1`. Commands and results are in the [CPU test results](gsn_inputs/CPU_TEST_RESULTS.json). Across the existing suites and eight new pack tests, 665 tests passed and one was skipped. The skip was the v4 infrastructure suite's Hestia-only check. The legacy registry integration suite uses a hard-coded Hestia filesystem path, so the portable pack validates the actual shared Graph implementation directly against these fixtures. The source receipts describe the saved requests and exclude replay of the original recordings or measurement payloads.

For an independent RQ3 run, Nikta needs to approve source eligibility and supply the relevant source receipts. Alex owns the final mutation specification and scoring setup. Both parent groups here are exposed to development. The text-only and retrieval-only conditions should use identical paired cases. Condition C for physical claims remains unavailable until checker evidence is independently admitted. Treat repeated runs and mutations as paired observations within one parent group.
