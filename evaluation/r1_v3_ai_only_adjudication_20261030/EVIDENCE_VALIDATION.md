# Evidence validation blocked at compute-node archive access

Fresh payload files verified: **0**. Complete freshly verified NV cases: **0/20**. All 20 remain matched at receipt level only.

Fir control socket works. Scratch quota report: 1961 MiB / 19 TiB and 67K / 1000K files. Selected 480 receipt-listed files total 2,697,453,653 bytes. Source archives report HSM exists archived (0x9), with no released flag; no restore request was issued.

Authorized CPU account def-hvpham_cpu supports normal jobs. Job 1525782 ran on fc30554 and failed with exit 1 before opening the first archive: the nearline path was absent in that compute-node namespace. The same original 34,351,513,600-byte archive remains visible from login2. This demonstrates path availability differs between these execution contexts; it does not demonstrate missing or corrupted archive payloads.

No login-node heavy extraction/decoding was performed. No controller, receipt or original archive was modified. A private scratch staging directory and header-only STAGING_MANIFEST.csv remain for traceability. The default and inspected scientific Python environments also lacked h5py; a supported HDF5 runtime is needed after archive access is resolved.

Evaluator 3 has not inspected original payloads or issued decisions. Its seal, three-evaluator adjudication, provisional reference and exploratory scores do not exist. No human approval gate was changed. Earlier judgments were not opened during this task.

Next operational step: obtain the documented Fir data-transfer-node or other permitted extraction route with access to both nearline and scratch, or stage the two required immutable containers to scratch through an authorized transfer service before CPU extraction. Confirm the exact host/path/procedure before resubmitting; do not repeat the failed job unchanged. No additional authentication or compute-account authorization is currently the blocker.
