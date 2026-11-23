#!/bin/bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$project_dir/reports"
exec /bin/bash "$project_dir/run.sh" > "$project_dir/reports/collection.log" 2>&1
