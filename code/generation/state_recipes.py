"""Synthetic target-state fixtures, not operational image or detection measurements."""
def make_state(name):
    image=lambda i,status='available',support='supported':{'id':i,'kind':'image','availability':status,'support':support}
    s={'assets':[image('img_1')],'active_image_id':'img_1','last_analysis':None}
    if name=='no_assets':return {'assets':[],'active_image_id':None,'last_analysis':None}
    if name in ['stored_real','stored_fake','stored_removed']:
        s['last_analysis']={'asset_id':'img_1','verdict':'REAL' if name=='stored_real' else 'FAKE','confidence':None,'evidence_summary':['A prior authenticity report is available.']}
        if name=='stored_removed':s['assets'][0]['availability']='missing'
    elif name in ['unsupported','unknown']:s['assets'][0]['support']=name
    elif name in ['missing','expired']:s['assets'][0]['availability']=name
    elif name=='multiple':s['assets'].append(image('img_2'));s['active_image_id']=None
    elif name=='video':s['assets']=[{'id':'clip_1','kind':'video','availability':'available','support':'unsupported'}];s['active_image_id']=None
    elif name in ['new','new_old_missing']:
        s['assets']=[image('img_1','missing' if name=='new_old_missing' else 'available'),image('img_2')]
        s['active_image_id']='img_2';s['last_analysis']={'asset_id':'img_1','verdict':'FAKE','confidence':None,'evidence_summary':['A prior authenticity report is available.']}
    elif name!='ready':raise ValueError('Unknown state recipe '+name)
    return s
