from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1]
m=json.loads((r/'MANIFEST.json').read_text(encoding='utf-8'))
for f in m['files']:
    p=(r/f['path']).resolve();assert p.is_relative_to(r.resolve())
    b=p.read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],f['path']
print('PASS:',len(m['files']),'supplied files verified; GPU execution pending.')
