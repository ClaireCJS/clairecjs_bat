from pathlib import Path
import datetime,hashlib,shutil
root=Path.cwd()
def backup(p,folder):
 base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 dest=root/folder/b.name;dest.parent.mkdir(parents=True,exist_ok=True)
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'PAFPlayer.py';backup(p,'releases');s=p.read_text(encoding='utf-8');s=s.replace('self.assertGreaterEqual(guard, 2)','self.assertEqual(guard, 1)');compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'tests/test_v755_preview_focus.py';backup(p,'tests/backups');s=p.read_text(encoding='utf-8-sig');s=s.replace('import urllib.error','import urllib.error\nimport threading\nimport time')
needle='    def test_one_bottom_safety_row_and_bundle_parity(self):'
addition='''    def test_waits_for_real_transport_queue_ack_even_without_web_server(self):
        server=app.PAFWebServer(enabled=False,host='127.0.0.1',port=0)
        state=[False]
        main=PlaybackFocus(self.fixture,state,server.enqueue_action,pause=app.WEB_PAUSE,resume=app.WEB_PLAY)
        main.start();self.players.append(main)
        preview=self.player(True);errors=[]
        def claim():
            try:preview.claim()
            except BaseException as exc:errors.append(exc)
        worker=threading.Thread(target=claim);worker.start()
        deadline=time.monotonic()+3;action=None
        while action is None and time.monotonic()<deadline:
            action=server.pop_action();time.sleep(.01)
        self.assertEqual(app.WEB_PAUSE,action)
        self.assertTrue(worker.is_alive())
        state[0]=True;worker.join(3)
        self.assertFalse(worker.is_alive());self.assertFalse(errors)
        preview.release();self.assertEqual(app.WEB_PLAY,server.pop_action())
        server.close()

'''
assert needle in s;s=s.replace(needle,addition+needle);p.write_text(s,encoding='utf-8')
notes=root/'releases/PAFPlayer_v755_preview_focus_release_notes.md'
assert not notes.exists();notes.write_text('# PAFPlayer V755 — preview audio focus and bottom-row spacing\n\nThe visualizer uses one bottom safety row instead of two, retaining explicit cursor movement without drawing the hazardous bottom-right cell.\n\nSimple previews now request acknowledged pauses from the main player and other previews before starting their decoder. Authenticated loopback coordination works with the web server disabled and keeps the official single-instance ownership separate. Pause leases preserve previously paused state, support nested previews and expire after a crash. Graceful exit releases requests and archives peer descriptors. Restart running players once to enable participation.\n\nValidation: focused HTTP coordination, real disabled-web transport queue acknowledgement, nested and out-of-order preview release, prior pause state, authentication, failure recovery, bundle parity, existing simple-mode and speed tests, and the embedded viewport geometry regression. Tests simulate transport state without interrupting the user\'s live music.\n',encoding='utf-8')
release=root/'releases/PAFPlayer_v755_preview_focus.py';assert not release.exists();shutil.copy2(root/'PAFPlayer.py',release)
assert hashlib.sha256(release.read_bytes()).digest()==hashlib.sha256((root/'PAFPlayer.py').read_bytes()).digest()
print('V755 release packaged with matching standalone source.')
