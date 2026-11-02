from pathlib import Path
import urllib.request,json,hashlib
w=Path('/disk/1/data/niktakbr/trustworthy-phase5h-working/primary');rows=[]
for source in ('src/engine/engine_forward.c','src/engine/engine_util_misc.c','include/mujoco/mjdata.h','include/mujoco/mjmodel.h'):
 url='https://raw.githubusercontent.com/google-deepmind/mujoco/3.8.1/'+source
 try:
  data=urllib.request.urlopen(url,timeout=30).read();p=w/source.replace('/','__');p.write_bytes(data);rows.append(dict(url=url,path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),version='3.8.1'))
 except Exception as e:rows.append(dict(url=url,error=str(e)))
with (w/'FETCH_MANIFEST.json').open('x') as f:json.dump(rows,f,indent=2)
print(rows,flush=True)
