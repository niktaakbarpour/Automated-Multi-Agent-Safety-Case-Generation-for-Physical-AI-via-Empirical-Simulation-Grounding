# Source-binding CPU checks

Run on Hestia, branch `research/m4-rq3-source-binding-20261123`, worktree `/disk/0/home/niktakbr/trustworthy_m4_rq3_source_binding_20261123`, using the Python environment described by the repository R1-v3 generalization README.

- Read the public R1 package build receipt and the documented generalization `inventory/inventory.json`; assert exactly 20 distinct canonical run IDs and matching expected trajectory SHA-256 receipts across both files: **20/20 pass**. This checks receipt consistency only.
- `os.path.isfile` on the exact 20 HDF5 paths named in the inventory: **0/20 present**.
- Attempted opening the first selected exact HDF5 path with the documented project Python/HDF5 environment: **blocked, `FileNotFoundError`**. No file hash or embedded ID was obtained.
- Checked the four proposed candidate receipt paths for HDF5, XML, metadata, and simulator-index presence: these source artifacts are not present at the recorded paths.
- No fallback-root search, symlink traversal, archive scan, or private reviewer-data access was performed.
- Request validation was not run because no source-bound request exists; this is intentionally not reported as a pass.

The scope, approval, and independence facts are taken from repository artifacts. Detailed per-execution receipt fields and path availability are in `SOURCE_BINDING_AUDIT.csv`.
