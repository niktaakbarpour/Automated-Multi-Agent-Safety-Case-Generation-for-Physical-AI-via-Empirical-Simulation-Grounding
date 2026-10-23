"""Lossless CSV import envelope, does not decide labels or edit legacy records."""
import csv,json,sys
from pathlib import Path
p=Path(sys.argv[1])
with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
print(json.dumps({'schema_version':'human-review-csv-envelope-v1','source_csv':p.name,'records':rows},indent=2))
