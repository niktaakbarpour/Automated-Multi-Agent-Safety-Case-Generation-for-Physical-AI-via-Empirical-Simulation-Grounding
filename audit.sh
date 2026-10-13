#!/bin/bash
set -euo pipefail
R=/local/home/niktakbr/trustworthy_project
exec /local/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/bin/python -u "$R/src/audit_imports.py" /disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero "$R/reports/existing_annotations_audit.json" > "$R/reports/audit.log" 2>&1
