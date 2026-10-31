# Hestia evidence audit

Hestia session 95742 was reused. Complete original cases: 0/20 at the exact mapped source paths. For every case, trajectory.h5, both original camera MP4s, metadata.json, simulator.xml, simulator_index.json and completion.json are absent. These original components require restoration for all 20 cases. Exact Alliance locations and hashes remain in fir_receipt_matches.json.

The preserved neutral reviewer-1 package remains available on disk1. Fresh verification matched all 597 checksum entries with zero failures. Both complete camera videos per case were decoded by ffprobe: all 40 streams match expected case frame counts at 20 fps. Frame-reference row counts/endpoints and presence of poses/contacts were checked; frame-to-physics synchronization and continuous visibility have not been established. Geometry exports are derived measurements, not fresh raw-HDF5 verification.

Available disk0 space: 386,032,922,624 bytes, already below the requested 500-GB reserve. No disk0 writes/deletions performed. Disk1 has 1,663,988,498,432 bytes available; any future restoration/output belongs there. No cleanup or capacity remediation is authorized.

The documented Hestia-to-Fir socket /tmp/hestia-fir-transfer-32484-20261026/fir-direct.sock is absent. The system /usr/bin/ssh also rejects /etc/ssh/ssh_config option WarnWeakCrypto; a per-command -F /dev/null permitted the socket-only check without changing configuration. No replacement authentication or controller restart was attempted. Restoration remains blocked by absence of an authenticated Hestia-to-storage route and a verified permitted archive extraction route. The Mac Fir socket is not a Hestia socket. No further Alliance compute jobs were submitted.

No Evaluator 3 decision, adjudication, reference or exploratory score is claimed. Earlier evaluator judgments were not opened. No archive, original evidence or human-approval mechanism was modified. Hestia source package: /disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_1_R1_20/. Inventory JSON distinguishes source absence from surviving derived package evidence.

Next: establish a user-authenticated Hestia-to-Fir storage connection using the supported SSH client and identify the permitted storage transfer/extraction endpoint. Restore only the exact missing raw files to a new disk1 directory, match member hashes, then perform raw-state validation and evidence-first assessment. No computational results are ready for final Alliance archival yet.
