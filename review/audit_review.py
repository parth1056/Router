"""Independent stdlib checks of returned evidence and reviewed dataset; no GPU work."""
from pathlib import Path
import json,hashlib,collections,sys,math
ROOT=Path(__file__).resolve().parent;SRC=ROOT/'returned';OUT=ROOT/'curated'
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
for path,f in manifest['files'].items():
 b=(SRC/path).read_bytes();assert len(b)==f['bytes'] and sha(b)==f['sha256'],path
originals={r['id']:r for r in read(SRC/'REVIEW_ROWS.jsonl')}
assert len(originals)==2500
for split in ['train','dev','test']:
 for r in read(SRC/f'candidates/{split}_candidates.jsonl'):assert r==originals[r['id']] and r['proposed_split']==split
mapping=json.loads((SRC/'critic/PRIVATE_MAPPING.json').read_text())['packet_id_to_candidate_id'];blind=read(SRC/'critic/blind_inputs.jsonl');judges={r['packet_id']:r for r in read(SRC/'critic/judgements.jsonl')}
assert len(mapping)==len(blind)==len(judges)==1200
for b in blind:
 assert set(b)=={'packet_id','input'} and b['input']==originals[mapping[b['packet_id']]]['input']
 j=judges[b['packet_id']];r=originals[mapping[b['packet_id']]]
 assert j['route']==r['critic']['route'] and j['ambiguous']==r['critic']['ambiguous'] and j['explanation']==r['critic']['note']
coverage=collections.Counter(originals[r]['proposed_split'] for r in mapping.values());disagreements=collections.Counter(originals[r]['proposed_split'] for p,r in mapping.items() if judges[p]['route']!=originals[r]['proposed_route'])
events_receipts={}
for filename in ['writer/events.jsonl','writer/retry_events.jsonl','critic/events.jsonl']:
 es=read(SRC/filename);started={e['case_id']:e for e in es if e['kind']=='started'};finished={e['case_id']:e for e in es if e['kind']=='finished'}
 assert len(started)==len(finished)==len(es)//2 and set(started)==set(finished)
 for cid,e in started.items():
  assert sha(canonical(e['request']).encode())==e['request_sha256']==finished[cid]['request_sha256']
  f=finished[cid];assert f['valid'] is True and f['response']['done_reason']=='stop'
  raw=json.loads(f['response']['message']['content']);assert raw==f['parsed']
  assert e['request']['options']['num_ctx']==4096
  if filename.startswith('critic/'):
   body=json.loads(e['request']['messages'][1]['content'].split('\n',1)[1]);assert body in blind
   assert f['parsed']==judges[cid]
 events_receipts[filename]={'calls':len(started),'raw_parsed_match':True,'hashes_match':True,'completed':True}
# The supplied input schema uses this limited standard-keyword subset.
schema=json.loads((SRC/'sources/input_schema.json').read_text())
def validate(x,s,path='input'):
 typ=s.get('type');ts=typ if isinstance(typ,list) else [typ] if typ else []
 if ts:
  ok=any((t=='object' and isinstance(x,dict)) or (t=='array' and isinstance(x,list)) or (t=='string' and isinstance(x,str)) or (t=='null' and x is None) or (t=='number' and type(x) in [int,float] and math.isfinite(x)) for t in ts)
  assert ok,(path,ts,type(x))
 if 'enum' in s:assert x in s['enum'],(path,x)
 if isinstance(x,dict):
  assert set(s.get('required',[]))<=set(x),path
  if s.get('additionalProperties') is False:assert set(x)<=set(s.get('properties',{})),path
  for k,v in x.items():
   if k in s.get('properties',{}):validate(v,s['properties'][k],path+'.'+k)
 if isinstance(x,list):
  assert len(x)<=s.get('maxItems',float('inf')),path
  for i,v in enumerate(x):validate(v,s.get('items',{}),path+f'[{i}]')
 if isinstance(x,str):assert len(x)>=s.get('minLength',0),path
 if type(x) in [int,float]:assert s.get('minimum',-float('inf'))<=x<=s.get('maximum',float('inf')),path
reviewed=read(OUT/'REVIEWED_ROWS.jsonl');assert len(reviewed)==2500
for r in reviewed:
 validate(r['input'],schema,r['id']);s=r['input'];assert len({a['id'] for a in s['assets']})==len(s['assets'])
 assert s['active_image_id'] is None or s['active_image_id'] in {a['id'] for a in s['assets']}
 assert r['human_reviewed'] is False and r['accepted_for_training'] is False and r['ai_reviewed'] is True
 if r['proposed_split']!='train':assert s==originals[r['id']]['input']
from collections import Counter
counts=Counter(r['proposed_split'] for r in reviewed);assert counts=={'train':2000,'dev':200,'test':300}
receipt={'source_hashes_verified':len(manifest['files']),'original_rows':len(originals),'reviewed_rows':len(reviewed),'counts':dict(counts),'blind_input_and_judgement_bijection':1200,'critic_coverage':dict(coverage),'critic_disagreements':dict(disagreements),'events':events_receipts,'reviewed_input_schema_and_asset_references_pass':True,'heldout_inputs_unchanged':True,'tokenizer_and_GPU_checks':'NOT RUN HERE; must execute pinned tokenizer input checks before fitting','human_review':False,'LAYA_training_or_inference':False}
(OUT/'EVIDENCE_AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2))
