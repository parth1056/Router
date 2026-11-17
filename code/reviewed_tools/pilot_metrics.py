import math,json,hashlib
from pathlib import Path
LABELS=('BASE','DEEPFAKE')
def read_rows(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]
def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def metrics(gold,pred,probs=None):
    if not gold or len(gold)!=len(pred):raise ValueError('Empty or mismatched predictions')
    if any(v not in (0,1) for v in list(gold)+list(pred)):raise ValueError('Binary labels required')
    tp=sum(y==h==1 for y,h in zip(gold,pred));tn=sum(y==h==0 for y,h in zip(gold,pred))
    fp=sum(y==0 and h==1 for y,h in zip(gold,pred));fn=sum(y==1 and h==0 for y,h in zip(gold,pred))
    d=lambda a,b:a/b if b else 0.
    f1=d(2*tp,2*tp+fp+fn);b1=d(2*tn,2*tn+fp+fn)
    m={'n':len(gold),'tp':tp,'tn':tn,'fp':fp,'fn':fn,'accuracy':d(tp+tn,len(gold)),
       'macro_f1':(f1+b1)/2,'deepfake_precision':d(tp,tp+fp),'deepfake_recall':d(tp,tp+fn),
       'deepfake_f1':f1,'base_false_activation_rate':d(fp,fp+tn)}
    if probs is not None:
        if len(probs)!=len(gold) or any(not math.isfinite(v) or not 0<=v<=1 for v in probs):raise ValueError('Invalid probabilities')
        m['nll']=-sum(math.log(max(1e-12,p if y else 1-p)) for y,p in zip(gold,probs))/len(gold)
        m['brier']=sum((p-y)**2 for y,p in zip(gold,probs))/len(gold)
    return m
def predictions(records,rows):
    if len(records)!=len(rows):raise ValueError('Silent skipped/multiple questions')
    output=[]
    for (qt,logits,target,k),row in zip(records,rows):
        if k!=2:raise ValueError('Expected binary choice')
        expected=row['gold']['route']['label'];gold=LABELS.index(expected)
        if list(target).index(max(target))!=gold:raise ValueError('Target/order mismatch')
        v=[float(x) for x in logits]
        if any(not math.isfinite(x) for x in v):raise ValueError('Nonfinite logits')
        e=[math.exp(x-max(v)) for x in v];p=e[1]/sum(e)
        pred=int(v[1]>v[0]) # exact ties are BASE, matching canonical argmax
        output.append({'id':row['id'],'family_id':row['family_id'],'group_id':row.get('group_id',row['family_id']),
                       'gold':expected,'prediction':LABELS[pred],'p_deepfake':p,'logits':v})
    return output
def summarise(rows):return metrics([LABELS.index(r['gold']) for r in rows],[LABELS.index(r['prediction']) for r in rows],[r['p_deepfake'] for r in rows])
def write_json(path,value):Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
