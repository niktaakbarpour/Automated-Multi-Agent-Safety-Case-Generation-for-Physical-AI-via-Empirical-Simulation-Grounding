# R1 v3 evidence records and citations

The original R1 v3 registry uses record schema `2.0.0` and the frozen R1 requirement version `r1-initial-table-support-v3-20261024`. Its standalone [record schema](registry_v3_record.schema.json) remains the interchange contract for the original recorder layout. A separately versioned Task 8C extension uses record schema `2.1.0` and the [Task 8C record schema](task8c_registry_v3_record.schema.json). Existing 2.0.0 records, source selectors, identifiers, and validation behavior are unchanged.

## Record types

- A `raw_measurement` identifies original HDF5 trajectory bytes by SHA-256 and provides one or more direct HDF5 paths for each named saved frame. Object pose, geometry, and contact records also bind the neighboring `simulator.xml` and corrected native map by SHA-256. Use `/geometries` for a standalone map or `/mapping/geometries` for a wrapped `NATIVE_PROFILE.json`. The registry checks the XML identity, native geometry count and ID ownership. A contact citation addresses the serialized contact group and requires valid native pairs consistent with the recorded count.
- A `derived_checker_event` is provisional. It binds the original prediction artifact and checker configuration by SHA-256. Its JSON pointer `/<prediction row>/events/<event index>` must select the stated event and interval in the frozen checker's output. The prediction must match the requirement, execution, object, trajectory hash and configuration hash. Registered v3 measurement inputs supply the cited saved frames for the same execution, task, object and trajectory.

Record IDs are `ev:` followed by the SHA-256 of canonical JSON for all fields other than `id`. The inclusive interval describes record scope. Only the explicitly listed saved frames are available to cite. Optional simulator endpoint timestamps describe those frames. Coverage between frames remains unknown.

## Registry API

Use `make_record(payload)` to add an ID to JSON metadata produced from the original artifacts. `validate_record(record)` checks the schema, content ID, and metadata invariants offline. Set `execution_id` and `task_id` from the trajectory's `global_episode_id` and `task_configuration_id` attributes.

Open a new database with `RegistryV3(path, source_root=approved_root, create=True)` or reopen it read-only with `RegistryV3(path, source_root=approved_root)`. The caller supplies the trusted source directory. Records use absolute, non-symlink artifact paths under that directory. `add(records)` validates every record and its referenced artifacts before committing the batch. Pose and geometry citations require the selected native rows in the saved arrays. `export()` returns the stored metadata in stable ID order.

For a measurement citation, call `resolve_citation(record_id, execution_id=..., task_id=..., object_id=..., trajectory_sha256=..., measurement_type=..., frames=[...])`. The scope and measurement type must match exactly. The call checks the requested saved frames and revalidates the source hashes, selectors and native bindings. Derived events are available in the registry export for audit. The export sets `empirical_admission_enabled` to `false`.

For Task 5, use the original trajectory and matching recorder artifacts to build v3 records. The existing RAG export is v2 evidence. Keep the evaluation-only human reference outside the source directory supplied to the agents.

For Task 8C, use `Task8CRegistryV3Adapter` from `registry_v3_task8c.py`; it delegates reconstruction to the recovered source adapter. Provide explicit trusted hashes for the source manifest, XML/native map/configuration files, runner-binding audit, and verified capture runner when constructing `RegistryV3`. Task 8C records are always development-only. Source validation and citation resolution do not constitute Checker admission; see the [2.1.0 trust boundary and supported source measurements](TASK8C_REGISTRY_V3_SCHEMA_2_1.md).

The prospective independent-cohort architecture and the nine-gate feasibility assessment are documented separately in [Task 8C registration and gate feasibility](TASK8C_PROSPECTIVE_REGISTRATION_AND_GATE_FEASIBILITY.md). This is a proposal and does not authorize new recordings or change admission criteria.

## CPU tests

Run from the repository root with Python 3.12 and the `h5py` and `jsonschema` versions in `requirements-m4-cpu.lock`.

```sh
python3.12 -m unittest discover -s evaluation/r1_v4/evidence_registry_gsn/tests -p test_registry_v3.py -v
python3.12 -m unittest evaluation.r1_v4.evidence_registry_gsn.tests.test_registry_v3_task8c -v
```

The tests use a synthetic HDF5 trajectory and a temporary SQLite database.
