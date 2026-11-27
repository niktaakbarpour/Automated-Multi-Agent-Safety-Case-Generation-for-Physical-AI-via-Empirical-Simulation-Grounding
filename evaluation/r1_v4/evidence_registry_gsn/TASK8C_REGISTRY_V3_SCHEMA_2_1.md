# Task 8C RegistryV3 source schema 2.1.0

**Status:** versioned development extension. It does not modify RegistryV3 2.0.0, the frozen R1 v3 requirement or Checker, or the physical admission protocol.

## Source and version boundary

RegistryV3 2.0.0 continues to accept the original `/frames/<frame>/simulator/...` recorder layout. RegistryV3 2.1.0 accepts only the Task 8C custom HDF5 layout version `1.0.0`, using `/observations`, `/physics`, and `/contacts`, and only the recovered `task8c-r1v3-source-adapter-1.0.0`. The 2.1.0 validator dispatches by record version; it does not reinterpret or migrate existing records.

The source reader is `evaluation/r1_v4/task8c_r1v3_adapter/task8c_adapter.py`. `registry_v3_task8c.py` delegates source reconstruction and checking to `prepare_case`; it defines scope-bound RegistryV3 records and citation verification, not a second measurement algorithm.

## Measurements that may be registered

For the bound `cream_cheese_1` native model only, the adapter can create separate raw-measurement records for:

| Record family | Recorded selectors | Meaning and limit |
| --- | --- | --- |
| `object_pose` | `/physics/body_xpos`, `/physics/body_xquat` | Native body position and quaternion for body 22. |
| `native_geometry` | body position/quaternion plus bound XML and native map | Geometry reconstructed using the recovered adapter and bound MuJoCo transforms. It is explicitly marked reconstructed, not a direct HDF5 geometry channel. |
| `contact` | `/contacts/*` and `/physics/ncon` | Native contact rows and per-sample count. This is contact observation, not validated load-bearing support, reaction force interpretation, or a force threshold. |
| `timestamp` | `/observations/source_frame`, `/observations/time`, `/physics/time_after` | Saved-frame/native-sample index and timestamps; it does not establish continuous inter-frame coverage. |

Each record binds the recording SHA-256, manifest row, execution and task identity, source-layout and adapter versions, protected-object identity, XML and native mapping hashes, body/geometry IDs, exact HDF5 paths, saved frames, native sample indices, timestamps, temporal interval, uncertainty/limitations, and development-only status. Saved frame `f` maps to native sample `25*f`; records use the saved-frame scope 10 through 257. Contact completeness is verified against the source arrays and `ncon` by the recovered adapter. A missing or malformed required channel fails registration; values are not imputed.

## Trust and admission boundary

The caller must explicitly configure trusted SHA-256 values for the source manifest, model/configuration artifacts, runner-binding audit, and verified capture runner. The registry recomputes file hashes, checks that artifacts are regular files under the approved source root, binds case/execution/group/recording/XML to the source manifest, checks runner availability against the separate runner-binding audit, and calls the recovered adapter to validate native bindings and source measurements. An unverified runner may be retained for diagnostics but its citation cannot resolve.

The API requires these trust anchors explicitly; it does not infer them from the record:

```python
adapter = Task8CRegistryV3Adapter(
    source_root=approved_source_root,
    source_manifest=task8c_source_manifest,
    runner_binding_manifest=runner_audit,
    trusted_manifest_hashes={expected_source_manifest_sha256},
    simulator_xml=simulator_xml,
    native_mapping=native_mapping,
    physical_config=physical_config,
    checker_config=frozen_checker_config,
    entity_inventory=entity_inventory,
)
records = adapter.build_records(
    case_id=case_id,
    recording_path=recording_path,
    runner_status="VERIFIED",
    runner_source=exact_capture_runner,
    frames=list(range(10, 258)),
)
registry = RegistryV3(
    registry_path,
    source_root=approved_source_root,
    create=True,
    trusted_task8c_manifest_hashes={expected_source_manifest_sha256},
    trusted_task8c_artifact_hashes=expected_artifact_hashes,
    trusted_task8c_runner_hashes={expected_capture_runner_sha256},
)
registry.add(records)
```

`expected_artifact_hashes` pins the keys `simulator_xml`, `mapping`, `physical_config`, `checker_config`, `entity_inventory`, and `runner_bindings`. Use `runner_status="UNVERIFIED"` and `runner_source=None` only for diagnostic registration; such sources cannot resolve as citations. Even a resolved verified-runner citation stays development-only and cannot pass the physical admission pathway.

Registry resolution is technical provenance and measurement validation only. Every 2.1.0 record has `development_only: true`; the admission evidence ledger returns it as blocked. No 2.1.0 citation can satisfy independent reference, independent review, or any of the nine physical gates. The registry does not create Checker predictions, derived Checker events, or human judgments. Those are separate artifacts and interfaces.

The Task 8C archive is development/regression material. The source groups used for development cannot be relabelled as an independent holdout cohort. Externally induced falls and stable shams are distinct from naturally occurring policy-execution failures.

## Unsupported claims and conditions

This schema does not supply policy trajectories/actions, intermediate saved frames, continuous-time coverage, contact reactions interpreted as support force, validated support loss, validated falling witnesses, floor-contact attribution as an event, a physical safety verdict, or generalization to other models/objects/recording layouts. If native contact attribution, a required source field, complete temporal coverage, exact provenance, or the bound object mapping is missing or inconsistent, registration or citation resolution fails. Uncertainty that the source does not quantify remains unknown; it is not estimated from reviewer labels.

## Tests

Run with the repository's complete Python 3.12 CPU environment:

```sh
python -m unittest evaluation.r1_v4.evidence_registry_gsn.tests.test_registry_v3_task8c -v
python -m unittest evaluation.r1_v4.evidence_registry_gsn.tests.test_registry_v3 -v
python -m unittest evaluation.r1_v4.checker_v3_admission.tests.test_admission -v
```

The Task 8C unit tests use synthetic HDF5 fixtures. The separate development verification report uses only existing immutable Task 8C recordings and never reads human-reference labels or runs Checker evaluation.
