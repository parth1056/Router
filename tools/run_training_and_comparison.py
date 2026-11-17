"""One integrated fit/select/test/export run after input-only data freeze."""
import argparse,json,subprocess,sys,time,shutil,zipfile
from pathlib import Path
from pilot_metrics import file_sha,write_json
TOOLS=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser()
    for k in ['model','train','dev','test','freeze','out']:p.add_argument('--'+k,required=True)
    p.add_argument('--micro-batch',type=int,default=4);p.add_argument('--grad-accum',type=int,default=4)
    p.add_argument('--recovery-budget-minutes',type=int,default=120)
    a=p.parse_args();out=Path(a.out)
    if out.exists():raise ValueError('Preserve earlier runs; select a new pipeline output directory')
    out.mkdir(parents=True);start=time.perf_counter();commands=[]
    frozen=json.loads(Path(a.freeze).read_text(encoding='utf-8'))
    for k in ['train','dev','test']:
        if file_sha(getattr(a,k))!=frozen['splits'][k]['sha256']:raise ValueError('Input changed after freeze: '+k)
    def run(name,script,args):
        cmd=[sys.executable,str(TOOLS/script)]+[str(x) for x in args]
        commands.append({'stage':name,'command':cmd});write_json(out/'commands.json',commands)
        print('RUN',name,flush=True)
        with (out/(name+'.log')).open('w',encoding='utf-8') as log:
            proc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        if proc.returncode:raise RuntimeError(name+' failed; see '+str(out/(name+'.log')))
    baseargs=['--train',a.train,'--dev',a.dev,'--model',a.model,'--freeze',a.freeze,
              '--micro-batch',a.micro_batch,'--grad-accum',a.grad_accum]
    run('primary_training','train_laya.py',baseargs+['--out',out/'primary'])
    primary=json.loads((out/'primary/selection.json').read_text(encoding='utf-8'));selections=[out/'primary/selection.json']
    remaining=a.recovery_budget_minutes-(time.perf_counter()-start)/60
    if primary['selected_dev']['macro_f1']<=primary['baseline_dev']['macro_f1'] and remaining>=30:
        try:
            run('head_recovery','train_laya.py',baseargs+['--out',out/'head_recovery','--freeze-encoder','--head-lr','0.0003','--epochs','6'])
            selections.append(out/'head_recovery/selection.json')
        except RuntimeError as error:
            write_json(out/'recovery_failure.json',{'error':str(error),'action':'Optional candidate failed; retain valid primary and disclose failure.'})
    selectargs=['--baseline-model',a.model,'--data-freeze',a.freeze,'--out',out/'FINAL_EVAL_FREEZE.json']
    for s in selections:selectargs+=['--selection',s]
    run('freeze_selection','select_and_freeze.py',selectargs)
    selected=json.loads((out/'FINAL_EVAL_FREEZE.json').read_text(encoding='utf-8'))
    # Both evaluations use separate fresh processes/checkpoint loads and the same unchanged test.
    run('baseline_test','evaluate_laya.py',['--model',a.model,'--data',a.test,'--out',out/'baseline_test.jsonl'])
    run('trained_test','evaluate_laya.py',['--model',selected['selected_checkpoint'],'--data',a.test,'--out',out/'trained_test.jsonl'])
    run('comparison','compare.py',['--baseline',out/'baseline_test.jsonl','--trained',out/'trained_test.jsonl','--freeze',out/'FINAL_EVAL_FREEZE.json','--out',out/'comparison.json'])
    release=out/'trained_laya_router';shutil.copytree(selected['selected_checkpoint'],release)
    shutil.copy2(TOOLS/'state.py',release/'input_serializer.py')
    shutil.copy2(out/'FINAL_EVAL_FREEZE.json',release/'comparison_provenance.json')
    if file_sha(release/'model.safetensors')!=selected['trained_weights_sha256']:raise ValueError('Release copy differs')
    archive=out/'trained_laya_router.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        for f in sorted(release.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(release).as_posix())
    summary={'status':'TRAINED_AND_EVALUATED_SYNTHETIC_PILOT','seconds':time.perf_counter()-start,
             'selected_checkpoint':selected['selected_checkpoint'],'release_dir':str(release.resolve()),
             'full_model_archive':str(archive.resolve()),'archive_sha256':file_sha(archive),
             'test_sha256':selected['test_sha256'],'comparison':json.loads((out/'comparison.json').read_text(encoding='utf-8')),
             'limits':'Actual held-out synthetic comparison; not a human-test/production certification. No desired improvement is fabricated.'}
    write_json(out/'FINISHED.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
