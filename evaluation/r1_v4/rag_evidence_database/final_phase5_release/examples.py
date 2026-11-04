"""Executable source-verified examples, no safety claims or agents."""
import json,copy
from .api import StructuredRetriever
from .config import *
from .fixtures import first,request

def run():
 r=StructuredRetriever();c=first(r);queries=[]
 q=request(c);queries.append(('valid_single',q,'COMPLETE WITHIN VERIFIED CONTRACT'))
 q=request(c);o=copy.deepcopy(q['obligations'][0]);o.update(id='finger',family=CHANNELS[0],field=REGISTRY[CHANNELS[0]]);q['obligations'].append(o);queries.append(('complete_multisource',q,'COMPLETE WITHIN VERIFIED CONTRACT'))
 q=request(c);o=copy.deepcopy(q['obligations'][0]);o.update(id='unavailable_action',family='action_metadata',field=REGISTRY['action_metadata'],selector=dict(kind='frames',start=0,end=0));q['obligations'].append(o);queries.append(('partial',q,'PARTIAL'))
 q=request(c);q['obligations'][0]['coordinate_frame']='world';queries.append(('unsupported_world',q,'UNSUPPORTED'))
 q=request(c);q['variant_id']='wrong-variant';queries.append(('wrong_variant',q,'INVALID SCOPE'))
 q=request(c);q.update(assurance='provenance_complete',provenance=dict(level='release_graph'));queries.append(('strict_provenance_failure',q,'UNSUPPORTED'))
 results=[]
 try:
  for name,q,expected in queries:
   b=r.retrieve(q);assert b['completeness_status']==expected,(name,b);results.append(dict(name=name,request=q,bundle=b));print(name,b['completeness_status'],flush=True)
 finally:r.close()
 (WORK/'EXECUTABLE_EXAMPLE_RESULTS.json').write_text(json.dumps(results,sort_keys=True,indent=2));return results
if __name__=='__main__':run()
