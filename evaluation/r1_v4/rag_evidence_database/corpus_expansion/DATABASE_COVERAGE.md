# Validated Phase 5D coverage

One new task profile and one bounded batch are complete. Object task 02 (salad dressing into the basket) contributes 49 executions, excluding historical preflight episode 000. All 60 reserved transfer-evaluation IDs and all 38 cross-scene preflight examples remain excluded. New data are corpus_expansion / unclassified_database_use_only, not automatically calibration-development evidence.

Preserved: 40 development executions and all 11,830 Phase 5C IDs. Added: 49 executions and 9,961 records. Total: 89 executions, 21,791 records, 17,833 saved frames and 2,000 historical catalog entries. New source closure: 443 files (441 episode files and two task sources), 3,656,363,457 bytes, all freshly hash-verified. Prior sources and releases are unchanged.

Raw measurement references: 20,250, with 3,375 each of pose, contact, native geometry, robot state, timestamp and camera reference. Source documents: 1,531. Provisional AI interpretations: ten, all inherited and separately attributed. No human ground truth or new event labels are generated. Metadata/instruction/requirement/calibration/limitation units each number 89; object and static-fixture identities each number 543.

Coverage checks pass all 3,258 execution/object/measurement-type scopes: 40 times 5 times 6 plus 49 times 7 times 6. Every saved index matches source counts. Forty-nine terminal-gap cases check all six types (294 checks). This is discrete recorded-state coverage, never continuous physical coverage or a negative safety certificate.

Task 00 keeps its original five-object/table profiles. Task 02 independently binds seven objects, 26 bodies, 58 qpos entries, 51 qvel entries, 110 flattened-state entries and 161 native geometry IDs. Its static fixture is floor, collision geometry 6; task 00's table IDs 10–15 are not reused. Equal geometry count does not imply equal layout. Compilation resolves all IDs, including anonymous entries if present; the new model happens to have named geometry throughout. No MjData, stepping, rollout or rendering occurs.

Remaining unindexed: 1,911 executions — 60 reserved, 38 preflight-exposed and 1,813 other unprofiled candidates. Two task partitions have registered profiles; Long task 01 matches old XML but remains evaluation-restricted; 37 other tasks require new profiles. No second batch begins.
