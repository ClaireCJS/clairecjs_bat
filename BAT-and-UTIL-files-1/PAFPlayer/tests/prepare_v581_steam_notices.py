"""Apply V581 with verified replacement backups; run once from the project checkout."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'monkeymote/research'))
from edit_v568 import write


def replace_once(text, before, after):
    assert text.count(before) == 1, (before[:120], text.count(before))
    return text.replace(before, after, 1)


source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
assert "PROGRAM_VERSION                = 'V580'" in source
steam = (ROOT / 'PAFPlayer_steam.py.bak.202610200649.replaced-by-chatgpt.bak').read_text(encoding='utf-8')
steam = replace_once(steam, "DEFAULTS = {REDUCE: 1, NO_GALLERY: 1}",
                     "DEFAULTS = {REDUCE: 1, NO_GALLERY: 1}\nNOTICE_SECONDS = 10.0")
steam = replace_once(steam, 'class Monitor:', r'''def activity_message(active, games, options, *, compact=False):
    # Metadata must never introduce terminal controls or extra HUD rows.
    name = re.sub(r'[\\x00-\\x1f\\x7f-\\x9f\\u2028\\u2029]', ' ', ', '.join(games))
    name = ' '.join(name.split())
    limit = 28 if compact else 160
    if len(name) > limit:
        name = name[:limit - 1] + '…'
    visualizer = '50%' if active and options[REDUCE] else 'normal'
    gallery = 'blocked' if active and options[NO_GALLERY] else 'allowed'
    return (f"🎮 Steam {'started' if active else 'stopped'}: {name}"
            f" · Visualizer {visualizer} · Idle gallery {gallery}")


class Monitor:''')
steam = replace_once(steam, 'inventory=catalog):', 'inventory=catalog, clock=None):')
steam = replace_once(steam, "        self.stop = threading.Event()", """        self.clock = clock or time.monotonic
        self._last_games = ()
        self._notice = None
        self._notice_serial = 0
        self.stop = threading.Event()""")
steam = steam.replace('time.monotonic()', 'self.clock()')  # All current calls belong to Monitor.
steam = replace_once(steam, """            self._state = (self.clock(), (), 'Steam checks disabled')
            return""", """            self._notice = None
            self._last_games = ()
            self._state = (self.clock(), (), 'Steam checks disabled')
            return""")
steam = replace_once(steam, """        self._state = (self.clock(), games, 'Steam game running' if games else 'No running Steam game detected')""", """        now = self.clock()
        self._state = (now, games, 'Steam game running' if games else 'No running Steam game detected')
        if bool(games) != bool(self._last_games):
            self._notice_serial += 1
            self._notice = {
                'id': self._notice_serial, 'until': now + NOTICE_SECONDS,
                'active': bool(games), 'games': games or self._last_games,
            }
        self._last_games = games
        self._refresh_notice_text()

    def _refresh_notice_text(self):
        notice = self._notice
        if notice:
            self._notice = dict(
                notice,
                message=activity_message(notice['active'], notice['games'], self._options),
                hud=activity_message(notice['active'], notice['games'], self._options, compact=True),
            )

    def _current_notice(self):
        # Hot-path cache reads only. Failure/staleness is not a game exit.
        notice = self._notice
        now = self.clock()
        if notice and now < notice['until'] and now - self._state[0] < 8.0:
            return notice
        return None

    def hud_notice(self):
        notice = self._current_notice()
        return notice['hud'] if notice else ''

    def notice(self):
        notice = self._current_notice()
        if not notice:
            return {}
        return {'id': notice['id'], 'message': notice['message'],
                'remaining_ms': max(0, (notice['until'] - self.clock()) * 1000)}""")
steam = replace_once(steam, """            except Exception as exc:
                self._state""", """            except Exception as exc:
                self._notice = None
                self._state""")
steam = replace_once(steam, """'status': self._state[2]}""",
                     """'status': self._state[2], 'notice': self.notice()}""")
steam = replace_once(steam, """            self._options = dict(self._options, **payload)
        return self.status()""", """            self._options = dict(self._options, **payload)
            if not any(self._options.values()):
                self._notice = None
            else:
                self._refresh_notice_text()
        return self.status()""")
# Keep the existing config poll. No new HTTP polling or player command is needed.
steam = replace_once(steam, """let busy=false,token='';""", """let busy=false,token='',requestSerial=0;
const notice=document.getElementById('steamPlaybackNotice');
let noticeId=0,noticeDeadline=0,noticeTimer=0;
function hideNotice(){clearTimeout(noticeTimer);notice.hidden=true;notice.textContent=''}
function showNotice(value,requestAge){
 const id=Number(value?.id||0),remaining=Math.max(0,Math.min(10000,Number(value?.remaining_ms||0))-requestAge);
 if(!id||!value.message||!Number.isFinite(remaining)||remaining<=0){hideNotice();return}
 if(id<noticeId)return;
 const deadline=performance.now()+remaining;
 if(id!==noticeId){noticeId=id;noticeDeadline=deadline}else{noticeDeadline=Math.min(noticeDeadline,deadline)}
 clearTimeout(noticeTimer);
 if(noticeDeadline<=performance.now()){hideNotice();return}
 notice.textContent=value.message;notice.hidden=false;
 noticeTimer=setTimeout(hideNotice,noticeDeadline-performance.now());
}
document.addEventListener('visibilitychange',()=>{if(!document.hidden){if(performance.now()>=noticeDeadline)hideNotice();refresh()}});""")
steam = replace_once(steam, "function show(data){", "function show(data,requestAge=0){showNotice(data.notice,requestAge);")
steam = replace_once(steam, """async function refresh(){if(busy)return;try{show(await request())}catch(e){status.textContent=String(e)}}""", """async function refresh(){if(busy)return;const serial=++requestSerial,started=performance.now();try{const data=await request();if(serial===requestSerial)show(data,performance.now()-started)}catch(e){if(serial===requestSerial)status.textContent=String(e)}}""")
steam = replace_once(steam, "async function change(key,control){busy=true;", "async function change(key,control){busy=true;++requestSerial;")
steam = replace_once(steam, """    return page.replace(anchor, html + anchor, 1).replace('</body>', script + '</body>', 1)""", """    title = '<h1 id="songTitle">Waiting for playback…</h1>'
    notice = '<div id="steamPlaybackNotice" role="status" aria-live="polite" hidden style="color:#8ddcff;font-size:0.95rem;margin:0.35rem 0 0.65rem;overflow-wrap:anywhere"></div>'
    return page.replace(title, title + notice, 1).replace(anchor, html + anchor, 1).replace('</body>', script + '</body>', 1)""")
write('PAFPlayer_steam.py', steam)

source = replace_once(source, """    steam_monitor = get_monitor(sys.modules[__name__])""", """    steam_monitor = get_monitor(sys.modules[__name__])
    last_steam_notice = ''""")
source = replace_once(source, """        transient_prefix = (transient + "  ") if transient else ""
""", """        transient_prefix = (transient + "  ") if transient else ""
        steam_notice = steam_monitor.hud_notice()
        steam_prefix = ("\\033[1;38;2;120;225;255m" + steam_notice + "\\033[0m  ") if steam_notice else ''
""")
source = replace_once(source, 'bake_prompt + transient_prefix + speed_fade_notice',
                     'bake_prompt + transient_prefix + steam_prefix + speed_fade_notice')
source = replace_once(source, 'if performance_stats_overlay_enabled and not exclusive_lines and not transient:',
                     'if performance_stats_overlay_enabled and not exclusive_lines and not transient and not steam_notice:')
source = replace_once(source, '    def color_catalog_swatch_line(', '''    def refresh_steam_notice(position_value: float) -> None:
        """Repaint on start/stop/expiry even while paused or with the FPS HUD off."""
        nonlocal last_steam_notice
        notice = steam_monitor.hud_notice()
        if notice != last_steam_notice and not help_overlay_until and not favorite_menu_active and not default_menu_active:
            last_steam_notice = notice
            render_controls(playback_fraction(position_value))

    def color_catalog_swatch_line(''')
source = replace_once(source, '                notice_signature = (',
                     '                refresh_steam_notice(displayed_position)\n                notice_signature = (')
source = replace_once(source, """                        paused_now = monotonic()
                        current_volume_blink_phase""", """                        paused_now = monotonic()
                        refresh_steam_notice(position)
                        current_volume_blink_phase""")
source = replace_once(source, "'2026-10-19-v580-remote-tray-options-and-steam-aware-visuals'",
                     "'2026-10-20-v581-steam-activity-notices'")
source = replace_once(source, "PROGRAM_VERSION                = 'V580'", "PROGRAM_VERSION                = 'V581'")
source = replace_once(source, "PROGRAM_RELEASE_LABEL          = 'V580'", "PROGRAM_RELEASE_LABEL          = 'V581'")
namespace = {'__name__': 'bundle_sync'}
sync_source = (ROOT / 'monkeymote/research/sync_v568_bundle.py').read_text(encoding='utf-8')
sync_source = sync_source.replace("('PAFPlayer_monkeymote', 'PAFPlayer_workflows_ui', 'PAFPlayer_web_workflows')", "('PAFPlayer_steam',)")
exec(compile(sync_source, '<bundle-sync>', 'exec'), namespace)
source = namespace['sync'](source)
compile(source, 'PAFPlayer.py', 'exec')
write('PAFPlayer.py', source)

doc = (ROOT / 'docs/steam.md').read_text(encoding='utf-8')
doc = replace_once(doc, '# Steam-aware visual load (V580)', '# Steam-aware visual load and activity notices (V581)')
doc = replace_once(doc, '## Detection and limits', '''## Start and stop notices

The console HUD and the web player directly below the song title show a
**10-second notice** when Steam detection changes from no running game to a
running game, and when the last running game exits. For example:

- `🎮 Steam started: RACCOIN · Visualizer 50% · Idle gallery blocked`
- `🎮 Steam stopped: RACCOIN · Visualizer normal · Idle gallery allowed`

The notice names the game and reports the effect of the two current checkboxes.
“Normal” and “allowed” mean Steam is no longer imposing that restriction;
other player settings still apply. An already-running game is announced when
the monitor first detects it. Repeated scans and song changes do not restart
the timer. One game's exit does not announce a stop while another remains.
HUD expiry also works during paused playback and with the FPS display off;
help screens, test-tone controls, and exclusive warnings retain priority.

Both views use the same ten-second detection window. The existing web config
poll can make the web notice arrive up to three seconds later; it shows the
remaining window and expires even if the server disconnects. Browser clock
differences do not affect expiry. Config → Steam keeps the current status
after the notice disappears. Failed/stale scans do not invent a game-stop
notice. With both Steam controls disabled, detection and notices are disabled.

## Detection and limits''')
doc = doc.replace('Run V580 as the official player', 'Run V581 as the official player')
doc += '''
6. Launch a game while watching the console HUD and the web song title. Confirm
   the start notice disappears ten seconds after detection, without restarting
   on repeated polls or a song change. The Steam config section stays current.
7. Pause music, disable the FPS HUD, then exit the last game. Confirm the stop
   notice appears and clears ten seconds later without needing a key press.
8. Repeat with one Steam checkbox disabled; confirm the notice describes the
   actual enabled restriction. Check that a help screen or warning still wins.
'''
write('docs/steam.md', doc)
changelog = (ROOT / 'PAFPlayer_changelog.md').read_text(encoding='utf-8')
changelog = replace_once(changelog, '# PAFPlayer changelog\n', '''# PAFPlayer changelog

## V581 — October 20, 2026

Show ten-second Steam game start/stop notices in the console HUD and directly
below the web song title. Include the game name and the current visualizer and
idle-gallery effects. Keep notices across track changes, expire them while
paused, and avoid resetting them on routine detection or web polls. Failed scans
do not masquerade as a game exit. Reuse the existing web poll and cached monitor;
audio, command routing, configuration IDs, and Steam defaults are unchanged.
[Release notes](releases/PAFPlayer_v581_steam_activity_notices_release_notes.md).
''')
write('PAFPlayer_changelog.md', changelog)
manual = (ROOT / 'PAFPlayer.md').read_text(encoding='utf-8')
manual = replace_once(manual, '## Current source — V580', '''## Current source — V581

- Ten-second Steam start/stop notices appear in the console HUD and below the
  web song title, including the game name, visualizer reduction, and idle-gallery
  restriction. They expire during paused playback and do not repeat every scan.
- [Steam configuration and manual checks](docs/steam.md).
- [V581 release notes](releases/PAFPlayer_v581_steam_activity_notices_release_notes.md).

## Previous release — V580''')
manual = manual.replace('## Previous release — V579', '## Earlier release — V579', 1)
write('PAFPlayer.md', manual)
index = (ROOT / 'docs/README.md').read_text(encoding='utf-8')
index = replace_once(index, 'Current release: **V580** — Steam-aware visual load, remote artwork lyrics and unified tray options.',
                     'Current release: **V581** — ten-second Steam start/stop notices in the HUD and below the web song title.\n\n- [V581 release notes](../releases/PAFPlayer_v581_steam_activity_notices_release_notes.md)')
write('docs/README.md', index)
