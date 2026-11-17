"""CPU-only immutable reviewed-data checks; no tokenizer, inference or fitting."""
from pathlib import Path
import json,hashlib,collections,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_and_freeze import normalised_state
lock=json.loads((ROOT/'REVIEW_LOCK.json').read_text(encoding='utf-8'))
assert lock['decision']=='APPROVED_FOR_FITTING_AFTER_PINNED_TOKENIZER_INPUT_CHECKS'
for path,digest in lock['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
sets={};total=0
for split,n in lock['expected_counts'].items():
 rows=[json.loads(x) for x in (ROOT/'data'/f'{split}.laya.jsonl').read_text(encoding='utf-8').splitlines()]
 sources=[json.loads(x) for x in (ROOT/'data'/f'{split}_reviewed.jsonl').read_text(encoding='utf-8').splitlines()]
 assert len(rows)==len(sources)==n
 keys=[]
 for row,source in zip(rows,sources):
  assert row['id']==source['id'] and row['gold']['route']['label']==source['pilot_label']
  assert json.loads(row['state'])==source['input'] and source['human_reviewed'] is False
  assert row['group_id']==source['template_group_id']
  assert row['questions']==json.loads((ROOT/'config/questions.json').read_text(encoding='utf-8'))
  keys.append(normalised_state(row['state']))
 assert len(set(keys))==len(keys)
 sets[split]={'ids':{r['id'] for r in rows},'families':{r['family_id'] for r in rows},'groups':{r['group_id'] for r in rows},'inputs':set(keys)}
 if split=='train':assert len(sets[split]['families'])>=500 and max(collections.Counter(r['family_id'] for r in rows).values())<=4
 total+=n
for a,b in [('train','dev'),('train','test'),('dev','test')]:
 for k in sets[a]:assert not sets[a][k]&sets[b][k],(a,b,k)
print('PASS: 2500 reviewed rows; locked data/questions/serializer hashes, labels, canonical inputs, conservative groups, unique inputs and split separation. Pinned-tokenizer check and GPU execution remain pending.')
