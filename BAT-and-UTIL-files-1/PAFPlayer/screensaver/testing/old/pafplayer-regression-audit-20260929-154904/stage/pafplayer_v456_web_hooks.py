from pafplayer_v456_stage1 import edit
from pafplayer_v416_edit import ROOT,replace_file,sub

def change(s):
    s=sub(s,'</body></html>"""\n    return (','</body></html>"""\n    from PAFPlayer_workflows_ui import augment\n    html = augment(html)\n    return (')
    s=sub(s,"['globalConfigSection','Global Config']", "['workflowSecuritySection','Security'],['workflowRepairSection','Repair'],['workflowMonitorSection','Monitoring'],['workflowLogsSection','Logs'],['workflowDiscordSection','Discord'],['globalConfigSection','Global Config']")
    s=sub(s,'"current": str(current_audio) if current_audio else None, "playlist": str(playlist_path),', '''"current": str(current_audio) if current_audio else None, "playlist": str(playlist_path),
                            "missing": [str(x) for x in order if not Path(x).is_file()],
                            "shuffled": bool(shuffle_state and shuffle_state[0]),''')
    s=sub(s,'                nonlocal playlist_entries, playlist_shuffle_order\n                from PAFPlayer_web_workflows', '                nonlocal playlist_entries, playlist_shuffle_order\n                from PAFPlayer_web_workflows')
    return s
edit(change)
f=ROOT/'PAFPlayer_web_workflows.py'; s=f.read_text(encoding='utf-8')
s=sub(s,"    result=dict(state,entries=entries,next=next_up)", "    result=dict(state,entries=entries,next=next_up)\n    if 'missing' in result: result['missing']=[x for x in entries if not Path(x).is_file()]")
s=sub(s,"        elif operation=='repair-preview':", '''        elif operation=='library':
            search=str(payload.get('search','')).casefold().strip()
            if not search: raise ValueError('Enter a library filename search')
            matches=[{'path':v['path'],'filename':Path(v['path']).name} for v in runtime.index.values()
                     if search in Path(v.get('path','')).name.casefold() and Path(v.get('path','')).is_file()][:200]
            if payload.get('preview'): data={'items':matches}
            else:
                allowed={x['path'] for x in matches}; approved=payload.get('approved',[])
                if not approved or any(x not in allowed for x in approved): raise ValueError('Library selection changed; preview again')
                data=edit_queue(runtime,{'op':'add','paths':approved,'revision':queue_snapshot(runtime)['revision']})
        elif operation=='repair-preview':''')
s=sub(s,"    dry=bool(payload.get('dry_run',True)); result={'changes':chosen,'dry_run':dry}", '''    dry=bool(payload.get('dry_run',True)); result={'changes':chosen,'dry_run':dry}
    if not payload.get('playlist_only') and not dry and chosen:
        if queue_snapshot(runtime)['revision']!=preview['queue_revision']:
            raise ValueError('CONFLICT: queue changed; preview repairs again before writing anything')''')
replace_file(f,s)
f=ROOT/'PAFPlayer_render_book.py';s=f.read_text(encoding='utf-8').replace('min(255,level)/255*130','min(app.SPECTRUM_ANALYSIS_HEIGHT,level)/max(1,app.SPECTRUM_ANALYSIS_HEIGHT)*130');replace_file(f,s)
