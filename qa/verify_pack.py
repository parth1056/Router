from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
for f in manifest['files']:
 p=(ROOT/f['path']).resolve();assert p.is_relative_to(ROOT.resolve()),f['path']
 h=hashlib.sha256()
 with p.open('rb') as src:
  for b in iter(lambda:src.read(8*1024*1024),b''):h.update(b)
 assert p.stat().st_size==f['bytes'] and h.hexdigest()==f['sha256'],f['path']
print('PASS:',len(manifest['files']),'archived payload hashes verified, including actual model weights. No inference or training performed.')
