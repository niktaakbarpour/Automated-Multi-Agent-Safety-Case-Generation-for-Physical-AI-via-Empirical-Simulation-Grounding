#!/bin/bash
set -euo pipefail
R=$(cd -- "$(dirname -- "$0")" && pwd)
PYTHON="${PYTHON:-python}"
export PYTHONPATH="$R/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python interpreter '$PYTHON' was not found. Activate an environment with collection dependencies or set PYTHON." >&2
  exit 127
fi
exec "$PYTHON" "$R/src/collect.py" --project "$R"
