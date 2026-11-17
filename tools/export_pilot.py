"""Explicitly authorised AI-labelled pilot export; never changes original human/acceptance flags."""
import argparse,json
from pathlib import Path
from state import serialize
from pilot_metrics import read_rows,LABELS
ROOT=Path(__file__).resolve().parents[1]
def convert(row,split):
    if split!='train' and row.get('split_reservation')=='TRAIN_ONLY':raise ValueError('Train-reserved case cannot become evaluation data')
    if row.get('pilot_label') in LABELS:
        label=row['pilot_label'];source=row.get('pilot_label_source')
        if not source:raise ValueError('Label source missing')
    elif row.get('label_source')=='codex_policy_review_of_derived_input':label=row['label'];source=row['label_source']
    else:raise ValueError('Explicit pilot label/adjudication required; intended_route or critic agreement alone is not ground truth')
    if label not in LABELS:raise ValueError('Unknown label')
    human=row.get('human_reviewed',False)
    if type(human) is not bool:raise ValueError('human_reviewed must be a real boolean; strings are not review evidence')
    rid=row.get('id') or row.get('candidate_id');family=row.get('family_id')
    if not rid or not family:raise ValueError('ID/family missing')
    return {'id':rid,'family_id':family,'group_id':row.get('template_group_id',row.get('template_cluster_id',family)),
            'split':split,'label_source':source,'human_reviewed':human,
            'state':serialize(row['input']),'questions':json.loads((ROOT/'config/questions.json').read_text(encoding='utf-8')),
            'gold':{'route':{'label':label,'probabilities':{k:float(k==label) for k in LABELS}}}}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--split',choices=['train','dev','test'],required=True);p.add_argument('--out',required=True);a=p.parse_args()
    rows=[convert(r,a.split) for r in read_rows(a.input)]
    if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('Empty/duplicate IDs')
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise ValueError('Preserve old export; choose a new path')
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    print('Exported',len(rows),a.split,'pilot rows; no claim of human review/final-data acceptance.')
