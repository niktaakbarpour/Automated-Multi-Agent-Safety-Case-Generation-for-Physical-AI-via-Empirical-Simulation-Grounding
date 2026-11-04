"""Independently check every materializable release/contract relationship endpoint."""
import json,sqlite3
from evaluation.r1_v4.provenance import digest
from .config import HERE,WORK
from .graph_release import supplement

def run():
 g=json.loads((HERE/'DEPENDENCY_GRAPH.json').read_text());c=sqlite3.connect('file:'+str(WORK/'expanded.sqlite')+'?mode=ro',uri=True);s=g['release_and_extraction_links'];assert s==supplement(c,g['database_sha256'])
 ids={r[0] for r in c.execute('select id from i_nodes')}|{n['id'] for n in s['nodes']};counts=[]
 for rule in s['relationship_views']:
  rows=c.execute(rule['sql']).fetchall();assert len(rows)==rule['edge_count'];assert all(a in ids and b in ids for a,b,r in rows);counts.append(len(rows))
 assert all(e['source'] in ids and e['target'] in ids and e['basis'] for e in s['edges'])
 result=dict(passed=True,explicit_additional_nodes=s['explicit_nodes'],explicit_additional_edges=s['explicit_edges'],virtual_edges=sum(counts),relationship_view_counts=counts,deterministic_reconstruction_digest=digest(s),historical_runtime_attested=False)
 (WORK/'GRAPH_RELEASE_VALIDATION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
