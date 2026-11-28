#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: audit.sh SOURCE_RESULTS OUTPUT_JSON" >&2
  exit 2
fi
if [[ ! -d "$1" || -e "$2" || -L "$2" ]]; then
  echo "Provide an existing source directory and a new output path." >&2
  exit 2
fi

project_dir=$(cd -- "$(dirname -- "$0")" && pwd)
exec "${PYTHON:-python}" -u "$project_dir/src/audit_imports.py" "$1" "$2"
