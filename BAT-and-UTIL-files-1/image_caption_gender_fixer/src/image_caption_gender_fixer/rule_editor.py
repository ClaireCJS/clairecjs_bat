"""Shared review rule ordering model and console editor; folder persistence is atomic."""
from dataclasses import asdict,replace
import json
import os
import uuid
from .rules import Rule,reject_cycles
from .errors import IntegrityError
from .presentation import color,GREEN,YELLOW,CYAN

def ordered(rules):return sorted(rules,key=lambda r:(-r.priority,r.order,r.id))

def move_rule(rules,index,offset):
    result=list(rules);target=max(0,min(len(result)-1,index+offset))
    rule=result.pop(index);result.insert(target,rule)
    if len(result)>64:raise IntegrityError('Reordering supports at most 64 rules; use shared priorities for a larger list.')
    highest=max(100,len(result)*10)
    return [replace(r,priority=highest-i*10) for i,r in enumerate(result)],target

def new_rule(before,after,priority,profile):
    rule=Rule(before,after,int(priority),str(uuid.uuid4()),scope='folder',profile=profile,user=True,order=10000)
    rule.validate();return rule

def validate_payload(payload,rules,profile):
    """Never trust GUI data as approval or arbitrary paths/rule definitions."""
    rule=new_rule(payload['before'],payload['after'],payload['priority'],profile)
    result=ordered([*rules,rule]);requested=payload.get('order')
    if requested is not None:
        # GUI identifies its new rule with a stable placeholder, not a UUID.
        byid={r.id:r for r in rules};byid['new']=rule
        if len(requested)!=len(byid) or set(requested)!=set(byid):raise IntegrityError('Rule list changed; reopen the rule editor.')
        highest=max(100,len(requested)*10)
        result=[replace(byid[key],priority=highest-i*10) for i,key in enumerate(requested)]
        rule=next(r for r in result if r.id==rule.id)
    reject_cycles(result)
    if len({r.priority for r in result if r.enabled})>64:raise IntegrityError('More than 64 priority levels.')
    return result,rule

def console_editor(app,rules):
    before=app.question('Source phrase (blank cancels): ')
    if not before:return None
    after=app.question('Replacement phrase: ')
    while True:
        try: priority=int(app.question('Priority: ','10'));break
        except ValueError:app.diagnostics('Use an integer priority.')
    payload={'before':before,'after':after,'priority':priority}
    result,rule=validate_payload(payload,rules,app.args.profile);index=next(i for i,r in enumerate(result) if r.id==rule.id);moved=False
    while True:
        app.diagnostics('\n'+ '\n'.join(('➜ ' if i==index else '  ')+str(r.priority)+': '+color(json.dumps(r.before,ensure_ascii=False),GREEN)+' ➜ '+color(json.dumps(r.after,ensure_ascii=False),YELLOW) for i,r in enumerate(result)))
        app.diagnostics(color('↑/↓ move selected rule; PgUp/PgDn move five; ENTER=save; Esc=cancel',CYAN))
        if os.name=='nt' and app.ask_callback is None:
            import msvcrt
            key=msvcrt.getwch()
            if key in ('\x00','\xe0'):key={'H':'up','P':'down','I':'pgup','Q':'pgdn'}.get(msvcrt.getwch(),'')
            if key=='\r':key='save'
            if key=='\x1b':key='cancel'
            if key=='\x03':raise KeyboardInterrupt
        else:key=app.question('up/down/pgup/pgdn/save/cancel: ','save').lower()
        if key in ('cancel','c'):return None
        if key in ('save','s'):
            if moved:payload['order']=['new' if r.id==rule.id else r.id for r in result]
            return payload
        offsets={'up':-1,'down':1,'pgup':-5,'pgdn':5}
        if key in offsets:result,index=move_rule(result,index,offsets[key]);moved=True
