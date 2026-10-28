from pafplayer_v456_stage1 import edit
from pafplayer_v416_edit import ROOT,replace_file,sub

def change(s):
    needle='''                    order = playlist_shuffle_order if shuffle_state and shuffle_state[0] and playlist_shuffle_order else (playlist_entries or [])
                    return {"entries":'''
    s=sub(s,needle,'''                    order = list(playlist_shuffle_order if shuffle_state and shuffle_state[0] and playlist_shuffle_order else (playlist_entries or []))
                    # Small-playlist loading skips missing files; keep them visible
                    # for repair without forcing the decoder to open them.
                    from PAFPlayer_web_workflows import missing_playlist_paths
                    present = {removed_runtime_key(Path(x)) for x in order}
                    for raw in missing_playlist_paths(paf_workflows(), playlist_path):
                        key = removed_runtime_key(Path(raw))
                        if key not in present and key not in removed_playlist_track_keys:
                            order.append(Path(raw)); present.add(key)
                    return {"entries":''')
    needle='''        if shuffle_state is None:
            shuffle_state = [False]
        pending_playlist_warning'''
    addition='''        if playlist_path is None:
            single_queue_members = [str(current_audio.resolve())]
            def single_queue_read():
                with playlist_shuffle_lock:
                    return {"entries":list(single_queue_members), "next":[str(x) for x in playlist_manual_next_queue],
                            "current":str(current_audio.resolve()), "playlist":None,
                            "missing":[x for x in single_queue_members if not Path(x).is_file()], "shuffled":False,
                            "reason":"Single-track session; explicit play-next requests take priority"}
            def single_queue_edit(payload):
                from PAFPlayer_web_workflows import calculate_queue_edit, queue_snapshot
                with playlist_shuffle_lock:
                    after = calculate_queue_edit(paf_workflows(), single_queue_read(), payload)
                    if payload.get("op") == "save": return after
                    single_queue_members[:] = after["entries"]
                    playlist_manual_next_queue[:] = [Path(x) for x in after["next"]]
                    if playlist_manual_next_queue and looping_state[0] and web_server is not None:
                        web_server.enqueue_action("web-set:repeat_mode:0")
                    return queue_snapshot(paf_workflows())
            paf_workflows().queue_read = single_queue_read
            paf_workflows().queue_bridge = single_queue_edit

'''
    s=sub(s,needle,addition+needle)
    s=sub(s,'            # Repeat Folder/playlist modes are session play-order modes, not', '''            if playlist_path is None and result in {NEXT_FILE, "completed"}:
                with playlist_shuffle_lock:
                    while playlist_manual_next_queue:
                        next_candidate = playlist_manual_next_queue.pop(0)
                        if next_candidate.is_file():
                            current_audio = next_candidate
                            break
                    else:
                        next_candidate = None
                if next_candidate is not None:
                    continue
            # Repeat Folder/playlist modes are session play-order modes, not''')
    return s
edit(change)
f=ROOT/'PAFPlayer_web_workflows.py'; s=f.read_text(encoding='utf-8')
s=sub(s,'def queue_snapshot(runtime):', '''def missing_playlist_paths(runtime,playlist):
    if not playlist: return []
    try:
        stat=Path(playlist).stat(); signature=(str(playlist),stat.st_size,stat.st_mtime_ns)
        cached=getattr(runtime,'missing_playlist_cache',None)
        if cached and cached[0]==signature: return cached[1]
        _,_,_,rows=playlist_rows(playlist)
        missing=[row['path'] for row in rows if not Path(row['path']).is_file()]
        runtime.missing_playlist_cache=(signature,missing)
        return missing
    except (OSError,ValueError): return []


def queue_snapshot(runtime):''')
s=sub(s,'    with runtime.lock:\n        cleanup_uploads(runtime)', '    cleanup_uploads(runtime)\n    with runtime.upload_lock:')
# Do not take playlist locks while holding the diagnostic/state lock.
replace_file(f,s)
f=ROOT/'PAFPlayer_workflows.py'; s=f.read_text(encoding='utf-8')
s=sub(s,'        self.lock=threading.RLock(); self.token=', '        self.upload_lock=threading.RLock()\n        self.lock=threading.RLock(); self.token=')
replace_file(f,s)
f=ROOT/'PAFPlayer_workflows_ui.py'; s=f.read_text(encoding='utf-8')
s=sub(s,"function source(path){return state?.index?.[path]?.source||''}", "function source(path){return (state?.index?.[path]||state?.index?.[path.replace(/\\//g,'\\\\').toLowerCase()])?.source||''}")
replace_file(f,s)
