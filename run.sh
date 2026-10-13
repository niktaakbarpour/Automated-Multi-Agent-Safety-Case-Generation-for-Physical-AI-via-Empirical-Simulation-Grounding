#!/bin/bash
set -euo pipefail
R=/local/home/niktakbr/trustworthy_project
PYTHON=/local/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/bin/python
export PYTHONPATH="$R/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
exec "$PYTHON" "$R/src/collect.py" --project "$R"
