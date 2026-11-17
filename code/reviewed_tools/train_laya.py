"""Single seeded pilot fit, dev-only checkpoint selection; NEVER scores the test."""
import argparse,copy,json,math,random,time
from pathlib import Path
from pilot_metrics import read_rows,file_sha,predictions,summarise,write_json
ROOT=Path(__file__).resolve().parents[1]
class DevelopmentStop(Exception):pass

def main():
    import numpy as np
    import torch
    from laya.train import TrainConfig,load_checkpoint,items_from_rows,train_model,calibration_records,save_checkpoint,optimizer_updates
    from laya.common import uses_parallel_layout
    p=argparse.ArgumentParser()
    for k in ['train','dev','model','out','freeze']:p.add_argument('--'+k,required=True)
    p.add_argument('--seed',type=int,default=42);p.add_argument('--epochs',type=int,default=8)
    p.add_argument('--micro-batch',type=int,default=4);p.add_argument('--grad-accum',type=int,default=4)
    p.add_argument('--head-lr',type=float,default=1e-4);p.add_argument('--freeze-encoder',action='store_true')
    a=p.parse_args();approval=json.loads((ROOT/'APPROVAL.json').read_text(encoding='utf-8'))
    if not approval['pilot_training_authorised']:raise RuntimeError('Pilot authorisation missing')
    if not torch.cuda.is_available():raise RuntimeError('Existing college CUDA environment required')
    if a.micro_batch*a.grad_accum!=16:raise ValueError('Preserve effective batch 16 for memory fallback')
    if a.seed!=42 or not 1<=a.epochs<=8:raise ValueError('Bounded seed42 run, at most eight epochs')
    freeze=json.loads(Path(a.freeze).read_text(encoding='utf-8'))
    if freeze['overlaps'] or freeze['bad_token_rows']:raise ValueError('Unresolved frozen-data defects')
    for k in ['train','dev']:
        if file_sha(getattr(a,k))!=freeze['splits'][k]['sha256']:raise ValueError('Data changed after freeze')
    out=Path(a.out)
    if out.exists():raise ValueError('New run directory required; preserve old results')
    out.mkdir(parents=True)
    random.seed(a.seed);np.random.seed(a.seed);torch.manual_seed(a.seed);torch.cuda.manual_seed_all(a.seed)
    train_rows=read_rows(a.train);dev_rows=read_rows(a.dev)
    if len(train_rows)!=2000 or len(dev_rows)!=200:raise ValueError('Approved sizes: 2000 train / 200 dev')
    model,tok,cfg=load_checkpoint(a.model)
    if cfg.get('max_len')!=512:raise ValueError('Wrong checkpoint/config; use reviewed English LAYA')
    parallel=uses_parallel_layout(cfg);tr,tskip=items_from_rows(tok,train_rows,512,192);dv,dskip=items_from_rows(tok,dev_rows,512,192)
    if len(tr)!=len(train_rows) or len(dv)!=len(dev_rows) or any(tskip.values()) or any(dskip.values()):raise ValueError('Skipped/multiple questions')
    probes={}
    for group in ['encoder','head']:
        candidates=[(n,p_) for n,p_ in model.named_parameters() if p_.ndim>=2 and (n.startswith('encoder.')==(group=='encoder'))]
        candidates.sort(key=lambda x:('embed' in x[0].lower(),x[0]))
        for n,p_ in candidates[:8]:
            idx=torch.linspace(0,p_.numel()-1,min(128,p_.numel()),device=p_.device).long()
            probes[n]=(idx.cpu(),p_.detach().flatten()[idx].cpu().clone())
    def weight_changes():
        params=dict(model.named_parameters());result={'encoder_max_probe_delta':0.,'head_max_probe_delta':0.}
        for n,(idx,old) in probes.items():
            now=params[n].detach().flatten()[idx.to(params[n].device)].float().cpu();delta=float((now-old.float()).abs().max())
            key='encoder_max_probe_delta' if n.startswith('encoder.') else 'head_max_probe_delta';result[key]=max(result[key],delta)
        return result
    device=torch.device('cuda');model.to(device);torch.cuda.reset_peak_memory_stats()
    baseline_records=calibration_records(model,tok,dv,device,512,192,batch_size=16,parallel=parallel)
    baseline=summarise(predictions(baseline_records,dev_rows));write_json(out/'baseline_dev.json',baseline)
    config=TrainConfig(epochs=a.epochs,micro_batch=a.micro_batch,grad_accum=a.grad_accum,encoder_lr=2.5e-5,head_lr=a.head_lr,
                       loss='soft-ce',shuffle_options=('choice',),seed=a.seed,max_len=512,head_max_len=192,
                       calib_frac=0.,freeze_encoder=a.freeze_encoder,log_every=25)
    saved=copy.deepcopy(cfg);saved.update(max_len=512,head_max_len=192,temperature=[1.,1.,1.],fine_tuned=True)
    saved.pop('temperature_by_options',None);saved.pop('abstention_thresholds',None)
    saved['training']={'project':'Polyvalent same-day synthetic pilot','seed':42,'encoder_frozen':a.freeze_encoder,
                       'calibration':'none, identity temperatures; compare raw logits','source_weights_sha256':file_sha(Path(a.model)/'model.safetensors')}
    best=None;history=[];stale=0;start=time.perf_counter();stop_reason='maximum epochs'
    def epoch_end(epoch,loss):
        nonlocal best,stale
        if not math.isfinite(loss):raise ValueError('Nonfinite training loss')
        records=calibration_records(model,tok,dv,device,512,192,batch_size=16,parallel=parallel)
        dev=summarise(predictions(records,dev_rows));rank=(dev['macro_f1'],-dev['base_false_activation_rate'],-dev['nll'],-epoch)
        changed=weight_changes();entry={'epoch':epoch+1,'train_loss':loss,'dev':dev,'weight_probe_changes':changed};history.append(entry)
        if best is None or rank>best[0]:
            ck=out/('epoch_%02d'%(epoch+1));save_checkpoint(model,tok,saved,str(ck))
            (ck/'questions.json').write_text(json.dumps(train_rows[0]['questions'],indent=2)+'\n',encoding='utf-8')
            best=(rank,str(ck.resolve()),epoch+1,dev);stale=0
        else:stale+=1
        write_json(out/'history.json',history)
        write_json(out/'selection.json',{'selected_checkpoint':best[1],'selected_epoch':best[2],'selected_dev':best[3],
                     'baseline_dev':baseline,'source_weights_sha256':saved['training']['source_weights_sha256'],'source_checkpoint':str(Path(a.model).resolve()),'selection':'development only; no test read/scored','seed':42,'encoder_frozen':a.freeze_encoder,
                     'train_sha256':file_sha(a.train),'dev_sha256':file_sha(a.dev),'test_sha256':freeze['splits']['test']['sha256']})
        model.train()
        if a.freeze_encoder:model.encoder.eval()
        if epoch+1>=4 and stale>=3:raise DevelopmentStop('Development patience reached after minimum four epochs')
    try:train_model(model,tok,tr,config,device,512,192,on_epoch_end=epoch_end,parallel=parallel)
    except DevelopmentStop as e:stop_reason=str(e)
    changes=weight_changes()
    if max(changes.values())==0:raise ValueError('No sampled parameter changes; training not established')
    write_json(out/'training_receipt.json',{'epochs_completed':len(history),'stop_reason':stop_reason,'seconds':time.perf_counter()-start,
                'n_train':len(tr),'n_dev':len(dv),'seed':42,'micro_batch':a.micro_batch,'grad_accum':a.grad_accum,
                'planned_optimizer_updates_for_completed_epochs':optimizer_updates(len(tr),a.micro_batch,a.grad_accum,len(history)),
                'actual_optimizer_step_count':'not separately instrumented; do not equate planned with AMP-executed steps',
                'weight_probe_changes':changes,'peak_torch_allocated_bytes':torch.cuda.max_memory_allocated(),
                'selected_checkpoint':best[1],'test_opened':False,'human_review_claim':False})
    print(json.dumps({'selected_checkpoint':best[1],'selected_dev':best[3],'baseline_dev':baseline,'seconds':time.perf_counter()-start},indent=2))
if __name__=='__main__':main()
