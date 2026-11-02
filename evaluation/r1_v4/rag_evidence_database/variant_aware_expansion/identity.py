"""Content identity over exact MJCF and its verified file dependencies."""
from pathlib import Path
import xml.etree.ElementTree as ET
from evaluation.r1_v4.provenance import load,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def identify(xml,asset_manifest):
 xml=Path(xml);root=ET.parse(xml).getroot()
 if root.findall('.//include'):raise ValueError('nested XML include requires new dependency contract')
 rows=load(asset_manifest)['assets'];assets=[]
 for r in rows:
  p=Path(r['path']).resolve()
  if not any(p.is_relative_to(prefix) for prefix in ('/disk/1/data/niktakbr','/disk/0/home/niktakbr','/local/home/niktakbr')):raise ValueError('asset outside authorized local roots')
  if sha(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:raise ValueError('asset hash/size mismatch')
  assets.append({'path':str(p),'sha256':r['sha256'],'bytes':r['bytes']})
 by_path={a['path']:a for a in assets}
 for a in assets:
  if a!=by_path[a['path']]:raise ValueError('conflicting references to same canonical asset')
 assets=list(by_path.values())
 compiler=root.find('compiler');options=compiler.attrib if compiler is not None else {}
 for elem in root.iter():
  if 'file' not in elem.attrib:continue
  p=Path(elem.attrib['file'])
  if not p.is_absolute():p=xml.parent/options.get('meshdir' if elem.tag=='mesh' else 'texturedir','')/p
  if str(p.resolve()) not in by_path:raise ValueError('unmanifested XML dependency:'+str(p))
 assets.sort(key=lambda a:a['path']);xml_sha=sha(xml);asset_digest=digest(assets)
 return {'variant_id':'xmlenv:'+digest({'identity_version':'1.0.0','xml_sha256':xml_sha,'asset_content_digest':asset_digest}),'xml_sha256':xml_sha,'asset_content_digest':asset_digest,'assets':assets,'asset_aliases':[{'kind':r.get('kind'),'name':r.get('name'),'declared_path':r['path'],'canonical_path':str(Path(r['path']).resolve())} for r in rows],'identity_version':'1.0.0','equivalence_rule':'Exact XML bytes and canonical asset paths, contents and sizes; never filename or task identity alone.'}
