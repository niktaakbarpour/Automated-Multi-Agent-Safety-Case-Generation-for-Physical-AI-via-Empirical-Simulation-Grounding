"""Fetch a pinned public encoder, never a hosted embedding API or private input."""
import hashlib,json,urllib.request
from pathlib import Path
from evaluation.r1_v4.provenance import write_new

def main():
 root=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/encoder');meta=json.loads((root/'HUB_METADATA.json').read_text());revision=meta['sha'];files={r['rfilename']:r for r in meta['siblings']}
 wanted=['model.safetensors','config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','sentence_bert_config.json','1_Pooling/config.json','README.md'];rows=[]
 for name in wanted:
  item=files[name];url='https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/'+revision+'/'+name+'?download=true';p=root/name;p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.part')
  with urllib.request.urlopen(url,timeout=60) as response,temp.open('xb') as out:
   while block:=response.read(1024**2):out.write(block)
  data=temp.read_bytes();digest=hashlib.sha256(data).hexdigest()
  if 'lfs' in item:assert digest==item['lfs']['sha256'] and len(data)==item['lfs']['size']
  else:assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['blobId']
  assert not p.exists();temp.rename(p);rows.append({'name':name,'path':str(p),'bytes':len(data),'sha256':digest,'source_url':url});print('Verified public encoder file',name,flush=True)
 write_new(root/'MODEL_MANIFEST.json',{'schema_version':'1.0.0','repo':'sentence-transformers/all-MiniLM-L6-v2','revision':revision,'license':meta['cardData']['license'],'files':rows,'use':'Local CPU source retrieval only; no hosted inference API; no safety data uploaded.'})
if __name__=='__main__':main()
