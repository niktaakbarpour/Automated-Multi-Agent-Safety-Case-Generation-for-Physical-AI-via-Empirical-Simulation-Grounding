import sqlite3,json,h5py,re,time,collections,os
from pathlib import Path
root=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working')
c=sqlite3.connect('file:/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite?mode=ro',uri=True)
rows=c.execute("SELECT e.execution_id,json_extract(e.body,'$.source_path'),json_extract(e.body,'$.source_sha256'),b.task_id,b.variant_id,b.body FROM evidence e JOIN rag_execution_env b ON e.execution_id=b.execution WHERE e.kind='raw_measurement' GROUP BY e.execution_id ORDER BY e.execution_id").fetchall()
assert len(rows)==432
out=root/'inventory';out.mkdir(exist_ok=True)
def norm(n):return re.sub(r'(?<=/)[0-9]+(?=/|$)','{index}',n)
def jvalue(v):
 try:return v.tolist()
 except AttributeError:return str(v)
for i,(execution,p,h,task,variant,bind) in enumerate(rows):
 dest=out/(execution+'.json')
 if dest.exists():continue
 stats={};attrs={};frames=[]
 with h5py.File(p,'r') as f:
  frames=[{'key':k,'attrs':{n:jvalue(v) for n,v in f['frames'][k].attrs.items()}} for k in f['frames']]
  def visit(n,v):
   key=norm(n)
   if isinstance(v,h5py.Dataset):
    key='/'+key; d=stats.setdefault(key,{'count':0,'dtype_shapes':collections.Counter(),'example':'/'+n,'attributes':{}});d['count']+=1;d['dtype_shapes'][str(v.dtype)+' '+str(tuple(v.shape))]+=1
    if v.attrs:d['attributes'].update({k:jvalue(x) for k,x in v.attrs.items()})
   if v.attrs:
    for k,x in v.attrs.items():
     a=attrs.setdefault('/'+key+'/@'+k,{'count':0,'example':'/'+n+'/@'+k,'types':set()});a['count']+=1;a['types'].add(str(type(x).__name__))
  f.visititems(visit)
  rootattrs={k:jvalue(v) for k,v in f.attrs.items()}
 for v in stats.values():v['dtype_shapes']=dict(v['dtype_shapes'])
 for v in attrs.values():v['types']=sorted(v['types'])
 binding=json.loads(bind);directory=Path(p).parent
 files=[];jsonkeys={}
 for path in directory.iterdir():
  if path.is_symlink():raise ValueError('symlink in source directory')
  if path.is_file():
   files.append({'path':str(path),'bytes':path.stat().st_size,'suffix':path.suffix})
   if path.suffix=='.json':
    def walk(v,key):
     if isinstance(v,dict):
      for k,x in v.items():walk(x,key+'/'+k)
     elif isinstance(v,list):jsonkeys[str(path)+'#'+key]={'type':'list','length':len(v)}
     else:jsonkeys[str(path)+'#'+key]={'type':type(v).__name__}
    walk(json.load(path.open()),'')
 result=dict(execution_id=execution,task_id=task,variant_id=variant,source_path=p,source_sha256=h,frames=frames,datasets=stats,attributes=attrs,root_attributes=rootattrs,files=files,json_fields=jsonkeys,binding=binding)
 with dest.open('x') as f:json.dump(result,f,sort_keys=True)
 if i%10==0:print(i+1,execution,'channels',len(stats),'frames',len(frames),flush=True)
print('INVENTORY COMPLETE',flush=True)
