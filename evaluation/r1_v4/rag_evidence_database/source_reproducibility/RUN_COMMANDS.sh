#!/bin/sh
# Reference commands for a fresh, isolated run. Preserve validated WORK outputs.
# Inventory outputs contain current host collection dates; do not expect their bytes to reproduce historical attestations.
set -eu
[ "$(hostname)" = hestia ]
repo=/disk/1/data/niktakbr/trustworthy-phase16
retrieval_packages=/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages
native_packages=/disk/0/home/niktakbr/smolVLA_libero/.venv/lib/python3.12/site-packages
system_packages=/usr/local/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages:/usr/lib/python3.12/site-packages
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$repo:$retrieval_packages:$system_packages"
cd "$repo"
module=evaluation.r1_v4.rag_evidence_database.source_reproducibility
python3 -S -m "$module.verify_baseline"
python3 -S -m "$module.inventory"
python3 -S -m "$module.archive_audit"
python3 -S -m "$module.dependencies" retrieval
PYTHONPATH="$repo:$native_packages:$system_packages" python3 -S -m "$module.dependencies" native
python3 -S -m "$module.clocks"
python3 -S -m "$module.build"
python3 -S -m "$module.validate"
python3 -S -m "$module.verify_claims"
python3 -S -m "$module.benchmarks" f
python3 -S -m "$module.benchmarks" g
python3 -S -m "$module.benchmarks" h
python3 -S -m "$module.semantic_benchmark"
python3 -S -m "$module.regressions"
python3 -S -m "$module.reports"
python3 -S -m "$module.verify_graph_release"
python3 -S -m "$module.seal_release"
# Verify with an externally trusted manifest hash; do not blindly trust a sibling checksum file.
