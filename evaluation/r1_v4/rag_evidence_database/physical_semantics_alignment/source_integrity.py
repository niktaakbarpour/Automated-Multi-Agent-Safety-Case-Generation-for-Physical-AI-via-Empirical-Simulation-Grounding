"""Hash-rooted external reads bound to open descriptors, never path-only HDF5 reads."""
import os,hashlib,socket
from pathlib import Path
from contextlib import contextmanager

class SourceError(ValueError):pass

def signature(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)

class SourceVerifier:
 def __init__(self,roots=('/disk/1/data/niktakbr','/disk/0/home/niktakbr'),namespace='hestia-owned-storage-v1'):
  self.roots=tuple(Path(x) for x in roots);self.namespace=namespace;self.cache={};self.hash_checks=0;self.cache_hits=0
 def open_fd(self,path):
  p=Path(path)
  if not p.is_absolute() or '..' in p.parts or not any(p.is_relative_to(r) for r in self.roots):raise SourceError('unapproved_source_path')
  # Walk every component using directory FDs and O_NOFOLLOW. No resolve() follows a redirect.
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
  try:
   for part in p.parts[1:-1]:
    nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
   result=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
  except OSError as e:raise SourceError('missing_or_redirected_source: '+str(p)) from e
  finally:os.close(fd)
  import stat
  if not stat.S_ISREG(os.fstat(result).st_mode):os.close(result);raise SourceError('source_not_regular_file')
  return result
 def hash_file(self,file):
  file.seek(0);h=hashlib.file_digest(file,'sha256').hexdigest();file.seek(0);self.hash_checks+=1;return h
 @contextmanager
 def access(self,path,expected,mode='strict'):
  if mode not in ('strict','verified_session'):raise SourceError('unsupported_verification_mode')
  if not isinstance(expected,str) or len(expected)!=64:raise SourceError('missing_trusted_source_hash')
  fd=self.open_fd(path)
  with os.fdopen(fd,'rb') as file:
   before=signature(os.fstat(file.fileno()));key=(self.namespace,str(path),expected);cached=self.cache.get(key)
   if mode=='verified_session' and cached==before:self.cache_hits+=1
   else:
    actual=self.hash_file(file)
    if actual!=expected:raise SourceError('source_sha256_mismatch')
    if signature(os.fstat(file.fileno()))!=before:raise SourceError('source_changed_while_hashing')
    self.cache[key]=before
   attestation=dict(status='verified_source',mode=mode,namespace=self.namespace,source_path=str(path),source_sha256=expected,file_identity=list(before),decoded_value_cache=False)
   try:
    yield file,attestation
   finally:
    if signature(os.fstat(file.fileno()))!=before:self.cache.pop(key,None);raise SourceError('source_changed_during_read')
    # Reopen the pathname safely: replacement/redirection cannot silently change attribution.
    check=self.open_fd(path)
    try:
     if signature(os.fstat(check))!=before:self.cache.pop(key,None);raise SourceError('source_path_identity_changed')
    finally:os.close(check)
    if mode=='strict' and self.hash_file(file)!=expected:self.cache.pop(key,None);raise SourceError('source_sha256_changed_during_read')
 def verify(self,path,expected,mode='strict'):
  with self.access(path,expected,mode) as (_,proof):return proof
