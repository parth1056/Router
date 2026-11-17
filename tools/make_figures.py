"""Rebuild publication/presentation figures from preserved result JSON only."""
from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'results/comparison.json').read_text(encoding='utf-8'))
H=json.loads((ROOT/'results/primary/history.json').read_text(encoding='utf-8'))
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True);(ROOT/'tables').mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'semibold'})
colors=['#647A91','#007F78']
def save(fig,name):
 fig.savefig(OUT/(name+'.svg'),bbox_inches='tight',facecolor='white');fig.savefig(OUT/(name+'.png'),dpi=240,bbox_inches='tight',facecolor='white');plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(10.8,3.7));fig.subplots_adjust(bottom=.25,wspace=.38)
for ax,(key,title) in zip(axs,[('accuracy','Accuracy'),('macro_f1','Macro-F1'),('base_false_activation_rate','False DEEPFAKE activation')]):
 scale=1 if key=='macro_f1' else 100
 vals=[scale*C[k][key] for k in ['baseline','trained']];bars=ax.bar([0,1],vals,color=colors,width=.58)
 ax.set_xticks([0,1],['Original','Fine-tuned']);ax.set_ylim(0,1.08*scale);ax.set_yticks([0,.25*scale,.5*scale,.75*scale,scale]);ax.set_ylabel('Score' if scale==1 else '%');ax.set_title(title);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
 for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+.02*scale,f'{v:.4f}' if scale==1 else f'{v:.2f}',ha='center',fontsize=11)
 ax.text(.5,-.23,'Lower is better' if key=='base_false_activation_rate' else 'Higher is better',transform=ax.transAxes,ha='center',color='#485563',fontsize=9)
fig.text(.5,.015,'Frozen AI-labelled synthetic test: 300 requests in 105 groups; one seed. False activation is measured among 186 BASE requests.',ha='center',fontsize=8.5,color='#485563')
save(fig,'routing_comparison')
fig,axs=plt.subplots(1,2,figsize=(8.5,3.8));fig.subplots_adjust(bottom=.2,wspace=.35,right=.88)
for ax,name,title in zip(axs,['baseline','trained'],['Original pretrained LAYA','Routing fine-tuned LAYA']):
 m=C[name];arr=[[m['tn'],m['fp']],[m['fn'],m['tp']]];im=ax.imshow(arr,cmap='Blues',vmin=0,vmax=186)
 ax.set_xticks([0,1],['BASE','DEEPFAKE']);ax.set_yticks([0,1],['BASE','DEEPFAKE']);ax.set_xlabel('Predicted route');ax.set_ylabel('Frozen label');ax.set_title(title)
 for i in range(2):
  for j in range(2):ax.text(j,i,str(arr[i][j]),ha='center',va='center',color='white' if arr[i][j]>95 else '#122B40',fontsize=18)
cax=fig.add_axes([.91,.24,.025,.58]);fig.colorbar(im,cax=cax,label='Requests');fig.text(.5,.015,'Identical 300 test inputs and labels for both checkpoints. Positive class: DEEPFAKE.',ha='center',fontsize=9)
save(fig,'routing_confusion_matrices')
fig,ax=plt.subplots(figsize=(7.6,3.9));fig.subplots_adjust(bottom=.22)
epoch=[h['epoch'] for h in H];score=[h['dev']['macro_f1'] for h in H]
ax.plot(epoch,score,'o-',color=colors[1],lw=2,label='Fine-tuned development macro-F1')
b=json.loads((ROOT/'results/primary/baseline_dev.json').read_text())['macro_f1'];ax.axhline(b,color=colors[0],ls='--',label='Original development macro-F1');ax.axvline(4,color='#A56220',ls=':',label='Selected epoch 4')
ax.set(xlabel='Completed epoch',ylabel='Development macro-F1',xticks=epoch,ylim=(.53,1.005));ax.grid(alpha=.15);ax.legend(loc='center right',bbox_to_anchor=(1,.35),frameon=False,fontsize=8.5)
fig.text(.5,.025,'200 development examples; checkpoint selected by development metrics. No test scores used for selection.',ha='center',fontsize=8.5)
save(fig,'development_learning_curve')
fig,ax=plt.subplots(figsize=(12,4.3));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
def box(x,y,w,h,text,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.012,rounding_size=.018',fc=color,ec='#587082',lw=1));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,lw=1.5,color='#35566A',connectionstyle='arc3'))
box(.025,.25,.22,.50,'Current message\nRecent conversation\nTrusted attachment state\nSelected image\nStored prior result','#EEF3F7')
box(.30,.34,.18,.32,'Canonical serializer\n+ fixed routing\nquestion and choices','#E6F1F8')
box(.535,.25,.235,.50,'English LAYA\nModernBERT-large encoder\n+ typed decision head\n\nEncoder and head fine-tuned','#D9EEEB')
box(.83,.58,.145,.17,'BASE label','#EAF0F6');box(.83,.25,.145,.17,'DEEPFAKE label','#D7EBE6')
arrow((.245,.5),(.30,.5));arrow((.48,.5),(.535,.5));arrow((.77,.58),(.83,.665));arrow((.77,.42),(.83,.335))
ax.text(.5,.09,'Raw two-choice argmax; exact ties select BASE. LAYA routes from text/state; image authenticity is assessed by the specialist after routing.',ha='center',fontsize=9,color='#485563')
ax.text(.5,.95,'Routing component evaluated in this experiment',ha='center',fontsize=14,fontweight='semibold')
save(fig,'router_architecture')
with (ROOT/'tables/metrics.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['metric','original','fine_tuned'])
 for k in ['n','accuracy','macro_f1','deepfake_precision','deepfake_recall','base_false_activation_rate','nll','brier','tp','tn','fp','fn']:w.writerow([k,C['baseline'][k],C['trained'][k]])
with (ROOT/'tables/epoch_history.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['epoch','training_loss','dev_macro_f1','dev_accuracy','dev_base_false_activation','dev_nll','selected'])
 for h in H:w.writerow([h['epoch'],h['train_loss'],h['dev']['macro_f1'],h['dev']['accuracy'],h['dev']['base_false_activation_rate'],h['dev']['nll'],h['epoch']==4])
(OUT/'FIGURE_GENERATION.json').write_text(json.dumps({'source':'Preserved comparison/history JSON; no generated or estimated result values','matplotlib':matplotlib.__version__,'formats':['SVG vector','PNG'],'uncertainty':'No invented seed variability or accuracy error bars; group-bootstrap delta is in result JSON','scope':'Synthetic benchmark only; see archive_review/RESULTS_CODEX_REVIEW.md for indirect-label ambiguity'},indent=2)+'\n')
print('Created four SVG/PNG figures and two CSV tables from verified results.')
