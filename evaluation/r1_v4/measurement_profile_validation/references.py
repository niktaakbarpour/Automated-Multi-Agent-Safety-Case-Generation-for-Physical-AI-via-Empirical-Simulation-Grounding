"""Development camera excerpts only; outputs are outside Git, never ground truth."""
import hashlib,socket
import h5py,numpy as np
from PIL import Image,ImageDraw
from .analyze import DATA,WORK,HERE
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha,save
WINDOWS={0:[0,10,14,16],2:[0,7,10,12],14:[260,276,282,284]}
def main():
 assert socket.gethostname().lower()=='hestia'
 manifest=[]
 for ep,indices in WINDOWS.items():
  source=DATA/'long/task_00'/f'episode_{ep:03d}'/'trajectory.h5';source_hash=sha(source);canvas=Image.new('RGB',(768,424),'white');draw=ImageDraw.Draw(canvas)
  with h5py.File(source,'r') as f:
   for row,camera in enumerate(('agentview_image','robot0_eye_in_hand_image')):
    for col,i in enumerate(indices):
     path=f'/frames/{i:06d}/raw_observation/{camera}/value';a=f[path][()];assert a.shape==(256,256,3) and a.dtype==np.uint8
     canvas.paste(Image.fromarray(a[::-1,::-1]).resize((192,192)),(col*192,row*212+20));draw.text((col*192+3,row*212+3),f'ep{ep:03d} f{i} '+('agent' if row==0 else 'wrist'),fill='black')
     manifest.append(dict(episode=ep,frame=i,camera=camera,source=str(source),source_sha256=source_hash,hdf5_path=path,raw_uint8_bytes_sha256=hashlib.sha256(a.tobytes()).hexdigest(),display_transform='180-degree rotation; resized to192; derived JPEG only',capture_time=None,review_role='qualitative corroboration; not physical proof'))
  out=WORK/'reference_sheets'/f'episode_{ep:03d}.jpg';canvas.save(out,quality=70)
  for r in manifest:
   if r['episode']==ep:r.update(derived_sheet=str(out),derived_sheet_sha256=sha(out))
 save(HERE/'CAMERA_EXCERPT_MANIFEST.json',manifest)
 print('Extracted selected camera datasets:',len(manifest))
if __name__=='__main__':main()
