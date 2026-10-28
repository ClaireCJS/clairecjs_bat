from pafplayer_v456_stage1 import edit
from pafplayer_v416_edit import sub

def change(s):
    s=sub(s,'GLOBAL_CONFIG_DEVELOPER_MACHINES = frozenset({"demona", "wyvern", "thailog", "goliath"})', 'from PAFPlayer_workflows import TRUSTED_MACHINES\nGLOBAL_CONFIG_DEVELOPER_MACHINES = frozenset(TRUSTED_MACHINES)')
    # Opt-in runtime is shared by CLI, HTTP and playlist callbacks.
    marker='class PAFWebServer:'
    s=sub(s,marker,'''def paf_workflows():
    from PAFPlayer_workflows import get_runtime
    return get_runtime(sys.modules[__name__])


'''+marker)
    s=sub(s,'        self._playlist_snapshot_callback = None', '        self.workflows = paf_workflows()\n        self.workflows.server = self\n        self._playlist_snapshot_callback = None')
    s=sub(s,'            def do_GET(self):\n', '''            def do_GET(self):
                from PAFPlayer_web_workflows import handle
                if handle(self, owner, self.path.partition("?")[0]): return
''')
    s=sub(s,'            def do_POST(self):\n', '''            def do_POST(self):
                from PAFPlayer_web_workflows import handle
                if handle(self, owner, self.path.partition("?")[0]): return
''')
    s=sub(s,'    arguments = list(sys.argv[1:] if argv is None else argv)\n', '''    arguments = list(sys.argv[1:] if argv is None else argv)
    from PAFPlayer_cli_workflows import dispatch
    workflow_result, arguments = dispatch(paf_workflows(), arguments)
    if workflow_result is not None: return workflow_result
''')
    s=sub(s,'    atexit.register(finish_pafplayer_diagnostic_session)', '    atexit.register(finish_pafplayer_diagnostic_session)\n    atexit.register(paf_workflows().close)')
    needle='            if web_server is not None:\n                web_server.set_playlist_bridge(\n'
    addition='''            def workflow_queue_read():
                with playlist_shuffle_lock:
                    order = playlist_shuffle_order if shuffle_state and shuffle_state[0] and playlist_shuffle_order else (playlist_entries or [])
                    return {"entries": [str(x) for x in order], "next": [str(x) for x in playlist_manual_next_queue],
                            "current": str(current_audio) if current_audio else None, "playlist": str(playlist_path),
                            "reason": "Explicit play-next requests take priority; otherwise " + ("uniform random selection" if shuffle_mode_state[0] == 2 else "least-recent/history-biased shuffled order" if shuffle_state and shuffle_state[0] else "playlist order")}

            def workflow_queue_edit(payload):
                nonlocal playlist_entries, playlist_shuffle_order
                from PAFPlayer_web_workflows import calculate_queue_edit, queue_snapshot
                runtime = paf_workflows()
                with playlist_shuffle_lock:
                    if playlist_rebuild_active.is_set() or (playlist_ready_event is not None and not playlist_ready_event.is_set()):
                        raise ValueError("CONFLICT: playlist is rebuilding; retry after it finishes")
                    before = workflow_queue_read()
                    after = calculate_queue_edit(runtime, before, payload)
                    if payload.get("op") == "save": return after
                    removed = set(before["entries"]) - set(after["entries"])
                    for raw in removed:
                        removed_playlist_track_keys.add(removed_runtime_key(Path(raw)))
                        runtime_added_playlist_tracks.pop(removed_runtime_key(Path(raw)), None)
                    for raw in after["entries"]:
                        candidate = Path(raw); key = removed_runtime_key(candidate)
                        removed_playlist_track_keys.discard(key)
                        runtime_added_playlist_tracks[key] = candidate
                    playlist_entries = [Path(x) for x in after["entries"]]
                    playlist_shuffle_order = list(playlist_entries)
                    playlist_manual_next_queue[:] = [Path(x) for x in after["next"]]
                    playlist_track_count_state[0] = len(playlist_entries)
                    return queue_snapshot(runtime)

            paf_workflows().queue_read = workflow_queue_read
            paf_workflows().queue_bridge = workflow_queue_edit

'''
    s=sub(s,needle,addition+needle)
    # Mirror normal diagnostics into the bounded redacted web ring.
    s=sub(s,'    clean = str(message or "").rstrip("\\r\\n") or "(empty diagnostic message)"', '''    clean = str(message or "").rstrip("\\r\\n") or "(empty diagnostic message)"
    try:
        from PAFPlayer_workflows import _runtimes, redact
        workflow = _runtimes.get(id(sys.modules[__name__]))
        if workflow is not None:
            with workflow.lock:
                workflow.sequence += 1
                workflow.events.append({"id": workflow.sequence, "time": time.time(), "level": str(level).upper(),
                    "category": clean.split()[0].split(".")[0], "message": redact(clean)})
    except Exception:
        pass''')
    s=sub(s,'        usage_line("--version / --which-script", "show build ID and exact script path")', '''        usage_line("--version / --which-script", "show build ID and exact script path")
        usage_line("--workflow-help", "folder monitor, repair, render-book and CUDA experiment options")''')
    return s

if __name__=='__main__': edit(change)
