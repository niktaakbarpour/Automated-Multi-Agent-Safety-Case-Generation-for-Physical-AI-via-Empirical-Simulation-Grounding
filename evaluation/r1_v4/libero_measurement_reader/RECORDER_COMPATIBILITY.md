# Recorder compatibility

Verified scope: the four restored OpenVLA-OFT long/task00 executions only, recorder/dataset/HDF5 schema 4.0. Model moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10 revision 638918f3d1c2e43a39a8a20772bdb8b91835e4b7, model configuration 85620572476d4a08fc0d, task configuration 2448c758145ae5ad500f. The metadata and producer manifests are exact original bytes. No benchmark-wide or other-checkpoint compatibility is claimed.

| Channel | Supported stored contract | Qualification |
|---|---|---|
| Identity/provenance | Execution/episode/seed/model/task/version, manifest/completion hashes | Exact four-run scope; no inferred identities |
| Endpoint state | time scalar, qpos65, qvel57, ctrl9, flattened123, native float64 | Flat state agrees exactly with time/qpos/qvel; mixed model coordinates retained |
| Initial state | Recorded benchmark_initial_state123 equals frame0 flattened state | Task archive bytes verified; archive pickle not deserialized |
| Native geometry | body29x3, body quaternion29x4 wxyz; geom161x3/161x9 | Complete map, native ownership, world transforms; exact model only |
| Table pieces | All collision IDs10–15 invariant in saved poses | Lower structure15 retained; visual mesh9 is not collision support |
| Contacts | Native IDs/dist/pos and count equal ncon | Complete recorded bundle per snapshot only; no contact normals/forces |
| Robot/gripper/objects | Stored raw observables plus native body/geom channels | Raw observable frame/unit/quaternion conventions explicitly unverified |
| Optional simulator arrays | qacc, act, sensordata, actuator_force, cfrc_ext, cvel | Availability/shape/dtype retained; no per-contact force reinterpretation |
| Cameras | Two 256x256x3 uint8 dataset references per frame | Pixels not decoded; exposure time null; display MP4 rotation not applied to raw arrays |
| Time/coverage | Consecutive frames, stage/control offsets, transition endpoint-time equality | Saved projection only; exact cache/exposure phases uncalibrated |

Native geometry/body/contact data are last-forward caches; endpoint qpos/qvel are a different bundle. Historical one-substep lag evidence remains qualified, not a fixed synchronization correction. Raw observables may have another phase, including quaternion/frame conventions that this reader deliberately does not convert. No physical tolerance, alignment window, persistence threshold or velocity estimator is added.

SOURCE_CONTRACT.json pins the unchanged corrected native map, constraints and NativeGeometryIndex helper; output reader_binding hashes the core reader code. The retained 512-epsilon transform guard checks numerical identity and arithmetic consistency only. Required unsupported/incompatible input yields structured failure; optional unavailable channels remain named diagnostics. External/soft links and external/virtual datasets are rejected before dereference.

Typed V4 observations carry unknown physical truth and null uncertainty bounds. They are not empirical witnesses, and there is no runtime adapter/profile registration. The authoritative R1 v2.0 and Phase2A admission restrictions remain unchanged.
