# RQ4 publication audit

The input per-output CSV SHA-256 is `c67fc529501030841f198a12b3ffa71e454866f662432261bc4da2c44b8c7727`. The public `RQ4_PER_OUTPUT.csv` is a labeled derivative, not the immutable source table. It omits `blind_item_id`, `new_statement`, `validators_failed`, `refused_edit_reasons`, and raw `new_objections`; the only retained objection information is the already-scored count. It retains case/output identifiers, condition, completion status, and approved judgment fields without altering a judgment.

The case error analysis removes the blind item code and raw revised claim prose while retaining a paraphrased semantic explanation of the one aggregate failure. The numerical summary removes reviewer identities, personal attribution, exact consensus timestamp, and private review metadata. The coordinator-confirmed agreement limitation remains.

Excluded from public staging: confidential reviewer forms, sealed coordinator key/mappings, human-submission integrity data, full raw provenance containing local paths, raw model response files, and private reconstruction commands. No reviewer identity, blind identifier, credentials, tokens, SSH details, private key, or other users' workload details are published.

Frozen-source SHA-256 values: raw per-output `c67fc529501030841f198a12b3ffa71e454866f662432261bc4da2c44b8c7727`; per-case `4bfee8745844b817e56d6307f029be37f141fb5226e52dea2acfbb4ed018654d`; aggregate `22cb73a74d6f24fe93252bbb1dc596e0c68dee22e4eaec745af53f61b398b8f9`; manuscript tables `b6ebdbca9d7b05c970953c8fb6d89edaf7a8a4e7f79072a7c98d246365ec037b`; error analysis `969452b9b034635f6cbf84f02dce80e0a989962e334555b26456ec2ae02092b6`.
