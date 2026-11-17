"""Independent result review; uses stored predictions, never invokes the model."""
from pathlib import Path
import json,hashlib,math,sys,collections
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'results/capsule';PACK=ROOT
OUTPUT=ROOT/'verification_output';OUTPUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(DATA/'MANIFEST.json')
for name,f in m['files'].items():assert len((DATA/name).read_bytes())==f['bytes'] and sha(DATA/name)==f['sha256']
freeze=read(DATA/'data/FREEZE.json');selected=read(DATA/'FINAL_EVAL_FREEZE.json');selection=read(DATA/'training/selection.json');history=read(DATA/'training/history.json');receipt=read(DATA/'training/training_receipt.json')
for split in ['train','dev','test']:assert freeze['splits'][split]['sha256']==sha(PACK/f'data/{split}.laya.jsonl')==selection[split+'_sha256'],split
assert not freeze['overlaps'] and not freeze['bad_token_rows'] and max(x['max_assembled_tokens'] for x in freeze['splits'].values())==314
assert selected['questions_sha256']==sha(PACK/'config/questions.json') and selected['serializer_sha256']==sha(PACK/'tools/state.py')
assert selected['test_sha256']==freeze['splits']['test']['sha256']
assert max(history,key=lambda h:(h['dev']['macro_f1'],-h['dev']['base_false_activation_rate'],-h['dev']['nll'],-h['epoch']))['epoch']==selection['selected_epoch']==4
assert [h['epoch'] for h in history]==list(range(1,8)) and receipt['epochs_completed']==7
assert 2000//16*7==receipt['planned_optimizer_updates_for_completed_epochs']==875
assert receipt['test_opened'] is False and receipt['seed']==42
base=rows(DATA/'predictions/baseline_test.jsonl');trained=rows(DATA/'predictions/trained_test.jsonl');test=rows(PACK/'data/test.laya.jsonl');gold={r['id']:r for r in test};sources={r['id']:r for r in rows(PACK/'data/test_reviewed.jsonl')}
independent={};errors=[]
for name,preds,field in [('baseline',base,'baseline_weights_sha256'),('trained',trained,'trained_weights_sha256')]:
 assert len(preds)==len(set(x['id'] for x in preds))==300 and set(x['id'] for x in preds)==set(gold)
 pr=read(DATA/f'predictions/{name}_test.receipt.json');assert pr['data_sha256']==freeze['splits']['test']['sha256'] and pr['weights_sha256']==selected[field]
 assert pr['questions_sha256']==hashlib.sha256(json.dumps(test[0]['questions'],sort_keys=True).encode()).hexdigest()
 tp=tn=fp=fn=0;nll=brier=0.
 for x in preds:
  g=gold[x['id']];assert x['gold']==g['gold']['route']['label'] and x['group_id']==g['group_id'] and x['family_id']==g['family_id']
  l=x['logits'];assert len(l)==2 and all(math.isfinite(v) for v in l)
  pred='DEEPFAKE' if l[1]>l[0] else 'BASE';assert pred==x['prediction']
  prob=1/(1+math.exp(l[0]-l[1]));assert math.isclose(prob,x['p_deepfake'],abs_tol=1e-12,rel_tol=1e-12)
  y=int(x['gold']=='DEEPFAKE');yp=int(pred=='DEEPFAKE')
  tp+=int(y and yp);tn+=int(not y and not yp);fp+=int(not y and yp);fn+=int(y and not yp)
  nll-=math.log(max(1e-12,prob if y else 1-prob));brier+=(prob-y)**2
  if name=='trained' and pred!=x['gold']:errors.append(dict(prediction=x,input=json.loads(g['state']),original_category=sources[x['id']]['category'],earlier_AI_review_reason=sources[x['id']]['pilot_label_reason']))
 mm=dict(n=300,tp=tp,tn=tn,fp=fp,fn=fn,accuracy=(tp+tn)/300,macro_f1=((2*tp/(2*tp+fp+fn))+(2*tn/(2*tn+fp+fn)))/2,deepfake_precision=tp/(tp+fp),deepfake_recall=tp/(tp+fn),base_false_activation_rate=fp/(fp+tn),nll=nll/300,brier=brier/300)
 for k,v in mm.items():assert math.isclose(v,pr['metrics'][k],abs_tol=1e-12,rel_tol=1e-12),(name,k,v,pr['metrics'][k])
 independent[name]=mm
sys.path.insert(0,str(PACK/'tools'));from compare import compare
comparison=compare(base,trained)
def same(a,b):
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 if isinstance(a,float):return math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12)
 return a==b
assert same(comparison,read(DATA/'comparison.json'))
subsets={}
for x in trained:
 cat=sources[x['id']]['category'];g=subsets.setdefault(cat,dict(n=0,correct=0));g['n']+=1;g['correct']+=int(x['gold']==x['prediction'])
for v in subsets.values():v['accuracy']=v['correct']/v['n']
reload=read(DATA/'RELOAD_RECEIPT.json');assert reload['weights_sha256']==selected['trained_weights_sha256'] and reload['predictions_identical_to_stored'] and reload['reloaded_rows']==24 and not reload['mismatched_ids']
result=dict(decision='SYNTHETIC_ROUTING_PILOT_COMPLETE_WITH_LABEL_AMBIGUITY_LIMITATION',internal_hashes_verified=len(m['files']),exact_reviewed_data_hashes_match=True,questions_hashes_resolved='Freeze hashes raw file bytes; inference receipts hash sorted question JSON. Both match their local sources.',raw_argmax_and_softmax_verified_for=600,independently_recomputed_metrics=independent,comparison_bootstrap_recomputed_exactly=True,epoch_selection_verified=4,epochs_completed=7,selected_checkpoint_planned_updates=500,completed_run_planned_updates=875,peak_allocated_GiB=receipt['peak_torch_allocated_bytes']/2**30,peak_allocated_decimal_GB=receipt['peak_torch_allocated_bytes']/1e9,error_count=len(errors),subsets=subsets,remote_reload_receipt_consistent=True,weights_locally_available_for_independent_reload=(ROOT/'model/trained_laya_router/model.safetensors').exists(),independent_model_reload_run_by_this_script=False,labels_changed_after_scoring=False,model_retrained_during_review=False)
(OUTPUT/'CODEX_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');(OUTPUT/'TEST_ERRORS.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in errors),encoding='utf-8');(OUTPUT/'RECOMPUTED_COMPARISON.json').write_text(json.dumps(comparison,indent=2)+'\n')
print('PASS',len(m['files']),'hashes; 600 raw predictions; exact data locks, metrics and bootstrap; development epoch selection.')
print('SUBSETS',json.dumps(subsets));print('MEMORY',result['peak_allocated_GiB'],'GiB /',result['peak_allocated_decimal_GB'],'GB')
