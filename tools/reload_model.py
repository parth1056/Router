"""Fresh local model-load check. Does not train, relabel or tune against test."""
from pathlib import Path
import argparse,json,sys
from pilot_metrics import predictions,file_sha,write_json
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default=str(ROOT/'model/trained_laya_router'));p.add_argument('--device',choices=['cpu','cuda'],default='cpu');p.add_argument('--count',type=int,default=24);p.add_argument('--out',default=str(ROOT/'verification_output/local_reload.json'));a=p.parse_args()
 import torch
 from laya.train import load_checkpoint,items_from_rows,calibration_records
 from laya.common import uses_parallel_layout
 if a.device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA is unavailable; use --device cpu')
 if not 1<=a.count<=300:raise ValueError('Count must be 1..300')
 out=Path(a.out)
 if out.exists():raise ValueError('Preserve earlier check: choose a new --out path')
 rows=[json.loads(x) for x in (ROOT/'data/test.laya.jsonl').read_text(encoding='utf-8').splitlines()][:a.count]
 saved={r['id']:r for r in [json.loads(x) for x in (ROOT/'results/trained_test.jsonl').read_text(encoding='utf-8').splitlines()]}
 model,tok,cfg=load_checkpoint(a.model);device=torch.device(a.device);model.to(device)
 items,skipped=items_from_rows(tok,rows,512,192)
 if len(items)!=len(rows) or any(skipped.values()):raise ValueError('Items were skipped')
 fresh=predictions(calibration_records(model,tok,items,device,512,192,batch_size=4,parallel=uses_parallel_layout(cfg)),rows)
 different=[r['id'] for r in fresh if r['prediction']!=saved[r['id']]['prediction']]
 result={'model':str(Path(a.model).resolve()),'weights_sha256':file_sha(Path(a.model)/'model.safetensors'),'device':a.device,'checked':len(fresh),'class_predictions_match':not different,'different_ids':different,'scope':'Fresh re-load check only. Small numerical differences across hardware are not retuning permission.'}
 write_json(out,result);print(json.dumps(result,indent=2))
 if different:raise RuntimeError('Class predictions differ; preserve report and inspect runtime compatibility without changing test labels')
if __name__=='__main__':main()
