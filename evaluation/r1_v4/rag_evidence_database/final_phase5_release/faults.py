"""Bounded isolated source faults; actual validated recordings never modified."""
import contextlib,tempfile,shutil,os
from pathlib import Path
from .config import WORK
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
class Redirect:
 def __init__(self,base,canonical,scratch):self.base=base;self.canonical=canonical;self.scratch=str(scratch)
 def access(self,p,h,mode='strict'):return self.base.access(self.scratch if str(p)==self.canonical else p,h,mode)
 def verify(self,p,h,mode='strict'):
  with self.access(p,h,mode) as (fd,a):return a
 def __getattr__(self,k):return getattr(self.base,k)
@contextlib.contextmanager
def source_fault(engine,canonical,expected,kind):
 old=engine.store.verifier
 with tempfile.TemporaryDirectory(dir=WORK,prefix='fault-') as directory:
  p=Path(directory)/'source.h5'
  if kind!='missing':
   with old.access(canonical,expected,'strict') as (fd,a),p.open('wb') as out:shutil.copyfileobj(fd,out)
   if kind=='symlink':p.rename(Path(directory)/'real.h5');p.symlink_to(Path(directory)/'real.h5')
   elif kind=='replace':
    old.verify(str(p),expected,'verified_session');replacement=Path(directory)/'replacement';replacement.write_bytes(b'replaced bytes');os.replace(replacement,p)
   else:
    with p.open('ab') as out:out.write(b'isolated tampering')
  engine.store.verifier=Redirect(old,canonical,p)
  try:yield
  finally:engine.store.verifier=old;assert sha(Path(canonical))==expected
