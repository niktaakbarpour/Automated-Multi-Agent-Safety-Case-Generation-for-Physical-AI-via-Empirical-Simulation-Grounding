#!/bin/sh
set -eu
[ "$(hostname)" = hestia ]
eval_run=${1:-operator_replay}
case "$eval_run" in ''|*[!a-zA-Z0-9_-]*) echo 'Use a simple new run name' >&2; exit 2;; esac
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/disk/1/data/niktakbr/trustworthy-phase16:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/local/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages:/usr/lib/python3.12/site-packages
export HF_HOME=/disk/1/data/niktakbr/trustworthy-phase5j-working/hf-cache
export XDG_CACHE_HOME=/disk/1/data/niktakbr/trustworthy-phase5j-working/cache
cd /disk/1/data/niktakbr/trustworthy-phase16
python3 -S -m evaluation.r1_v4.rag_evidence_database.readiness_evaluation.run --split final --run "$eval_run"
