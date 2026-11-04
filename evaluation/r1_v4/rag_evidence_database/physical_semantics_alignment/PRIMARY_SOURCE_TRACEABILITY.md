# Primary-source traceability

Sources were inspected on Hestia. Recorder/run_oft hashes match all execution metadata. The snapshot writes raw_observation and simulator fields directly; run_oft applies policy preprocessing separately and records native eight-action chunks. Robot/single-arm getters use qpos/qvel addresses in model order; exact saved indexes and compiled XML establish actual component identities.

MuJoCo 3.8.1 was used for identity compilation and algebraic validation; no newer-version documentation was substituted. Installed mjdata.h/mjmodel.h bytes match pinned official 3.8.1 headers (MUJOCO_HEADER_COMPARISON.json). Compiler RECORD hashes, XML/assets and per-execution native indexes are retained in model maps. Metadata declares MuJoCo 3.8.1 and robosuite 1.4.0. Historical binary attestation is unavailable.

engine_forward.c documents actuator gain/bias/limiting, moment mapping and semi-implicit Euler integration. engine_util_misc.c defines configuration integration. Observable/base/binding code explains refresh and cache ordering. Headers identify actuator_force/ncon; these are not contact-force/event labels. Native model types, gears, gains and biases support the tested equations. Interpretations include audit/validation/source-manifest hashes and original source/model/metadata lineage.

| Inspected source | SHA-256 |
|---|---|
| /disk/1/data/niktakbr/trustworthy-phase16/reports/fall_review_v2_20261016/source_evidence/recording_base.py | `7ce898669c01fd3a6b7a7c3217a6326464ff9343aab32c25fe4a16b08b1f5268` |
| /disk/1/data/niktakbr/trustworthy-phase16/reports/fall_review_v2_20261016/source_evidence/run_oft.py | `418a48ad136d0734039eef6b4f394d28c0ee8f14daea26035e475b4ad94f9bfc` |
| /disk/1/data/niktakbr/trustworthy-phase16/reports/fall_review_v2_20261016/source_evidence/robosuite__environments__base.py | `3d55a1d8b0350478b7e7e8d1c7a1250c8f173b69a67016ecb9e65c6965e741f6` |
| /disk/1/data/niktakbr/trustworthy-phase16/reports/fall_review_v2_20261016/source_evidence/robosuite__utils__binding_utils.py | `f5c8aada3bc85d3e66b9c4719c62892f0a32e4ea3489f66cc9abcaa170282c04` |
| /disk/1/data/niktakbr/trustworthy-phase16/reports/fall_review_v2_20261016/source_evidence/robosuite__utils__observables.py | `0368fbfca3b732915819f9618a30aa38b559cc343a45fc15fab8ef0d5e8f7446` |
| /disk/1/data/niktakbr/trustworthy-phase16/reports/fall_review_v2_20261016/source_evidence/robosuite__macros.py | `d09834e770db690f43f46d6dc93605efe316b8b5eb7fe6cf2bc1647df95a302d` |
| /disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite/robots/robot.py | `7a3a98eb75b4e7cb1b822a918d0c693d441356279a8e796cfc02eb1fd5963f23` |
| /disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite/robots/single_arm.py | `d233b1b785e8f88ffb5df1357666b02a397ae930ce98181b079e0496ab35fc57` |
| /disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite/models/grippers/panda_gripper.py | `a3760a8fc4599fa6f79914304b82466f3c1bda1a945943ca693bb57f00dc59eb` |
| /disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite/models/robots/robot_model.py | `baa86c64ae55ebbbabda9b6fc47c8e9bf1ed07e557315e999712b3082728dddc` |
| /disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite/models/base.py | `a5d7bc8c7f317735b76347c0038d3c0888e592da0ee059d0f937eb9f1b272b34` |
| /disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite/utils/observables.py | `0368fbfca3b732915819f9618a30aa38b559cc343a45fc15fab8ef0d5e8f7446` |
| /disk/1/data/niktakbr/trustworthy-phase5h-working/primary/src__engine__engine_forward.c | `5f9683631cc1c72cb28cd23d8503216324ec4ea96346f51780ff5609616a7950` |
| /disk/1/data/niktakbr/trustworthy-phase5h-working/primary/src__engine__engine_util_misc.c | `fd4bb18e85ca3b068896ac857e63bde54f2e0966d2fb3f26e6e2d0c5ad8a7701` |
| /disk/1/data/niktakbr/trustworthy-phase5h-working/primary/include__mujoco__mjdata.h | `1be8300051e0ecfb69c4c88b2d190d7f23c32a713434fb19cec7b06d254ecd16` |
| /disk/1/data/niktakbr/trustworthy-phase5h-working/primary/include__mujoco__mjmodel.h | `4437bd2f26323108cc6be2e84b547234c96f845b55441ebaa5ff2dd8b10e7c02` |

Pinned upstream references:
- https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/src/engine/engine_forward.c — SHA-256 `5f9683631cc1c72cb28cd23d8503216324ec4ea96346f51780ff5609616a7950`
- https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/src/engine/engine_util_misc.c — SHA-256 `fd4bb18e85ca3b068896ac857e63bde54f2e0966d2fb3f26e6e2d0c5ad8a7701`
- https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/include/mujoco/mjdata.h — SHA-256 `1be8300051e0ecfb69c4c88b2d190d7f23c32a713434fb19cec7b06d254ecd16`
- https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/include/mujoco/mjmodel.h — SHA-256 `4437bd2f26323108cc6be2e84b547234c96f845b55441ebaa5ff2dd8b10e7c02`

These establish model definitions, not hardware calibration. Installed robosuite sources are version-matched explanatory evidence; cache clocks and binary history remain conditional/unresolved. Independent recorded-value/model comparisons provide separate evidence, instead of verification from variable names or absence of counterexamples.
