"""Raw-logit evaluation of an explicit checkpoint on one fixed file; no fitting/calibration."""
import argparse,json,time
from pathlib import Path
from pilot_metrics import read_rows,file_sha,predictions,summarise,write_json

def main():
    import torch
    from laya.train import load_checkpoint,items_from_rows,calibration_records
    from laya.common import uses_parallel_layout
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--batch-size',type=int,default=16);a=p.parse_args()
    out=Path(a.out)
    if out.exists():raise ValueError('Preserve prior predictions; use new output path')
    if not torch.cuda.is_available():raise RuntimeError('Expected the existing college CUDA environment')
    rows=read_rows(a.data)
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate IDs')
    model,tok,cfg=load_checkpoint(a.model);model.to('cuda')
    items,skipped=items_from_rows(tok,rows,512,192)
    if any(skipped.values()) or len(items)!=len(rows):raise ValueError('Skipped/multiple items: '+str(skipped))
    torch.cuda.synchronize();start=time.perf_counter()
    records=calibration_records(model,tok,items,torch.device('cuda'),512,192,batch_size=a.batch_size,parallel=uses_parallel_layout(cfg))
    torch.cuda.synchronize();elapsed=time.perf_counter()-start
    result=predictions(records,rows);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(''.join(json.dumps(r)+'\n' for r in result),encoding='utf-8')
    receipt={'checkpoint':str(Path(a.model).resolve()),'weights_sha256':file_sha(Path(a.model)/'model.safetensors'),
             'data_sha256':file_sha(a.data),'questions_sha256':__import__('hashlib').sha256(json.dumps(rows[0]['questions'],sort_keys=True).encode()).hexdigest(),
             'metrics':summarise(result),'seconds':elapsed,'batch_size':a.batch_size,
             'scoring':'canonical raw logits, no temperature/threshold tuning; exact ties BASE',
             'limits':'Synthetic held-out pilot evidence unless independently established otherwise.'}
    write_json(out.with_suffix('.receipt.json'),receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
