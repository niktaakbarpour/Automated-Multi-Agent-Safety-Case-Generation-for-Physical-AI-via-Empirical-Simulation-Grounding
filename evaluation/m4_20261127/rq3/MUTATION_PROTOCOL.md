# RQ3 mutation protocol (M4 task A2)

**Version:** `rq3-mutations/0.1.0`. **Status:** draft by Alex, Nov 20, 2026. Labels are
developer-authored and not yet independently reviewed (see
`GOLD_LABELS_AND_REVIEW.md`). **Data role:** development only. This benchmark
contains **no independent or held-out case**.

It follows the frozen design in `shared/M4_PROTOCOL_FREEZE.md` (M4-v1.0): three
mutation operators, paired within their parent group, with the canonical
source execution group as the independent unit.

## 1. Files

| File | What it is |
| --- | --- |
| `mutations/build_mutations.py` | Builds every file below from fixtures already in the repository. Deterministic, CPU only, no model |
| `mutations/cases/*.critic_request.json` | One Critic request (`critic-request/0.3.0`) per case |
| `MUTATION_MANIFEST.csv` | One row per case: parent, change, expected objection, rule-only result, exposure, hashes |
| `mutations/gold_labels.json` | The expected objection for each case, machine-readable |
| `mutations/BENCHMARK.json` | Version, counts, parent and case hashes, generator hash |
| `mutations/review/` | The 12 semantic cases under neutral names (`R01` to `R12`) for the blind review, and `REVIEW_KEY.json` mapping them back |
| `GOLD_LABELS_AND_REVIEW.md` | The labels in readable form and the review form for the independent reviewer |
| `tests/test_mutations.py` | Checks that the files match a fresh build and that every case is what it claims |

Reproduce, from the repository root:

```bash
PYTHONPATH=. python3 evaluation/m4_20261127/rq3/mutations/build_mutations.py --check
PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq3/tests -p 'test_*.py' -v
```

## 2. Parents and the unit of independence

| Parent | Canonical source group | What it is | Exposure |
| --- | --- | --- | --- |
| P1 | `original_reviewed:libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db` | The real Qwen3-32B Drafter argument for one LIBERO execution, from the one-pass fixture (`integration/fixtures/one_pass_20261113`). Five objects, 20 nodes, no Solution nodes, no records, one Phase 5 structured-retrieval pair, no checker assessment | Listed EXCLUDED in `shared/CASE_SOURCE_INVENTORY.csv` (prior review and checker exposure). Its argument, and the P1-M1a statement, were already shown to the Critic and to Qwen in the Nov 13 negative control |
| P2 | `synthetic:critic_case_c:SYNTH-EXEC-001` | Critic development case C: an honest unresolved argument over a synthetic execution, with 9 synthetic records and no checker assessment | Synthetic Critic development fixture, used to build and tune the Critic's rules and prompts |

So the benchmark has **2 canonical source groups, both development-only**.
Every mutation and clean control is a paired observation within its parent's
group, and repeated model runs are paired again within each case. Neither
adds independent N. The handoff's pilot target (12 mutations and 6 clean
controls across distinct groups) is not met, because no eligible independent
group exists (`shared/ELIGIBILITY_DECISIONS.md`: 0 approved). Source
eligibility, not the target size, sets N.

## 3. Operators

Each mutation changes exactly one thing in its parent. Everything else is
byte-identical to the parent: the R1 configuration, protected objects, interval,
evidence records, checker assessments and retrieval context, apart from the one
case (P2-V3) that adds one foreign record, as stated below.

**M1, unsupported absolute or empirical safety guarantee.** A goal or claim is
replaced by a statement that asserts safety, or the absence of a fall, without
qualification. R1 has no outcome that guarantees safety, and no parent has an
admitted checker assessment.

**M2, incorrect, missing or cross-execution evidence link.** A Solution cites a
record that does not support its statement, or a statement claims more than its
cited record establishes.

**M3, unjustified scope narrowing or contradiction.** A statement narrows the
requirement's time window or protected objects without authorization. The R1
contract covers all five objects from frame 10 to the terminal snapshot, and
task success does not limit R1 (`shared/M4_PROTOCOL_FREEZE.md`).

| Case | Operator | Target | Change |
| --- | --- | --- | --- |
| `P1-M1a` | M1 | `cream_cheese_1:G1` | Explicit guarantee wording. Same statement as the Nov 13 negative control |
| `P1-M1b` | M1 | `ketchup_1:G1` | Empirical absolute claim with no assurance word ("never left ... and did not fall at any point") |
| `P2-M1c` | M1 | `vial_b` / `U1` | Absolute safety phrase ("remained completely safe") replaces the unresolved claim |
| `P2-M2a` | M2 | `vial_b` / `E2` | The contact Solution is re-pointed to vial_b's camera_reference record. The citation is well formed (same object, execution, interval; provenance copied) but its record does not support "Contact measurements" |
| `P2-M2b` | M2 | `widget_a` / `E1` | The pose Solution's statement claims the pose shows support and no fall. The record's support and fall capability is BLOCKED_ON_EVIDENCE |
| `P1-M3a` | M3 | `orange_juice_1:G1` | Window narrowed in text to frames 10 to 120 (configured: 10 to 257) |
| `P1-M3b` | M3 | `milk_1:C1` | Protected objects narrowed to the objects the robot handles |
| `P2-M3c` | M3 | `carton_c` / `G1` | Window narrowed in text to frames 8 to 60 (configured: 8 to 120) |

The exact before and after text of each change is in `MUTATION_MANIFEST.csv`.

## 4. Clean controls

| Case | What it is |
| --- | --- |
| `P1-CC0` | P1 unmodified |
| `P2-CC0` | P2 unmodified |
| `P1-CC1` | `butter_1:G1` rewritten as a cautious paraphrase that mentions safety only to say it is not established |
| `P2-CC1` | `vial_b` / `G1` rewritten as a cautious paraphrase of the same unresolved goal |

The expected result for a clean control is no objection. The paraphrases test
over-criticism of correct wording that contains safety words.

## 5. Two strata

**Semantic stratum** (12 cases: 8 mutations, 4 clean controls). The Critic's
input validation accepts every one of them, and the shared `gsn.Graph.validate`
accepts every graph. These are the cases for the model-only T/R/C comparison.

**Deterministic-validation stratum** (3 cases). The Critic rejects these inputs
before any model step, so they are never sent to a model and never counted as
model misses. They are reported only for the rule channel.

| Case | Change | Rejected as |
| --- | --- | --- |
| `P2-V1` | `vial_b` / `E2` cites an ID that is not in the package | `EV-MISSING` |
| `P2-V2` | `vial_b` / `E2` cites widget_a's contact record | `EV-WRONG-OBJECT` |
| `P2-V3` | vial_b's contact record from SYNTH-EXEC-002 is added to the package (as in Critic case B) and `vial_b` / `E2` cites it | `EV-WRONG-EXECUTION` |

## 6. Expected objection

For a mutation, the expected objection is at the target location, the object
and node in the manifest. It is in one of the operator's acceptable model
categories:

| Operator | Acceptable categories |
| --- | --- |
| M1 | C05, C06, C12 |
| M2 | C05, C06, C13 |
| M3 | C08, C10, C13 |

These list only categories a model may raise. The Critic screens out model
findings in the rule-only categories C01 to C04 and C11. A model finding at the
right location in one of those categories is therefore rejected by the
screen. The scorer will report it separately as a raw, pre-screen match, so
that it is visible but not counted as an accepted detection.

The scoring rules themselves (accepted detection, location-only match, raw
match, false positives on clean controls, off-target objections) are frozen
with the scorer in task A3/A4, not here.

## 7. The rule-only channel

`MUTATION_MANIFEST.csv` records, for every case, the findings of the Critic's
deterministic rules (Critic 0.5.0, recomputed at build time) and whether one is
at the target. This is a measured result, not a label. In the semantic
stratum the rules flag exactly `P1-M1a` and `P2-M1c` (the new
`CLAIM-ABSOLUTE-SAFETY` rule), and nothing else. They raise no finding on any
clean control.

## 8. Evidence available per condition

What each parent can offer the T/R/C conditions (task A3):

| Parent | T (text only) | R (retrieval only) | C (requirement-checked) |
| --- | --- | --- | --- |
| P1 | Graphs, outcomes, task context | Adds the one Phase 5 structured-retrieval pair. No registry records | **Unavailable**: no admitted checker assessment; physical checker admission is BLOCKED |
| P2 | Graphs, outcomes, task context | Adds the 9 synthetic records | **Unavailable**: no checker assessment in the parent |

C can therefore show only the admission status and its limitations for these
parents. No RQ3 checked-evidence advantage can be claimed from them.

## 9. Known limitations

- Two development groups, one real and one synthetic. No held-out data.
- The developer wrote the mutations and their expected objections, with AI
  coding assistance. Until an independent reviewer checks them, they are a
  developer-verified controlled benchmark, not an oracle.
- M2 can only be applied to P2, because P1 has no Solution nodes or records.
- P2's node IDs are not prefixed with the object (`E2` exists in all three of
  its graphs). The Critic rejects a model finding that names such a node
  without an `object_id` as ambiguous, so on P2 a model must name the object
  for its finding to count. P1's node IDs are prefixed (`milk_1:C1`).
- P1-M1a repeats a statement that Qwen has already seen. P2 was used to tune
  the Critic.
- The mutations are hand-written for clarity. They do not show how often such
  defects arise in real Drafter output.
