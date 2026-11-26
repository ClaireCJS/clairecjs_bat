from pathlib import Path
import datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('PAFPlayer.py','releases'),('docs/README.md','docs/backups'),('docs/PAFPlayer_changelog.md','docs/backups')]:
 p=root/raw;original=p.read_bytes();base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');i=0
 while b.exists():i+=1;b=p.with_name(base+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(original).digest()
 target=root/folder/b.name;target.parent.mkdir(parents=True,exist_ok=True)
 while target.exists():i+=1;target=root/folder/(base+f' ({i}).bak')
 b.rename(target)
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf-8-sig')
s=s.replace("= 'V756'","= 'V757'").replace('2026-11-25-v756-speed-confirmation-minor-credit','2026-11-25-v757-smooth-idle-artwork')
s=s.replace('EXTERNAL_ALBUM_ART_IDLE_DRIFT_INTERVAL_MS = 33  # V655: ~30 FPS time-based motion inside the monitor-safe box.', 'EXTERNAL_ALBUM_ART_IDLE_DRIFT_INTERVAL_MS = 1000 / 60  # Deadline-paced motion; speed remains elapsed-time based.')
needle='def external_album_art_music_dance_step('
idx=s.index(needle)
helper='''def external_album_art_next_frame_delay(state, now: float) -> int:
    """Keep a stable 60-Hz deadline and skip missed frames without catch-up bursts."""
    interval = EXTERNAL_ALBUM_ART_IDLE_DRIFT_INTERVAL_MS / 1000.0
    deadline = float(state.get('idle_frame_deadline', now)) + interval
    if deadline <= now:
        deadline += (math.floor((now - deadline) / interval) + 1) * interval
    state['idle_frame_deadline'] = deadline
    return max(1, math.ceil((deadline - now) * 1000.0))


'''
s=s[:idx]+helper+s[idx:]
needle='''            transient = str(state.get("transient_geometry") or "")
            is_programmatic = bool(state.get("programmatic_geometry", False))'''
replacement='''            transient = str(state.get("transient_geometry") or "")
            if (bool(state.get("idle_promoted")) and current_size == previous_size
                    and (bool(state.get("aspect_adjusting")) or geometry == transient)):
                # A dance step changes position, not pixels. Avoid image resampling,
                # border/title work and placement persistence on every Configure.
                state["last_geometry"] = geometry
                return
            is_programmatic = bool(state.get("programmatic_geometry", False))'''
assert s.count(needle)==1;s=s.replace(needle,replacement,1)
# The existing monitor watcher already refreshes this signature on display changes.
needle='''            monitors = external_album_art_monitor_work_areas()
            monitor = external_album_art_idle_monitor_for_rect(origin_outer, monitors)'''
assert s.count(needle)==1;s=s.replace(needle,'''            monitors = state.get("monitor_signature") or external_album_art_monitor_work_areas()
            monitor = external_album_art_idle_monitor_for_rect(origin_outer, monitors)''',1)
needle='''        def idle_art_watch() -> None:'''
helper='''        def schedule_idle_art_frame(frame_started: float) -> None:
            """Schedule from a deadline, and summarize actual pacing every ten seconds."""
            finished = time.monotonic()
            if state.get("idle_promoted"):
                stats = state.get("idle_frame_stats")
                if not stats:
                    stats = {"start": frame_started, "previous": frame_started,
                             "frames": 0, "max_gap": 0.0, "max_work": 0.0}
                    state["idle_frame_stats"] = stats
                stats["frames"] += 1
                stats["max_gap"] = max(stats["max_gap"], frame_started - stats["previous"])
                stats["max_work"] = max(stats["max_work"], finished - frame_started)
                stats["previous"] = frame_started
                elapsed = finished - stats["start"]
                if elapsed >= 10:
                    append_pafplayer_trace("art.idle.pacing", frames=stats["frames"],
                        fps=round(stats["frames"] / elapsed, 1),
                        max_gap_ms=round(stats["max_gap"] * 1000, 2),
                        max_callback_ms=round(stats["max_work"] * 1000, 2),
                        extra_windows=len(state.get("idle_extra_windows") or []))
                    state["idle_frame_stats"] = None
                state.setdefault("idle_frame_deadline", frame_started)
                delay = external_album_art_next_frame_delay(state, finished)
            else:
                state.pop("idle_frame_deadline", None)
                state["idle_frame_stats"] = None
                delay = 100  # Idle detection needs no animation-rate polling.
            root.after(delay, idle_art_watch)

'''
assert s.count(needle)==1;s=s.replace(needle,helper+needle,1)
# Only these two animation-loop reschedules use the old interval.
assert s.count('root.after(EXTERNAL_ALBUM_ART_IDLE_DRIFT_INTERVAL_MS, idle_art_watch)')==2
s=s.replace('root.after(EXTERNAL_ALBUM_ART_IDLE_DRIFT_INTERVAL_MS, idle_art_watch)','schedule_idle_art_frame(now)')
compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'docs/README.md';s=p.read_text(encoding='utf-8-sig');s+='\n\n### V757: idle artwork frame pacing\n\nThe idle artwork dance targets 60 frames per second using monotonic deadlines. Callback work no longer adds a full delay to every frame, and missed frames are skipped rather than replayed in bursts. Position-only dance Configure events reuse the existing artwork instead of resampling the image and scheduling border/title updates. Monitor geometry comes from the existing display watcher. Motion speed and monitor-safe bounds remain time based.\n\nEvery ten seconds while dancing, diagnostic tracing records `art.idle.pacing`: actual FPS, longest callback gap, longest callback duration, and extra-window count. These measurements help distinguish UI stalls from compositor/display issues. Restart the player to load this change; real visual smoothness still needs comparison on the affected display.\n';p.write_text(s,encoding='utf-8')
p=root/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8-sig');s=s.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V757 — November 25, 2026\n\nAvoid artwork re-rendering during position-only dance steps, use 60-Hz deadline scheduling, reuse monitor snapshots, and record aggregated animation pacing diagnostics. [Release notes](../releases/PAFPlayer_v757_smooth_idle_artwork_release_notes.md).\n',1);p.write_text(s,encoding='utf-8')
print('V757 frame-pacing and position-only Configure changes applied with verified backups.')
