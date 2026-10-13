#!/bin/bash
set -euo pipefail
R=/local/home/niktakbr/trustworthy_project
exec /bin/bash "$R/run.sh" > "$R/reports/collection.log" 2>&1
