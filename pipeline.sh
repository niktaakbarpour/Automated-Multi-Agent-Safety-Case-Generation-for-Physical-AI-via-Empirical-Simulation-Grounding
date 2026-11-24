#!/bin/bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "$0")" && pwd)
export PYTHONPATH="$project_dir/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
python_bin="${PYTHON:-python}"
if ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "Python interpreter '$python_bin' was not found. Activate an environment with Python installed or set PYTHON." >&2
  exit 127
fi
exec "$python_bin" "$project_dir/src/pipeline.py" --project "$project_dir" "$@"
