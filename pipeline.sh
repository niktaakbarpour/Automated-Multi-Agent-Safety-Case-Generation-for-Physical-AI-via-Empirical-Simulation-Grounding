#!/bin/bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "$0")" && pwd)
export PYTHONPATH="$project_dir/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
exec /local/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/bin/python "$project_dir/src/pipeline.py" --project "$project_dir" "$@"
