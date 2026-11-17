"""Paired fixed-test comparison; no model or threshold fitting."""
import argparse,json,random,collections
from pathlib import Path
from pilot_metrics import read_rows,summarise,metrics,LABELS,write_json

def compare(base,trained):
    b={r['id']:r for r in base};t={r['id']:r for r in trained}
    if len(b)!=len(base) or len(t)!=len(trained) or set(b)!=set(t):raise ValueError('Different/duplicate test IDs')
    keys=sorted(b)
    for k in keys:
        if b[k]['gold']!=t[k]['gold'] or b[k]['group_id']!=t[k]['group_id']:raise ValueError('Different gold/group per test ID')
    bm=summarise([b[k] for k in keys]);tm=summarise([t[k] for k in keys])
    wins=sum(b[k]['prediction']!=b[k]['gold'] and t[k]['prediction']==t[k]['gold'] for k in keys)
    losses=sum(b[k]['prediction']==b[k]['gold'] and t[k]['prediction']!=t[k]['gold'] for k in keys)
    groups=collections.defaultdict(list)
    for k in keys:groups[b[k]['group_id']].append(k)
    names=sorted(groups);rng=random.Random(42);deltas=[]
    for _ in range(1000):
        sample=[k for g in rng.choices(names,k=len(names)) for k in groups[g]]
        deltas.append(summarise([t[k] for k in sample])['macro_f1']-summarise([b[k] for k in sample])['macro_f1'])
    deltas.sort()
    return {'baseline':bm,'trained':tm,'delta_accuracy_pp':100*(tm['accuracy']-bm['accuracy']),
            'delta_macro_f1':tm['macro_f1']-bm['macro_f1'],'paired_wrong_to_right':wins,'paired_right_to_wrong':losses,
            'group_bootstrap_delta_macro_f1_95pct':[deltas[24],deltas[974]],'bootstrap_groups':len(names),
            'majority_BASE':metrics([LABELS.index(b[k]['gold']) for k in keys],[0]*len(keys)),
            'observed_primary_improvement':tm['macro_f1']>bm['macro_f1'],
            'limits':'Observed result on a frozen synthetic test, one selected seed42 run; not human-test or production-accuracy evidence. Bootstrap groups must represent shared scenario/template dependence.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--trained',required=True);p.add_argument('--freeze',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    frozen=json.loads(Path(a.freeze).read_text(encoding='utf-8'))
    for pred,field in [(a.baseline,'baseline_weights_sha256'),(a.trained,'trained_weights_sha256')]:
        receipt=json.loads(Path(pred).with_suffix('.receipt.json').read_text(encoding='utf-8'))
        if receipt['data_sha256']!=frozen['test_sha256'] or receipt['weights_sha256']!=frozen[field]:raise ValueError('Predictions do not match frozen test/checkpoint')
    result=compare(read_rows(a.baseline),read_rows(a.trained));write_json(a.out,result)
    md=Path(a.out).with_suffix('.md')
    lines=['# LAYA routing fine-tuning: fixed synthetic-test comparison','', '| Metric | Original pretrained LAYA | Routing fine-tuned LAYA |','|---|---:|---:|']
    for name in ['accuracy','macro_f1','deepfake_precision','deepfake_recall','base_false_activation_rate']:
        lines.append('| '+name+' | %.4f | %.4f |'%(result['baseline'][name],result['trained'][name]))
    lines+=['','Accuracy difference: %+.2f percentage points.'%result['delta_accuracy_pp'],
            'Macro-F1 difference: %+.4f.'%result['delta_macro_f1'],
            'Paired corrections/regressions: %d / %d.'%(result['paired_wrong_to_right'],result['paired_right_to_wrong']),
            '',result['limits']]
    md.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
