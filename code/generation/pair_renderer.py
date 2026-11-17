"""Code owns pair roles and operative clauses; no model-authored history is accepted here."""
import copy
OFFER_FRAMES=[
    'I can {action}. Would you like me to?',
    'Would you like me to {action}?',
    'If you want, I can {action}. Shall I?',
    'I can {action} for you. Should I go ahead?',
    'I could {action}. Would you like that?']
CONTINUATIONS={
    'NEW_TARGET_CONTINUATION':['And this one?','Can you do the same for this one?','What about this picture?','Please check this one too.','The same for this picture, please.'],
    'REPEAT_PREVIOUS_OPERATION':['Check it again, please.','Could you repeat that check?','Can you check it once more?','Please repeat the same check.','Would you do that check again?'],
    'ACCEPT_CLEAR_OFFER':['Yes, please do that.','Go ahead with that.','Could you do that now?','Please do what you offered.','Yes, that would help.']}
def current_variant(recipe,index):
    options=CONTINUATIONS[recipe['template_lineage']]
    # For an existing-family extension, ensure a new current-message variant rather than a duplicate.
    choices=[v for v in options if v!=recipe['current_message']]
    return choices[index%len(choices)]
def render_pair(recipe,runtime_state,current_message,context_sentence='',surface_index=0,scene=None):
    if recipe['template_lineage'] not in CONTINUATIONS:raise ValueError('Unknown reviewed recipe type')
    if not isinstance(current_message,str) or not current_message:raise ValueError('Missing code-owned continuation')
    if any(t in context_sentence.lower() for t in ['synthetic fixture','b100_','b500_']):raise ValueError('Scaffolding in user context')
    last=runtime_state['last_analysis'];verdict='recorded' if last is None else last['verdict']
    values={'scene':scene or recipe['scenario'],'verdict':verdict}
    output=[]
    for prefix,label in [('base','BASE'),('deepfake','DEEPFAKE')]:
        user=recipe[prefix+'_user'].format(**values)
        if context_sentence:user=context_sentence.strip()+' '+user
        if recipe['template_lineage']=='ACCEPT_CLEAR_OFFER':
            action=recipe[prefix+'_action_clause'].format(**values)
            assistant=OFFER_FRAMES[surface_index%len(OFFER_FRAMES)].format(action=action)
        else:
            assistant=recipe[prefix+'_assistant'].format(**values)
        state=copy.deepcopy(runtime_state)
        state.update(message=current_message,history=[{'role':'user','content':user},{'role':'assistant','content':assistant}])
        output.append({'label_condition':label,'input':state,'history_source':'code_reviewed_recipe','human_reviewed':False,'accepted_for_training':False})
    a,b=output
    if {k:v for k,v in a['input'].items() if k!='history'}!={k:v for k,v in b['input'].items() if k!='history'}:raise AssertionError('Pair control changed')
    if a['input']['history']==b['input']['history']:raise AssertionError('No context contrast')
    return output
