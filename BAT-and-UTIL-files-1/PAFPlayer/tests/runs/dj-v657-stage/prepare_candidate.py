from pathlib import Path
import ast
root=Path(__file__).resolve().parents[3]; here=Path(__file__).parent
player=(root/'PAFPlayer.py').read_text(encoding='utf8')
web=(root/'src/PAFPlayer_web_workflows.py').read_text(encoding='utf8')
workflow=(root/'src/PAFPlayer_workflows.py').read_text(encoding='utf8')
dj=(here/'PAFPlayer_dj_candidate.py').read_text(encoding='utf8')
def change(src,old,new):
 assert src.count(old)==1,(old[:100],src.count(old));return src.replace(old,new,1)
web=change(web,"            elif operation=='steam':\n", "            elif operation=='dj':\n                from PAFPlayer_dj import get_controller\n                data=dict(get_controller(runtime).status(),local=local,token=runtime.token if local else None)\n            elif operation=='steam':\n")
web=change(web,"        elif operation=='steam':\n", "        elif operation=='dj':\n            if not local: raise PermissionError('Change AI DJ settings on the player computer')\n            from PAFPlayer_dj import get_controller\n            changed=payload.pop('changed',None)\n            data={'settings':get_controller(runtime).configure(payload,changed)}\n        elif operation=='steam':\n")
workflow=change(workflow,'        self.stop_event.set()\n        if getattr(self,\'discord\',None):',"        self.stop_event.set()\n        if getattr(self,'ai_dj_controller',None): self.ai_dj_controller.close()\n        if getattr(self,'discord',None):")
player=change(player,"PROGRAM_VERSION                = 'V656'","PROGRAM_VERSION                = 'V657'")
player=change(player,"PROGRAM_RELEASE_LABEL          = 'V656'","PROGRAM_RELEASE_LABEL          = 'V657'")
player=change(player,'class _PAFBundledFinder(',"_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n\nclass _PAFBundledFinder(')
for name,content in [('PAFPlayer_workflows',workflow),('PAFPlayer_web_workflows',web)]:
 tree=ast.parse(player);found=None
 for node in tree.body:
  if not isinstance(node,ast.Assign):continue
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES' and isinstance(node.value,ast.Dict):
    for k,v in zip(node.value.keys,node.value.values):
     if ast.literal_eval(k)==name:found=v
   if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(target.slice)==name:found=node.value
 assert found and found.lineno==found.end_lineno
 lines=player.splitlines(keepends=True);line=lines[found.lineno-1].encode('utf8');lines[found.lineno-1]=(line[:found.col_offset]+repr(content).encode('utf8')+line[found.end_col_offset:]).decode('utf8');player=''.join(lines)
player=change(player,'    audio_tags = dict(prepared_track.audio_tags) if prepared_valid else probe_audio_tags(audio_path)\n', '''    audio_tags = dict(prepared_track.audio_tags) if prepared_valid else probe_audio_tags(audio_path)
    from PAFPlayer_dj import get_controller as _get_dj_controller
    dj_controller = _get_dj_controller(paf_workflows())
    dj_owned_pause = False
    dj_message = ['', '', '']
''')
player=change(player,'''        if local_eligible and local_log_state[0] is not True:
            record_local_history_if_eligible(merged, force=full_play_completion)
''','''        dj_controller.track_changed()
        if local_eligible or full_play_completion:
            dj_controller.record(audio_tags.get('Artist', ''), audio_tags.get('Song', '') or audio_path.stem)
        if local_eligible and local_log_state[0] is not True:
            record_local_history_if_eligible(merged, force=full_play_completion)
''')
player=change(player,'''                    set_transient_notice("Unknown command: #" + command, seconds=3.0)
                    return None
''','''                    if command == 'dj':
                        value = dj_controller.configure({'enabled': not dj_controller.options['enabled']})
                        set_transient_notice('AI DJ ' + ('enabled' if value['enabled'] else 'disabled'), seconds=3.0)
                    elif command == 'djforce':
                        if dj_controller.start(True): set_transient_notice('AI DJ: preparing or ready', seconds=3.0)
                        else: set_transient_error(dj_controller.error, seconds=4.0)
                    else:
                        set_transient_notice("Unknown command: #" + command, seconds=3.0)
                    return None
''')
player=change(player,'''            while True:
                if pending_actions:
''','''            while True:
                # Only forced jobs expose stage-based progress in the HUD.
                with dj_controller.lock:
                    message = [dj_controller.error, dj_controller.notice,
                               dj_controller.stage if dj_controller.forced else '']
                if message != dj_message:
                    if message[0] and message[0] != dj_message[0]: set_transient_error(message[0], seconds=6.0)
                    elif message[1] and message[1] != dj_message[1]: set_transient_notice(message[1], seconds=6.0)
                    elif message[2] and message[2] != dj_message[2]: set_transient_notice('AI DJ: ' + message[2], seconds=3.0)
                    dj_message[:] = message
                if pending_actions:
''')
player=change(player,'''                if action == EXTERNAL_MEDIA_PAUSE:
                    snapshot = external_media_controller.last_snapshot
''','''                if action is None and not startup_pause_transition and dj_controller.due():
                    dj_owned_pause = True
                    action = PAUSE_TOGGLE
                if action == EXTERNAL_MEDIA_PAUSE:
                    snapshot = external_media_controller.last_snapshot
''')
player=change(player,'''                    show_status(position, "⏹️" if header_stopped else "⏸️")
                    while True:
''','''                    show_status(position, "⏹️" if header_stopped else "⏸️")
                    dj_started = False
                    if dj_owned_pause:
                        dj_files = dj_controller.take()
                        if dj_files: dj_started = dj_controller.play(dj_files, player)
                        if not dj_started: dj_owned_pause = False
                    while True:
''')
player=change(player,'''                        previous_pause_reason = external_media_controller.pause_reason
                        paused_action = external_media_controller.filter_action(paused_action, True, paused_now)
''','''                        if paused_action in ({STOP, QUIT_Q, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP} | NAVIGATION_ACTIONS) or (paused_action is not None and seek_seconds_for_action(paused_action) is not None):
                            dj_controller.cancel_request()
                            dj_owned_pause = False
                            dj_started = False
                        if paused_action is None and not dj_started and dj_controller.forced and dj_controller.due():
                            dj_files = dj_controller.take()
                            if dj_files: dj_started = dj_controller.play(dj_files, player)
                        if paused_action is None and dj_started and dj_controller.play_done:
                            dj_started = False
                            if dj_owned_pause:
                                dj_owned_pause = False
                                paused_action = PAUSE_TOGGLE
                        previous_pause_reason = external_media_controller.pause_reason
                        paused_action = external_media_controller.filter_action(paused_action, True, paused_now)
                        if dj_started and paused_action == EXTERNAL_MEDIA_RESUME:
                            paused_action = None
''')
player=change(player,'''    finally:
        # The analyzer's gate must be released on every exit path, not
''','''    finally:
        dj_controller.cancel_playback()
        # The analyzer's gate must be released on every exit path, not
''')
for path,content in [(here/'PAFPlayer_candidate.py',player),(here/'PAFPlayer_web_workflows_candidate.py',web),(here/'PAFPlayer_workflows_candidate.py',workflow)]:
 compile(content,str(path),'exec')
 with path.open('x',encoding='utf8',newline='\n') as f:f.write(content)
 print('staged',path)
