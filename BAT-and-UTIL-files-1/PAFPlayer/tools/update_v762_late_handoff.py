from pathlib import Path
import datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('PAFPlayer.py','releases'),('docs/README.md','docs/backups'),('docs/PAFPlayer_changelog.md','docs/backups')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("= 'V761'","= 'V762'").replace('2026-11-26-v761-faster-preview-startup','2026-11-26-v762-late-preview-handoff')
needle='''        if playback_focus is not None:
            playback_focus.claim()
        while True:
            speed = current_speed()'''
new='''        def claim_ready_preview() -> None:
            nonlocal startup_pause_pending, header_paused
            playback_focus.claim()
            if simple_mode and paused_state is not None:
                # A newer preview may have held this silent startup. Re-read
                # the state after waiting, rather than replaying an old pause latch.
                startup_pause_pending = bool(paused_state[0])
                header_paused = startup_pause_pending
                prompt_paused_state[0] = startup_pause_pending

        if playback_focus is not None:
            if simple_mode:
                playback_focus.start()  # Discoverable while preparing, without pausing peers.
            else:
                playback_focus.claim()
        while True:
            speed = current_speed()'''
assert s.count(needle)==1;s=s.replace(needle,new,1)
needle='''            if buffered_waveout_active and process is None:
                try:'''
new='''            preview_preroll = bool(simple_mode and playback_focus is not None and not playback_focus.claimed)
            if buffered_waveout_active and process is None:
                try:'''
assert s.count(needle)==1;s=s.replace(needle,new,1)
# Restrict replacement to this initial renderer branch, not prepared successor/seek launches.
start=s.index('            preview_preroll = bool(');end=s.index('            if process is None:\n                command = ffplay_command(',start)
block=s[start:end]
needle='''                        input_url=(memory_source.url if memory_source is not None and not early_eof_force_file else None),
                    )
                    append_pafplayer_trace('''
new='''                        input_url=(memory_source.url if memory_source is not None and not early_eof_force_file else None),
                        hold_for_handoff=preview_preroll,
                    )
                    if preview_preroll and not process.wait_primed():
                        raise RuntimeError("Preview audio did not finish silent preparation")
                    append_pafplayer_trace('''
assert needle in block;block=block.replace(needle,new,1)
needle='''                except Exception as exc:
                    record_pafplayer_runtime_warning('''
new='''                except Exception as exc:
                    if process is not None:
                        hard_stop_process(process)
                    record_pafplayer_runtime_warning('''
assert needle in block;block=block.replace(needle,new,1)
block+='''            if process is not None and preview_preroll:
                try:
                    append_pafplayer_trace("preview.output.primed", track=audio_path)
                    claim_ready_preview()
                    if not process.start_output():
                        raise RuntimeError("Prepared preview audio could not start")
                    append_pafplayer_trace("preview.output.started", track=audio_path)
                except BaseException:
                    hard_stop_process(process)
                    raise
'''
s=s[:start]+block+s[end:]
needle='''                process = process_factory(command, **process_kwargs)
'''
assert s.count(needle)==1;s=s.replace(needle,'''                if playback_focus is not None:
                    claim_ready_preview()
                process = process_factory(command, **process_kwargs)
''',1)
needle='''            web_server.enqueue_action, preview=simple_instance, pause=WEB_PAUSE, resume=WEB_PLAY, trace=append_pafplayer_trace, guarded=True)
'''
assert s.count(needle)==1;s=s.replace(needle,needle+'''        if simple_instance:
            playback_focus.start()  # Register early; acquire audio focus only when output is ready.
''',1)
compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'docs/README.md';s=p.read_text(encoding='utf-8-sig');s+='\n\n### V762: pause peers only when preview audio is ready\n\nSimple previews register for coordination during setup but leave the other players playing. The buffered audio renderer loads and primes silently first; only then does the preview acquire pause acknowledgements and release its prepared output. If preparation fails, the fallback pauses peers immediately before launching FFplay. Failed silent preparation never acquires focus. Existing focus ownership and previously paused-player protections remain in effect.\n';p.write_text(s,encoding='utf-8')
p=root/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8-sig');s=s.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V762 — November 26, 2026\n\nPrime preview audio silently before pausing peers, then acquire focus immediately before releasing output; delay FFplay fallback focus until process launch. [Release notes](../releases/PAFPlayer_v762_late_preview_handoff_release_notes.md).\n',1);p.write_text(s,encoding='utf-8')
print('V762 late preview handoff applied; originals backed up and verified.')
