"""Development examples use actual registered source scope, not reserved recordings."""
import json
from .config import *
def request(c,family=CHANNELS[2],frame=20):
 o=dict(id='measurement',execution_id=c['execution_id'],family=family,field=REGISTRY[family],mandatory=True,selector=dict(kind='frames',start=frame,end=frame))
 return dict(schema_version=VERSION,execution_id=c['execution_id'],task_id=c['task_id'],variant_id=c['variant_id'],assurance='verified_source_values',provenance=dict(level='source_identity'),obligations=[o])
def first(engine):return json.loads(engine.backend.catalogue.execute('select body from catalogue order by execution limit 1').fetchone()[0])
