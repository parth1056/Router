"""Fetch the optional pristine baseline at its exact public revision; never runs automatically."""
from pathlib import Path
import argparse,json,hashlib,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--dest',default=str(ROOT/'retrieved_baseline/laya-english'));a=p.parse_args();dest=Path(a.dest).resolve()
 receipt=json.loads((ROOT/'dependencies/baseline_download_receipt.json').read_text());rev=receipt['revision'];repo=receipt['repo'];checked=[]
 for name,meta in receipt['files'].items():
  if name.startswith('.cache/'):continue
  target=(dest/name).resolve();assert target.is_relative_to(dest)
  if target.exists():
   if target.stat().st_size!=meta['bytes'] or sha(target)!=meta['sha256']:raise ValueError('Existing file differs; preserve and choose a new destination: '+str(target))
  else:
   target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.download')
   if tmp.exists():raise ValueError('Preserve previous partial download; choose a fresh destination')
   url='https://huggingface.co/'+repo+'/resolve/'+rev+'/'+name
   with urllib.request.urlopen(url,timeout=90) as src,tmp.open('wb') as out:
    size=0
    for chunk in iter(lambda:src.read(4*1024*1024),b''):
     size+=len(chunk)
     if size>meta['bytes']:raise ValueError('Unexpected download size')
     out.write(chunk)
   if tmp.stat().st_size!=meta['bytes'] or sha(tmp)!=meta['sha256']:raise ValueError('Download did not match original receipt: '+name)
   tmp.rename(target)
  checked.append(name);print('Verified',name,flush=True)
 print(json.dumps({'repo':repo,'revision':rev,'dest':str(dest),'verified_files':checked},indent=2))
if __name__=='__main__':main()
