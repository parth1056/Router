"""CPU-only smoke checks of export/metrics/comparison. No model/accuracy result."""
from pathlib import Path
import sys,math,copy,ast
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from pilot_metrics import metrics,predictions
from export_pilot import convert
from compare import compare
for f in (root/'tools').glob('*.py'):ast.parse(f.read_text(encoding='utf-8'),filename=str(f))
s={'message':'How do I look?','history':[],'assets':[{'id':'a','kind':'image','availability':'available','support':'supported'}],'active_image_id':'a','last_analysis':None}
r={'id':'x','family_id':'f','input':s,'pilot_label':'BASE','pilot_label_source':'mock_AI_label','human_reviewed':False,'split_reservation':'TRAIN_ONLY'}
a=convert(r,'train');b=convert(dict(r,pilot_label='DEEPFAKE'),'train')
assert a['state']==b['state'] and a['gold']!=b['gold'],'Label leaked into state'
try:convert(r,'test');raise AssertionError('Train-only evaluation leak allowed')
except ValueError:pass
rows=[{'id':'x','family_id':'f','gold':{'route':{'label':'BASE'}}}]
p=predictions([(0,[0.,0.],[1.,0.],2)],rows)
assert p[0]['prediction']=='BASE' and p[0]['p_deepfake']==.5
m=metrics([0,0,1,1],[0,0,1,0],[.5,.1,.7,.2]);assert m['tp']==1 and m['tn']==2 and m['fn']==1 and m['accuracy']==.75
base=[];trained=[]
for i,(gold,bp,tp) in enumerate([('BASE','BASE','BASE'),('BASE','DEEPFAKE','BASE'),('DEEPFAKE','BASE','DEEPFAKE'),('DEEPFAKE','DEEPFAKE','DEEPFAKE')]):
    base.append({'id':str(i),'group_id':'g'+str(i),'family_id':'f'+str(i),'gold':gold,'prediction':bp,'p_deepfake':.8 if bp=='DEEPFAKE' else .2})
    trained.append({'id':str(i),'group_id':'g'+str(i),'family_id':'f'+str(i),'gold':gold,'prediction':tp,'p_deepfake':.8 if tp=='DEEPFAKE' else .2})
result=compare(base,trained);assert result['paired_wrong_to_right']==2 and result['paired_right_to_wrong']==0 and result['trained']['accuracy']==1.
print('PASS: Python syntax, label-free serialization, train-only split guard, exact tie handling, metrics and paired comparison. No GPU training/model evaluation was run here.')

freeze_source=(root/'tools/check_and_freeze.py').read_text(encoding='utf-8')
train_source=(root/'tools/train_laya.py').read_text(encoding='utf-8')
assert "len(datasets['train'])==2000" in freeze_source
assert "len(datasets['dev'])==200 and len(datasets['test'])==300" in freeze_source
assert 'len(train_rows)!=2000 or len(dev_rows)!=200' in train_source
assert 'len(family_sizes)>=500 and max(family_sizes.values())<=4' in freeze_source
print('PASS: approved 2000/200/300 size and training-family guards present.')
