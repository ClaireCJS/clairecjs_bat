"""Transition, paused-HUD and browser timer checks without real games or settings writes."""
import ast
import copy
import inspect
import json
from pathlib import Path
import re
import shutil
import subprocess
from types import SimpleNamespace as NS
import unittest
from unittest import mock

import PAFPlayer as app
import PAFPlayer_steam as steam


class SteamNoticeTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.saved = {}
        self.ids = []
        self.owner = NS(load_player_settings=lambda: self.saved.copy(),
                        save_player_settings=lambda value: self.saved.update(value))
        self.monitor = steam.Monitor(
            self.owner, clock=lambda: self.now,
            processes=lambda: [{'name': 'steam.exe', 'exe': r'C:\Steam\steam.exe'}],
            registry=lambda: ([], self.ids),
            inventory=lambda roots: {'42': {'name': 'Game One', 'directory': r'C:\Games\One'},
                                     '43': {'name': 'Game Two', 'directory': r'C:\Games\Two'}})

    def scan(self, at, ids=None):
        self.now = at
        if ids is not None:
            self.ids = ids
        self.monitor.tick()
        return self.monitor.status()['notice']

    def test_no_startup_stop_and_start_notice_for_an_already_running_game(self):
        self.assertEqual({}, self.scan(100, []))
        self.assertEqual('', self.monitor.hud_notice())
        notice = self.scan(102, ['42'])
        self.assertIn('Steam started: Game One', notice['message'])
        self.assertIn('Visualizer 50%', notice['message'])
        self.assertIn('Idle gallery blocked', notice['message'])
        self.assertEqual(10000, notice['remaining_ms'])

    def test_repeated_scans_do_not_restart_ten_second_timer(self):
        first = self.scan(100, ['42'])
        for at in (102, 104, 106, 108, 109.999):
            notice = self.scan(at)
            self.assertEqual(first['id'], notice['id'])
            self.assertAlmostEqual((110 - at) * 1000, notice['remaining_ms'])
        self.assertEqual({}, self.scan(110))
        self.assertEqual('', self.monitor.hud_notice())
        self.assertTrue(self.monitor.running())

    def test_stop_notice_is_independent_and_expires_at_ten_seconds(self):
        first = self.scan(100, ['42'])
        stopped = self.scan(101, [])
        self.assertNotEqual(first['id'], stopped['id'])
        self.assertIn('Steam stopped: Game One', stopped['message'])
        self.assertIn('Visualizer normal', stopped['message'])
        self.assertIn('Idle gallery allowed', stopped['message'])
        self.scan(109)
        self.now = 110.999
        self.assertTrue(self.monitor.hud_notice())
        self.now = 111
        self.assertEqual({}, self.monitor.notice())
        self.assertEqual('', self.monitor.hud_notice())

    def test_one_game_exiting_while_another_runs_does_not_announce_stop(self):
        first = self.scan(100, ['42'])
        self.assertEqual(first['id'], self.scan(102, ['42', '43'])['id'])
        self.assertEqual(first['id'], self.scan(104, ['43'])['id'])
        self.assertTrue(self.monitor.running())
        last = self.scan(106, [])
        self.assertIn('Steam stopped: Game Two', last['message'])

    def test_restart_during_stop_notice_replaces_notice(self):
        self.scan(100, ['42'])
        stopped = self.scan(102, [])
        started = self.scan(103, ['43'])
        self.assertNotEqual(stopped['id'], started['id'])
        self.assertIn('Steam started: Game Two', started['message'])
        self.assertEqual(10000, started['remaining_ms'])

    def test_checkbox_updates_do_not_extend_notice(self):
        first = self.scan(100, ['42'])
        self.now = 104
        notice = self.monitor.configure({steam.REDUCE: False})['notice']
        self.assertEqual(first['id'], notice['id'])
        self.assertEqual(6000, notice['remaining_ms'])
        self.assertIn('Visualizer normal', notice['message'])
        self.assertIn('Idle gallery blocked', notice['message'])
        notice = self.monitor.configure({steam.REDUCE: True, steam.NO_GALLERY: False})['notice']
        self.assertIn('Visualizer 50%', notice['message'])
        self.assertIn('Idle gallery allowed', notice['message'])
        self.assertEqual(6000, notice['remaining_ms'])

    def test_disabling_both_clears_without_false_stop_and_reenable_announces(self):
        self.scan(100, ['42'])
        self.assertEqual({}, self.monitor.configure({k: False for k in steam.DEFAULTS})['notice'])
        self.scan(102)
        self.assertEqual('', self.monitor.hud_notice())
        self.monitor.configure({steam.REDUCE: True})
        self.assertIn('Steam started', self.scan(104)['message'])

    def test_stale_state_and_failed_scan_do_not_claim_game_stopped(self):
        self.scan(100, ['42'])
        self.now = 108.01
        self.assertEqual({}, self.monitor.notice())
        self.assertEqual('', self.monitor.hud_notice())
        self.monitor.processes = mock.Mock(side_effect=OSError('test failure'))
        # Execute exactly one worker iteration without sleeping or a live thread.
        self.monitor.stop = mock.Mock()
        self.monitor.stop.is_set.side_effect = [False, True]
        self.monitor._run()
        self.assertEqual({}, self.monitor.notice())
        self.assertIn('unavailable', self.monitor.status()['status'])
        self.monitor.processes = lambda: [{'name': 'steam.exe', 'exe': r'C:\Steam\steam.exe'}]
        self.assertEqual({}, self.scan(109))  # Same game recovered; no duplicate start.
        self.assertIn('Steam stopped', self.scan(110, [])['message'])

    def test_cached_hud_does_not_load_settings_or_scan(self):
        self.scan(100, ['42'])
        self.owner.load_player_settings = mock.Mock(side_effect=AssertionError('HUD read settings'))
        self.monitor.processes = mock.Mock(side_effect=AssertionError('HUD scanned'))
        self.monitor.registry = mock.Mock(side_effect=AssertionError('HUD read registry'))
        with mock.patch.object(steam, 'activity_message', side_effect=AssertionError('HUD formatted')):
            for _ in range(1000):
                self.assertIn('Steam started', self.monitor.hud_notice())
                self.assertEqual(30, self.monitor.visualizer_fps(60))

    def test_terminal_text_cannot_inject_rows_or_escape_codes(self):
        text = steam.activity_message(True, ('Name\n\033[31m\r\t' + 'x' * 200,), steam.DEFAULTS, compact=True)
        self.assertFalse(re.search(r'[\x00-\x1f\x7f-\x9f]', text))
        self.assertIn('… · Visualizer 50%', text)
        self.assertLess(len(text), 105)

    def test_new_monitor_has_new_notice_identity(self):
        first = self.scan(100, ['42'])
        second = steam.Monitor(self.owner, processes=self.monitor.processes,
                               registry=self.monitor.registry, inventory=self.monitor.inventory,
                               clock=lambda: self.now)
        second.tick()
        self.assertNotEqual(first['id'], second.notice()['id'])


class HudIntegrationTests(SteamNoticeTests):
    # Only load the HUD test here; inherited transition cases are loaded separately.
    def test_paused_or_playing_hud_repaints_on_change_and_expiry_only(self):
        tree = ast.parse(inspect.getsource(app.play_audio_file))
        node = copy.deepcopy(next(n for n in ast.walk(tree)
                                  if isinstance(n, ast.FunctionDef) and n.name == 'refresh_steam_notice'))
        node.body = [ast.Global(n.names) if isinstance(n, ast.Nonlocal) else n for n in node.body]
        ns = dict(steam_monitor=self.monitor, last_steam_notice='', help_overlay_until=0,
                  favorite_menu_active=False, default_menu_active=False,
                  render_controls=mock.Mock(), playback_fraction=lambda value: value / 100)
        exec(compile(ast.fix_missing_locations(ast.Module([node], type_ignores=[])), '<HUD helper>', 'exec'), ns)
        refresh = ns['refresh_steam_notice']
        self.scan(100, [])
        refresh(25)
        ns['render_controls'].assert_not_called()
        self.scan(102, ['42'])
        for _ in range(20):
            refresh(25)
        ns['render_controls'].assert_called_once_with(.25)
        self.scan(110)
        self.now = 112
        refresh(25)
        self.assertEqual(2, ns['render_controls'].call_count)
        ns['help_overlay_until'] = 999
        self.scan(113, [])
        refresh(25)
        self.assertEqual(2, ns['render_controls'].call_count)
        ns['help_overlay_until'] = 0
        refresh(25)
        self.assertEqual(3, ns['render_controls'].call_count)
        calls = [ast.unparse(n.args[0]) for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == 'refresh_steam_notice']
        self.assertCountEqual(['displayed_position', 'position'], calls)
        source = inspect.getsource(app.play_audio_file)
        self.assertIn('transient_prefix + steam_prefix + speed_fade_notice', source)
        self.assertIn('not transient and not steam_notice:', source)


class WebNoticeTests(unittest.TestCase):
    def test_notice_is_directly_below_title_and_embedded_module_is_current(self):
        html = app._paf_web_html()
        self.assertIn('</h1><div id="steamPlaybackNotice"', html)
        self.assertEqual(1, html.count('id="steamPlaybackNotice"'))
        self.assertIn('aria-live="polite" hidden', html)
        external = Path(app.__file__).with_name('PAFPlayer_steam.py').read_text(encoding='utf-8')
        self.assertEqual(external, app._PAF_BUNDLED_SOURCES['PAFPlayer_steam'])

    def test_browser_polling_expiry_pause_and_restart_with_fake_dom(self):
        node = shutil.which('node') or r'C:\Program Files\nodejs\node.exe'
        self.assertTrue(Path(node).is_file(), 'Node is required for the browser timer verification')
        script = re.findall(r'<script>(.*?)</script>', steam.augment('</body>'), re.S)[0]
        harness = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
let now=0,nextTimer=1,interval,timers=new Map(),pending=[];
const elements=new Map(['steamReduce','steamGallery','steamStatus','steamPlaybackNotice'].map(id=>[id,{hidden:true,textContent:''}]));
const handlers={};
global.performance={now:()=>now};
global.document={hidden:false,getElementById:id=>elements.get(id),addEventListener:(name,fn)=>handlers[name]=fn};
global.setTimeout=(fn,ms)=>{const id=nextTimer++;timers.set(id,{fn,at:now+ms});return id};
global.clearTimeout=id=>timers.delete(id);
global.setInterval=fn=>{interval=fn;return 1};
global.fetch=()=>new Promise(resolve=>pending.push(resolve));
const data=(id,message,remaining_ms)=>({local:true,token:'token',settings:{SteamReduceVisualizerLoad:1,SteamDisableIdleGallery:1},games:['Game'],status:'Steam game running',notice:{id,message,remaining_ms}});
async function reply(index,value){const resolve=pending.splice(index,1)[0];assert.ok(resolve);resolve({ok:true,json:async()=>value});await new Promise(setImmediate)}
function advance(ms){now+=ms;for(const [id,t] of [...timers])if(t.at<=now){timers.delete(id);t.fn()}}
const notice=elements.get('steamPlaybackNotice');
vm.runInThisContext(SCRIPT);
(async()=>{
 await reply(0,data('owner1:1','Steam started: <Game>',10000));
 assert.equal(notice.textContent,'Steam started: <Game>');assert.equal(notice.hidden,false);
 advance(3000);interval();await reply(0,data('owner1:1','Steam started: <Game>',7000));
 advance(6999);assert.equal(notice.hidden,false);
 advance(1);assert.equal(notice.hidden,true); // Expires without any server reply.
 interval();await reply(0,data('owner1:1','Stale retry',10000));assert.equal(notice.hidden,true);
 interval();await reply(0,data('owner1:2','Steam stopped: Game',10000));assert.equal(notice.hidden,false);
 advance(3000);interval();await reply(0,data('owner1:2','Steam stopped: Game',7000));
 advance(7000);assert.equal(notice.hidden,true);
 interval();await reply(0,data('owner2:1','New player started',10000));assert.equal(notice.hidden,false);
 interval();interval(); // Delayed response must not overwrite a newer response.
 await reply(1,data('owner2:2','Steam stopped: Game',10000));
 await reply(0,data('owner2:1','Old start',10000));assert.equal(notice.textContent,'Steam stopped: Game');
 advance(9000);interval();advance(1000);
 await reply(0,data('owner2:2','Expired in transit',500));assert.equal(notice.hidden,true);
 interval();await reply(0,data('owner2:3','Game started',10000));
 now+=11000;handlers.visibilitychange();assert.equal(notice.hidden,true);
 await reply(0,data('', '',0));assert.equal(notice.textContent,'');
 assert.equal(elements.get('steamReduce').checked,true);
 console.log('browser timer, delayed replies, reconnect and hidden-tab checks passed');
})().catch(error=>{console.error(error);process.exitCode=1});
""".replace('SCRIPT', json.dumps(script))
        result = subprocess.run([node, '-'], input=harness, text=True, encoding='utf-8',
                                capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


def load_tests(loader, tests, pattern):
    # HUD test shares the fixture, without running inherited transition cases twice.
    result = unittest.TestSuite(loader.loadTestsFromTestCase(SteamNoticeTests))
    result.addTest(HudIntegrationTests('test_paused_or_playing_hud_repaints_on_change_and_expiry_only'))
    result.addTests(loader.loadTestsFromTestCase(WebNoticeTests))
    return result
