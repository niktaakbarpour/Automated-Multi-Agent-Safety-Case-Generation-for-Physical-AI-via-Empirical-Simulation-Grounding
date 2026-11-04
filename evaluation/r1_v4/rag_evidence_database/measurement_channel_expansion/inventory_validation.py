"""Independent normalized-coverage round trip and exclusion verification."""
import csv,json,sqlite3,itertools
from .channels import HERE,WORK,BASE
from .validate import save

def run():
 with (HERE/'CHANNEL_INVENTORY.csv').open() as f:channels={r['channel_key']:r['canonical_channel_id'] for r in csv.DictReader(f)}
 with (HERE/'EXECUTION_SOURCE_BINDINGS.csv').open() as f:sources={r['source_key']:r for r in csv.DictReader(f)}
 profiles=json.loads((HERE/'VALUE_PROFILES.json').read_text());count=0;executions=set();variants=set()
 with (WORK/'FULL_CHANNEL_COVERAGE_MATRIX.csv').open() as a,(HERE/'CHANNEL_COVERAGE_MATRIX.csv').open() as b:
  for original,normalized in itertools.zip_longest(csv.DictReader(a),csv.DictReader(b)):
   assert original is not None and normalized is not None
   s=sources[normalized['source_key']];p=profiles[normalized['value_profile_key']]
   assert normalized['execution_key']==s['execution_key']
   for k in ('execution_id','task_id','variant_id','source_path','source_sha256'):assert original[k]==s[k]
   assert original['channel_id']==channels[normalized['channel_key']]
   assert original['recorded_occurrences']==normalized['recorded_occurrences'] and original['saved_frames_denominator']==normalized['saved_frame_denominator']
   assert original['dtype_shape_counts']==p['dtype_shape_counts'] and original['phase5f_representation']==p['phase5f_representation']
   count+=1;executions.add(s['execution_id']);variants.add(s['variant_id'])
 c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);indexed={r[0] for r in c.execute("select execution from rag_scope_status where status='indexed'")};excluded={r[0] for r in c.execute("select execution from rag_scope_status where status!='indexed'")}
 assert executions==indexed and not executions&excluded and len(variants)==104 and count==816800
 save('INVENTORY_VALIDATION.json',dict(passed=True,coverage_rows=count,indexed_executions=len(executions),variants=len(variants),channel_keys=len(channels),source_bindings=len(sources),scope_leakage=0,qualification='All normalized source/channel/type/coverage fields match expanded matrix; exact example selectors also retained in external original matrix and per-execution inventories.'))
 print('Inventory round trip passed',count,flush=True)
if __name__=='__main__':run()
