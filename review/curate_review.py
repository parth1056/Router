"""Codex AI adjudication of the preserved 2500-row return; no fitting or model calls."""
from pathlib import Path
import json,collections,hashlib,copy,sys,re
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'returned'
OUT=ROOT/'curated'
OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT.parents[1]/'LAYA_Router_2000/tools'))
from check_and_freeze import normalised_state

def load(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def dump(p,rows):p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
rows=load(SRC/'REVIEW_ROWS.jsonl')
# Explicit row-by-row policy decisions, not critic voting or desired-category inference.
base_ids='''521_3 522_1 522_2 522_4 523_1 523_2 523_4 524_2 524_3 524_4 525_3 525_4 527_3 527_4 530_2 530_3 532_2 532_4 533_4 534_2 535_2 535_4 536_1 536_2 537_1 537_2 537_4 538_3 538_4 539_2 539_3 539_4 540_1 540_4 541_4 542_2 543_4 544_1 544_2 544_4 545_1 545_2 545_4 546_3 547_2 547_3 548_4 549_1 549_4 551_2 551_3 552_2 553_1 553_3 554_1 554_2 554_4 555_1 555_2 555_3 577_3 577_4 580_3 581_2 581_4 582_2 586_1 587_1 590_4'''.split()
changes={'fam2_train_s'+s:('BASE','Unqualified oddness, general checking/opinion, text accuracy, methods, or provenance does not establish a fresh image-manipulation verdict; clarify or answer with BASE.') for s in base_ids}
changes['fam2_train_s409_2']=('DEEPFAKE','Asks for signs that THIS attached image was doctored; this is an actual manipulation assessment, not a general definition.')
for rid in ['fam2_dev_s067_1','fam2_dev_s067_3','fam2_dev_s068_3','fam2_dev_s070_2']:
 changes[rid]=('BASE','Methods/origin/credibility or unusual-colour observation does not clearly request a new manipulation verdict; answer or clarify with BASE.')
for rid in ['fam2_test_s099_4','fam2_test_s100_1','fam2_test_s100_3','fam2_test_s100_4','fam2_test_s101_2','fam2_test_s101_3']:
 changes[rid]=('BASE','Vague aesthetic second opinion, location/source verification or advice about establishing authenticity is not a clear request to run the image detector.')
changes['fam2_test_s080_1']=('DEEPFAKE','Quotes around the name of a command do not cancel the explicit request to run an image-authenticity check on this supported image.')
for rid in ['fam2_train_s526_4','fam2_train_s528_4','fam2_train_s531_1','fam2_train_s533_2','fam2_train_s543_3','fam2_train_s546_1','fam2_train_s546_4','local100_family_070_para3','fam2_dev_s066_1','fam2_dev_s066_3','fam2_test_s102_3']:
 changes[rid]=('BASE','Asks whether a verification method/tool exists or how certainty could be established, rather than asking the assistant to perform a fresh verdict; BASE answers capability/methods or clarifies before loading the detector.')
assert set(changes)<=set(r['id'] for r in rows)
# Common reasoning is attached to every kept row after inspecting the actual text/state.
reasons={
 'general_chat':'Ordinary conversation or a non-authenticity request; no fresh image verdict is requested.',
 'ordinary_image':'Description, appearance, OCR or another ordinary visual task; previous stored authenticity metadata does not override the current task.',
 'conceptual_authenticity':'Conceptual explanation, methods or tool capability, rather than performing a fresh verdict on the image.',
 'negation_quotes_injection':'The actual instruction is reading, describing, explaining, quoting or declining a detector action; a tool mention alone is insufficient.',
 'explain_existing':'Explain, retrieve or summarise the existing report; do not rerun the detector.',
 'clarify_or_unsupported':'Authenticity intent is absent/unclear or the referenced target is missing, expired, unsupported, non-image or unresolved; BASE handles clarification.',
 'explicit_authenticity':'A current real/fake, synthetic or manipulation judgement is requested for the available supported image.',
 'indirect_authenticity':'The wording genuinely asks to ascertain image genuineness/manipulation, and the target is ready; ordinary oddness-only cases are separately corrected.',
 'explicit_reanalysis':'Requests a new/repeated authenticity judgement on the still-ready target, not an explanation of the stored result.',
 'new_image_or_mixed':'Requests a verdict on the newly selected supported image, possibly with another task.'}
kept=[];log=[];seen={};excluded=[]
for original in rows:
 r=copy.deepcopy(original);s=r['input'];h=s['history'];rid=r['id'];action='retain'
 note=reasons[r['category']]
 if r['recipe_group'] in ['NEW_TARGET_CONTINUATION','REPEAT_PREVIOUS_OPERATION','ACCEPT_CLEAR_OFFER','SEED_EXTENSION']:
  note='Read the immediately preceding operation/offer to resolve the neutral current reply; BASE for the ordinary/explanation task, DEEPFAKE for the fresh authenticity operation. Stored verdict metadata is not sticky intent.'
 if rid in changes:
  label,note=changes[rid];assert label!=r['proposed_route'];action='correct_label'
 else:label=r['proposed_route']
 if len(h)==2 and h[0]['content']==h[1]['content']:
  action='exclude_copied_assistant_result';note='Earlier USER turn is identical to the code-owned ASSISTANT result; this survived the writer text filter and is a malformed role exchange.'
 key=normalised_state(json.dumps(s,ensure_ascii=False))
 if not action.startswith('exclude') and key in seen:
  assert label==seen[key]['pilot_label'],'Conflicting duplicate labels require a new explicit adjudication'
  action='exclude_normalised_duplicate';note='Identical runtime input after asset-ID/whitespace/case normalisation; retained '+seen[key]['id']+'.'
 decision={'id':rid,'split':r['proposed_split'],'source_input_sha256':sha(s),'source_route':r['proposed_route'],'reviewed_route':label,'action':action,'reason':note,'reviewer':'Codex AI; not a human annotator','model_predictions_seen':False}
 log.append(decision)
 if action.startswith('exclude'):excluded.append(decision);continue
 r.update(pilot_label=label,pilot_label_source='codex_full_input_policy_adjudication_2026_11_17',pilot_label_reason=note,ai_reviewed=True,review_decision=action,status='AI_REVIEWED_EXPLORATORY_PILOT',human_reviewed=False,accepted_for_training=False)
 r['source_proposed_route']=original['proposed_route'];r['source_input_sha256']=sha(s)
 if r['proposed_split']=='train':r['split_reservation']='TRAIN_ONLY'
 kept.append(r);seen[key]=r

# Fill ONLY excluded training slots with separately disclosed AI-authored coverage cases.
# Existing development/test inputs are never rewritten. These are not Qwen outputs.
def state(recipe='ready'):
 a=lambda i,availability='available',support='supported',kind='image':dict(id=i,kind=kind,availability=availability,support=support)
 s=dict(message='',history=[],assets=[a('image_a')],active_image_id='image_a',last_analysis=None)
 if recipe=='no_assets':s.update(assets=[],active_image_id=None)
 elif recipe in ['unsupported','unknown']:s['assets'][0]['support']=recipe
 elif recipe in ['missing','expired']:s['assets'][0]['availability']=recipe
 elif recipe=='video':s.update(assets=[a('clip_a',support='unsupported',kind='video')],active_image_id=None)
 elif recipe in ['stored_real','stored_fake','stored_removed','new','new_old_missing']:
  s['last_analysis']=dict(asset_id='image_a',verdict='REAL' if recipe=='stored_real' else 'FAKE',confidence=None,evidence_summary=['A previous authenticity report is stored.'])
  if recipe in ['stored_removed','new_old_missing']:s['assets'][0]['availability']='missing'
  if recipe in ['new','new_old_missing']:s['assets'].append(a('image_b'));s['active_image_id']='image_b'
 elif recipe=='multiple':s['assets'].append(a('image_b'));s['active_image_id']=None
 elif recipe!='ready':raise ValueError(recipe)
 return s
add=[]
def C(message,label,recipe='ready',reason=None,custom=None,family=None):
 s=copy.deepcopy(custom) if custom is not None else state(recipe);s['message']=message
 add.append(dict(input=s,label=label,family=family,reason=reason or ('Ordinary content, explanation, ambiguity or provenance; no new image-manipulation verdict.' if label=='BASE' else 'Explicit fresh image-authenticity judgement with a ready supported target.')))
# 24 distinct ordinary/conceptual/current-task negatives.
for msg in [
 'How does this portrait look as a professional headshot?',
 'Does the smile look forced, or just a bit nervous?',
 'The lighting feels odd; suggest a better lamp position for my next portrait.',
 'Is this makeup too shiny for a passport-style photograph?',
 'Is the jacket in this picture made of fake leather?',
 'Can you authenticate the handbag brand, rather than check whether the photograph was edited?',
 'Does the film monster in this poster look convincing as a costume?',
 'How could I make this avatar design look more lifelike?',
 'Edit this photo so it deliberately looks fake.',
 'Write a prompt for creating a fictional profile photograph.',
 'Translate the phrase "this portrait was digitally altered" into Spanish.',
 'Explain what a detector means by "likely synthetic" without analysing this photograph.',
 'What risks come from treating an authenticity score as proof?',
 'Count the visible faces in the staff picture.',
 'Describe the hairstyle and expression; please skip authenticity checking.',
 'Check the grammar of the caption I wrote for the picture.',
 'Read the printed date from this photograph; do not verify its provenance.',
 'Could you help identify the building in this street photo?',
 'Can you establish whether the event shown happened in 2010?',
 'Does our image checker support pictures with several faces?',
 'What is the difference between a face swap and ordinary colour correction?',
 'This photo looks strange to me, but I only want composition advice.'
]:C(msg,'BASE')
C('Copy the exact verdict already stored for this photograph.','BASE','stored_real')
C('The upload is gone. Summarise the saved report without doing a new check.','BASE','stored_removed')
# 20 positive requests with varied operations, not just a repeated real/fake phrase.
for msg in [
 'Please check whether the face in this passport-style picture was swapped.',
 'Was this attached portrait captured by a camera or generated with AI?',
 'Inspect the picture for digital manipulation and give me a verdict.',
 'Could the person in this photograph have been synthetically inserted?',
 'I suspect an AI-generated face here; please assess the image.',
 'Check this scan for evidence of a face replacement.',
 'Is the uploaded headshot a genuine photograph or a synthetic one?',
 'Tell me whether the visible face has been digitally fabricated.',
 'Please assess whether this photograph has been doctored.',
 'I need a fresh real-or-fake judgement for the attached portrait.',
 'Verify whether the submitted photo was made with a generative model.',
 'Before I use this headshot, check whether it is AI-generated.',
 'The facial features look pasted in. Please check for manipulation.',
 'Could you give an authenticity verdict on the selected photograph?',
 'Check for a digitally substituted face, then describe the background.',
 'Please decide whether this picture is synthetic and read its badge text.',
 'Does this portrait show signs of a deepfake? Analyse it.',
 'Assess whether somebody digitally changed the face in the photograph.',
 'Run the photo-authenticity check; I am not asking for aesthetic feedback.',
 'Look for AI synthesis in the image and report your verdict.'
]:C(msg,'DEEPFAKE')
# 20 asset-readiness/target-resolution cases.
for recipe,msg in [
 ('no_assets','Could you analyse the photo for manipulation? I have not uploaded it yet.'),
 ('unsupported','Please check the attachment for a digitally replaced face.'),
 ('unknown','I want to know whether the uploaded portrait is synthetic.'),
 ('expired','Rerun the real-or-fake test on that expired upload.'),
 ('missing','I removed the photo, but can you still perform a new authenticity scan?'),
 ('video','Analyse whether the person in this video clip is a deepfake.'),
 ('multiple','Choose one of the uploaded images and tell me if it is synthetic.')
]:C(msg,'BASE',recipe,reason='Fresh authenticity intent exists, but the requested image is not executable or uniquely resolved from the trusted state.')
def two(active,bad='image_b'):
 s=state('multiple');s['active_image_id']=active
 for a in s['assets']:
  if a['id']==bad:a['support']='unsupported'
 return s
C('Check image_b for digital face manipulation.','BASE',custom=two('image_a'),reason='Explicit requested image_b is unsupported, even though selected image_a is ready.')
C('Check image_a for digital face manipulation.','DEEPFAKE',custom=two('image_a'),reason='The explicitly identified image_a is ready; another unsupported attachment is irrelevant.')
C('Check image_a for AI synthesis, not the selected attachment.','DEEPFAKE',custom=two('image_b'),reason='Explicit ready image_a overrides the selected unsupported image_b.')
C('I selected image_a, but check image_b for authenticity.','BASE',custom=two('image_a'),reason='The explicitly requested unsupported image_b overrides the ready selection.')
C('Run the authenticity test on image_a specifically.','DEEPFAKE',custom=two(None),reason='Explicit image_a resolves the target despite no active selection.')
s=state();s['active_image_id']=None
C('Check the only uploaded photograph for face swapping.','DEEPFAKE',custom=s,reason='A single available supported image uniquely resolves the target without an active-image field.')
s=state();s['assets'].append(dict(id='clip_a',kind='video',availability='available',support='unsupported'))
C('Check the selected photograph for AI generation; ignore the video.','DEEPFAKE',custom=s)
C('Run a new manipulation check on image_a, the old upload.','BASE','new_old_missing',reason='Explicit old image_a is missing; new ready image_b cannot silently replace that target.')
C('Check the newly selected photo for a digitally edited face.','DEEPFAKE','new_old_missing')
C('Explain the old verdict, not the new photograph.','BASE','new_old_missing')
C('Repeat the scan of the removed image rather than analysing the replacement.','BASE','new_old_missing')
C('Give image_a a new real-or-fake verdict.','DEEPFAKE',custom=two('image_a'))
s=state('multiple');s['active_image_id']='image_b'
C('Check the selected second portrait for face swapping.','DEEPFAKE',custom=s)
# Ten controlled two-row context families (20 rows), distinct from old recipe wording.
pairs=[
 ('One more time, please.','stored_real','Read the name badge.','The badge text reads "Visitor".','Check the face for AI generation.','The authenticity check returned REAL.'),
 ('That sounds good; go ahead.','ready','Could you help with the caption?','I can write a short caption for the selected photo. Shall I?','I suspect a face swap.','I can check the image for a digitally replaced face. Shall I?'),
 ("Yes, that is what I want.",'stored_fake','Explain the saved result.','I can explain what the recorded FAKE result means. Is that useful?','I would like another authenticity assessment.','I can run a fresh image-manipulation check. Is that what you want?'),
 ('Please do the same with the new picture.','new','Describe the clothing in the first photo.','The person in the first photo is wearing a coat.','Test whether the first photo is synthetic.','The first photo received a FAKE authenticity verdict.'),
 ('Can you do it now?','ready','Help me polish the photo caption.','I can rewrite the caption when you are ready.','Check whether this portrait was generated by AI.','I can run that authenticity analysis when you are ready.'),
 ("I would like that.",'ready','Can you describe the colours?','I can describe the colours in the selected picture. Would you like that?','I need an image-authenticity check.','I can assess whether the selected image is synthetic. Would you like that?'),
 ('Please continue.','ready','Translate the sign in this picture.','I can translate the visible sign into English. Should I continue?','Can you assess whether the picture has been manipulated?','I can run the manipulation assessment. Should I continue?'),
 ('Yes, on this image.','ready','Count the faces for me.','Do you want me to count the faces in the selected picture?','Check for digital face replacement.','Do you want me to test the selected picture for a face swap?'),
 ('Again, but on the selected photo.','new','Write a caption for the first image.','Here is a short caption for the first image.','Run the authenticity detector on the first image.','The first image was classified FAKE by that check.'),
 ('All right, do that.','ready','Help me write an invitation to the portrait session.','I can draft the invitation. Would you like me to do that?','Can we check whether this portrait is authentic?','I can run a fresh authenticity assessment of the portrait. Would you like me to do that?')]
for i,(msg,recipe,bu,ba,du,da) in enumerate(pairs,1):
 for label,u,a in [('BASE',bu,ba),('DEEPFAKE',du,da)]:
  s=state(recipe);s['history']=[dict(role='user',content=u),dict(role='assistant',content=a)]
  C(msg,label,custom=s,family='context_'+str(i),reason='Controlled context contrast: the neutral current reply accepts/repeats the immediately preceding ordinary operation or authenticity operation; assets/current message are identical within the pair.')
assert len(add)==84,len(add)
assert len([r for r in kept if r['proposed_split']=='train'])+len(add)==2000
for i,c in enumerate(add,1):
 rid='codex_gap_'+str(i).zfill(3);family='codex_gap_family_'+(c['family'] or str(i).zfill(3))
 key=normalised_state(json.dumps(c['input'],ensure_ascii=False));assert key not in seen,(rid,seen.get(key))
 r=dict(id=rid,family_id=family,recipe_group='CODEX_COVERAGE_ADDITION',mode='context_pair' if c['family'] else 'single',category='codex_coverage',proposed_split='train',proposed_route=c['label'],pilot_label=c['label'],pilot_label_source='codex_AI_authored_and_policy_reviewed_2026_11_17',pilot_label_reason=c['reason'],input=c['input'],human_reviewed=False,accepted_for_training=False,ai_reviewed=True,status='AI_REVIEWED_EXPLORATORY_PILOT',split_reservation='TRAIN_ONLY',provenance=dict(generator='Codex AI; not Qwen output',purpose='Distinct coverage cases replacing excluded training slots',source_capsule_sha256='3bec2683239192f24fd8594e579abf29787a292305ca988ec1712511c1b4833c'))
 kept.append(r);seen[key]=r;log.append(dict(id=rid,split='train',action='add_AI_authored_training_case',reviewed_route=c['label'],reason=c['reason'],input_sha256=sha(c['input']),reviewer='Codex AI; not a human annotator',model_predictions_seen=False))
# Group repeated scenario/recipe lineages honestly, not just numbered family IDs.
jobs={}
for split in ['train','dev','test']:
 for j in json.loads((SRC/'sources'/f'{split}_jobs.json').read_text(encoding='utf-8')):jobs[j['family_id']]=j
bank={r['family_id']:r for r in json.loads((SRC/'sources/pair_recipe_bank.json').read_text(encoding='utf-8'))}
for r in kept:
 f=r['family_id'];j=jobs.get(f)
 if f.startswith('codex_gap_family_'):group=f
 elif f in bank:group='seedlineage_'+f
 elif j:
  # Same scenario + operation recipe are siblings even when the plan gave new IDs.
  group='scenario_'+r['proposed_split']+'_'+sha([j['scene'],j['recipe_group'],r['category'] if j['mode']=='single' else 'paired_operations'])[:16]
 else:group='seedlineage_'+f
 r['template_group_id']=group
 for k in ['quality_flags','critic','writer_route_readback']:r.pop(k,None)
# Repeated full dialogue across distinct states is a related evaluation cluster.
# Keep useful metadata contrasts, but do not bootstrap them as independent cases.
parent={r['template_group_id']:r['template_group_id'] for r in kept}
def find(g):
 while parent[g]!=g:
  parent[g]=parent[parent[g]];g=parent[g]
 return g
dialogues={}
for r in kept:
 k=sha([r['input']['message'],r['input']['history']]);g=r['template_group_id']
 if k in dialogues:
  other=dialogues[k];assert other['proposed_split']==r['proposed_split'],'Dialogue crosses a split'
  a,b=find(g),find(other['template_group_id'])
  if a!=b:parent[max(a,b)]=min(a,b)
 else:dialogues[k]=r
for r in kept:r['template_group_id']=find(r['template_group_id'])

# Verify unique canonical inputs and disjoint original family and scenario group membership.
summary={};splitsets={}
for split in ['train','dev','test']:
 rr=[r for r in kept if r['proposed_split']==split]
 keys=[normalised_state(json.dumps(r['input'],ensure_ascii=False)) for r in rr]
 assert len(keys)==len(set(keys));assert len({r['id'] for r in rr})==len(rr)
 splitsets[split]=dict(inputs=set(keys),families={r['family_id'] for r in rr},groups={r['template_group_id'] for r in rr})
 summary[split]=dict(rows=len(rr),labels=dict(collections.Counter(r['pilot_label'] for r in rr)),source_families=len(splitsets[split]['families']),scenario_groups=len(splitsets[split]['groups']),history_present=sum(bool(r['input']['history']) for r in rr),family_max=max(collections.Counter(r['family_id'] for r in rr).values()),scenario_group_max=max(collections.Counter(r['template_group_id'] for r in rr).values()))
 dump(OUT/f'{split}_reviewed.jsonl',rr)
for a,b in [('train','dev'),('train','test'),('dev','test')]:
 for field in ['inputs','families','groups']:assert not splitsets[a][field]&splitsets[b][field],(a,b,field)
assert [summary[k]['rows'] for k in ['train','dev','test']]==[2000,200,300]
assert summary['train']['source_families']>=500 and summary['train']['family_max']<=4
# READY check is necessary, not a substitute for the actual intent adjudication above.
for r in kept:
 s=r['input'];assert set(s)=={'message','history','assets','active_image_id','last_analysis'}
 assert r['human_reviewed'] is False and r['accepted_for_training'] is False
 if r['pilot_label']=='DEEPFAKE':assert any(a['kind']=='image' and a['availability']=='available' and a['support']=='supported' for a in s['assets']),r['id']
# All held-out runtime inputs remain byte-equivalent as JSON objects to the originals.
originals={r['id']:r for r in rows}
assert all(r['input']==originals[r['id']]['input'] for r in kept if r['proposed_split']!='train')
dump(OUT/'REVIEWED_ROWS.jsonl',kept);dump(OUT/'ROW_DECISIONS.jsonl',log);dump(OUT/'EXCLUSIONS.jsonl',excluded);dump(OUT/'ADDED_TRAINING_CASES.jsonl',[r for r in kept if r['id'].startswith('codex_gap_')])
summary.update(source_capsule_sha256='3bec2683239192f24fd8594e579abf29787a292305ca988ec1712511c1b4833c',original_rows=2500,actions=dict(collections.Counter(r['action'] for r in log)),label_corrections=[r for r in log if r['action']=='correct_label'],heldout_inputs_unchanged=True,review='Codex AI review, including inherited review for 100 unchanged seed inputs; no human annotation',tokenizer_check='Pending on the college PC using pinned LAYA tokenizer; no LAYA inference/training run here',test_scores_seen=False)
(OUT/'REVIEW_RECEIPT.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='label_corrections'},indent=2))
