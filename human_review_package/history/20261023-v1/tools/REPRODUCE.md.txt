# Reproduce exports (coordinator only)
No reviewer needs to run code. The source recordings are intentionally not redistributed in their original HDF5 form. The manifest contains their content hashes and logical episode paths. Obtain the matching original release and these four existing development recordings through authorized project access. Do not access held-out episodes, run robot experiments or rerun models/checkers.

Using an existing Python environment with numpy, h5py, Pillow and system ffmpeg/ffprobe:

```sh
python human_review_package/tools/build_review.py --repo /path/to/trustworthy_project --recordings /current/verified/path/to/long/task_00
python human_review_package/tools/verify_package.py human_review_package
```

The builder writes a new human_review_package folder, or human_review_package_v20261023 if the first exists; it refuses to overwrite either. It reads only episodes 000, 001, 002 and 014 in mode r, checks development membership, task/run IDs, corrected XML/native geometry identity and action/frame mapping. It does not import the checker or a simulator. Each video's encoder arguments and exact source-frame sequence are in evidence_manifest.json. H.264 is lossy; raw image hashes audit the original scene arrays, while checksums audit delivered bytes. Export sequence is deterministic by frame index, with 20 or 5 fps and unchanged scene content. Reproducing byte-identical encodings may depend on ffmpeg/Pillow versions.

Normal→slow changes playback timing and speed caption only. No optical flow or generated intermediate images. The verifier decodes videos, checks counts, durations, source sequences and decoded scene similarity, resolves relative links, compares reviewer forms, and checks blank human fields. SHA256SUMS covers all package files except itself. Run checks on an extracted copy as well.
