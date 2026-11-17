"""Select from completed dev-only candidates before opening test scores."""
import argparse,json,datetime
from pathlib import Path
from pilot_metrics import file_sha,write_json
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selection',action='append',required=True);p.add_argument('--baseline-model',required=True);p.add_argument('--data-freeze',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    if Path(a.out).exists():raise ValueError('Preserve the frozen evaluation; do not reselect after test inspection')
    data=json.loads(Path(a.data_freeze).read_text(encoding='utf-8'));candidates=[]
    original_sha=file_sha(Path(a.baseline_model)/'model.safetensors')
    for i,path in enumerate(a.selection):
        s=json.loads(Path(path).read_text(encoding='utf-8'))
        assert s['source_weights_sha256']==original_sha,'Candidate does not start from the same original baseline'
        assert s['train_sha256']==data['splits']['train']['sha256'] and s['dev_sha256']==data['splits']['dev']['sha256'] and s['test_sha256']==data['splits']['test']['sha256']
        m=s['selected_dev'];rank=(m['macro_f1'],-m['base_false_activation_rate'],-m['nll'],-i)
        candidates.append((rank,s,path))
    _,best,path=max(candidates,key=lambda x:x[0]);weight=Path(best['selected_checkpoint'])/'model.safetensors'
    result={'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'test_sha256':data['splits']['test']['sha256'],
            'baseline_checkpoint':str(Path(a.baseline_model).resolve()),'baseline_weights_sha256':file_sha(Path(a.baseline_model)/'model.safetensors'),
            'selected_checkpoint':best['selected_checkpoint'],'trained_weights_sha256':file_sha(weight),'selected_selection_file':path,
            'selected_dev':best['selected_dev'],'candidate_selections':[s for _,s,_ in candidates],
            'questions_sha256':file_sha(ROOT/'config/questions.json'),'serializer_sha256':file_sha(ROOT/'tools/state.py'),
            'test_scored_before_selection':False,'type':'group-held-out synthetic pilot','raw_argmax':True}
    assert result['baseline_weights_sha256']!=result['trained_weights_sha256'],'No differing trained artifact'
    write_json(a.out,result);print(json.dumps(result,indent=2))
