"""Input-only split/token checks; no checkpoint scoring or training."""
import argparse,json,re,collections
from pathlib import Path
from pilot_metrics import read_rows,file_sha,write_json

def normalised_state(text):
    s=json.loads(text);names=[]
    for a in s['assets']:
        if a['id'] not in names:names.append(a['id'])
    if s['last_analysis'] and s['last_analysis']['asset_id'] not in names:names.append(s['last_analysis']['asset_id'])
    raw=json.dumps(s,sort_keys=True,ensure_ascii=False)
    for i,name in enumerate(names):raw=re.sub(r'(?<![\w])'+re.escape(name)+r'(?![\w])','asset_'+str(i),raw)
    return re.sub(r'\s+',' ',raw).strip().lower()
def main():
    from transformers import AutoTokenizer
    from laya.train import items_from_rows
    from laya.common import build_sequence
    from laya.agent import _fix_tokenizer_config
    p=argparse.ArgumentParser()
    for key in ['train','dev','test','model','out']:p.add_argument('--'+key,required=True)
    a=p.parse_args();_fix_tokenizer_config(a.model);tok=AutoTokenizer.from_pretrained(str(Path(a.model)/'tokenizer'))
    datasets={k:read_rows(getattr(a,k)) for k in ['train','dev','test']}
    assert len(datasets['train'])==2000,'Approved training size is 2000'
    assert len(datasets['dev'])==200 and len(datasets['test'])==300
    family_sizes=collections.Counter(r['family_id'] for r in datasets['train'])
    assert len(family_sizes)>=500 and max(family_sizes.values())<=4,'Use at least 500 honest scenario families and at most four variants per family; renaming a derivative does not make it independent'
    sets={};reports={};all_questions=None;bad=[]
    for split,rows in datasets.items():
        ids=[r['id'] for r in rows];families={r['family_id'] for r in rows};groups={r.get('group_id',r['family_id']) for r in rows}
        assert len(ids)==len(set(ids)),'Duplicate IDs'
        assert {r['gold']['route']['label'] for r in rows}=={'BASE','DEEPFAKE'}
        for r in rows:
            q=r['questions']
            if all_questions is None:all_questions=q
            assert q==all_questions and list(q)==['route'] and q['route']['type']=='choice' and list(q['route']['criteria'])==['BASE','DEEPFAKE']
            g=r['gold']['route'];assert g['probabilities']=={k:float(k==g['label']) for k in ['BASE','DEEPFAKE']}
        norms=[normalised_state(r['state']) for r in rows]
        assert len(norms)==len(set(norms)),'Normalised exact duplicates inside '+split
        items,skipped=items_from_rows(tok,rows,512,192)
        assert len(items)==len(rows) and not any(skipped.values()),(split,skipped)
        lengths=[]
        for row,it in zip(rows,items):
            ids_,markers,stats,trunc=build_sequence(tok,row['state'],it['q'],512,192,return_stats=True,return_truncation_stats=True)
            if len(markers)!=2 or stats['options_distinct']!=2 or trunc['state_tokens_dropped']:
                bad.append({'split':split,'id':row['id'],'option_stats':stats,'truncation':trunc})
            lengths.append(len(ids_))
        sets[split]={'ids':set(ids),'families':families,'groups':groups,'inputs':set(norms)}
        reports[split]={'n':len(rows),'sha256':file_sha(getattr(a,split)),'labels':dict(collections.Counter(r['gold']['route']['label'] for r in rows)),
                        'max_assembled_tokens':max(lengths),'family_count':len(families),'group_count':len(groups)}
    overlaps=[]
    for left,right in [('train','dev'),('train','test'),('dev','test')]:
        for field in ['ids','families','groups','inputs']:
            if sets[left][field]&sets[right][field]:overlaps.append({'splits':[left,right],'field':field,'count':len(sets[left][field]&sets[right][field])})
    receipt={'splits':reports,'overlaps':overlaps,'bad_token_rows':bad,'evaluation_type':'group-held-out synthetic pilot; no human-test claim','test_scored':False}
    write_json(a.out,receipt)
    if overlaps or bad:raise ValueError('Resolve reported overlap/token defects BEFORE fitting; do not silently truncate or change held-out labels after scoring')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
