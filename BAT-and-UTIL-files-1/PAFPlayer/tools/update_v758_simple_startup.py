from pathlib import Path
import datetime,hashlib,shutil,ast
root=Path.cwd()
def backup(p,folder):
 base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');i=0
 while b.exists():i+=1;b=p.with_name(base+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest()
 target=root/folder/b.name;target.parent.mkdir(exist_ok=True,parents=True)
 while target.exists():i+=1;target=root/folder/(base+f' ({i}).bak')
 b.rename(target)
p=root/'src/PAFPlayer_playback_focus.py';backup(p,'src/backups');s=p.read_text(encoding='utf-8-sig')
s=s.replace("pause='web_pause', resume='web_play'):","pause='web_pause', resume='web_play', trace=None):",1)
s=s.replace('        self.claimed = False\n        self.server = None','        self.claimed = False\n        self.started_ns = time.monotonic_ns()\n        self.starting = bool(preview)\n        self.held_before_start = False\n        self.trace = trace or (lambda *_args, **_kwargs: None)\n        self.server = None',1)
needle='    @staticmethod\n    def request('
helper='''    @staticmethod
    def process_alive(pid):
        """Skip exited Windows PIDs before any slow refused TCP connection."""
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            return False
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.OpenProcess(0x1000, False, pid)
            if not handle:
                return ctypes.get_last_error() != 87  # Access denied is unknown, not dead.
            try:
                code = wintypes.DWORD()
                return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
            finally:
                kernel.CloseHandle(handle)
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def retire(self, path):
        """Archive stale registration files; never delete or replace them."""
        retired = self.root / 'retired'
        retired.mkdir(exist_ok=True)
        target = retired / path.name
        suffix = 0
        while target.exists():
            suffix += 1
            target = retired / (path.stem + ' (%d)' % suffix + path.suffix)
        try:
            path.rename(target)
        except FileNotFoundError:
            pass  # A graceful shutdown may have archived it concurrently.

'''
assert needle in s;s=s.replace(needle,helper+needle,1)
s=s.replace("'identity': self.identity}, target)","'identity': self.identity, 'preview': self.preview, 'started_ns': self.started_ns}, target)",1)
s=s.replace('''                if not self.paused[0]:
                    self.enqueue(self.pause)''','''                if self.starting:
                    # A newer preview can pause us before our decoder exists.
                    # Acknowledge the silent state instead of waiting on our own
                    # startup thread to consume a queued pause (mutual deadlock).
                    self.held_before_start = True
                    self.paused[0] = True
                elif not self.paused[0]:
                    self.enqueue(self.pause)''',1)
s=s.replace('''            self.restore = False
            self.enqueue(self.resume)''','''            self.restore = False
            if self.held_before_start:
                self.held_before_start = False
                self.paused[0] = False
            else:
                self.enqueue(self.resume)''',1)
s=s.replace('''        self.claimed = True
        try:''','''        self.claimed = True
        started = time.monotonic()
        self.trace('preview.focus.start')
        try:''',1)
needle="                    peer = json.loads(path.read_text(encoding='utf-8'))\n                    # Remember before requesting:"
replacement="""                    peer = json.loads(path.read_text(encoding='utf-8'))
                    if not isinstance(peer, dict) or not self.process_alive(peer.get('pid')):
                        self.trace('preview.focus.stale', peer_pid=peer.get('pid') if isinstance(peer, dict) else None)
                        self.retire(path)
                        continue
                    # The newest preview has priority. An older startup must not
                    # pause a newer preview that is already asking it to wait.
                    if peer.get('preview') and peer.get('started_ns', 0) > self.started_ns:
                        continue
                    self.trace('preview.focus.pause-request', peer_pid=peer.get('pid'))
                    # Remember before requesting:"""
assert needle in s;s=s.replace(needle,replacement,1)
needle="                if not result.get('ok'):\n                    raise RuntimeError('Another PAFPlayer did not acknowledge pausing; preview has not started.')\n        except BaseException:"
replacement="""                if not result.get('ok'):
                    raise RuntimeError('Another PAFPlayer did not acknowledge pausing; preview has not started.')
                self.trace('preview.focus.paused', peer_pid=peer.get('pid'))
            while True:
                with self.lock:
                    waiting = bool(self.leases)
                    if not waiting:
                        self.starting = False
                        break
                if self.stopping.wait(.02):
                    raise InterruptedError('Preview startup was cancelled')
            self.trace('preview.focus.ready', elapsed_ms=round((time.monotonic() - started) * 1000, 2))
        except BaseException:"""
assert needle in s;s=s.replace(needle,replacement,1)
start=s.index("        if hasattr(self, 'descriptor') and self.descriptor.exists():")
s=s[:start]+"        if hasattr(self, 'descriptor') and self.descriptor.exists():\n            self.retire(self.descriptor)\n"
compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';backup(p,'releases');m=p.read_text(encoding='utf-8-sig');m=m.replace("= 'V757'","= 'V758'").replace('2026-11-25-v757-smooth-idle-artwork','2026-11-25-v758-simple-startup-recovery')
old="        playback_paused_state = [bool(persisted_settings.get('PlaybackPaused', 0))]";new="        playback_paused_state = [False if simple_instance else bool(persisted_settings.get('PlaybackPaused', 0))]"
assert old in m;m=m.replace(old,new,1)
# Keep the embedded regression in step with the intended preview exception.
m=m.replace('self.assertIn("playback_paused_state = [bool(persisted_settings.get(\'PlaybackPaused\', 0))]", main_source)', 'self.assertIn("playback_paused_state = [False if simple_instance else bool(persisted_settings.get(\'PlaybackPaused\', 0))]", main_source)')
m=m.replace('web_server.enqueue_action, preview=simple_instance, pause=WEB_PAUSE, resume=WEB_PLAY)', 'web_server.enqueue_action, preview=simple_instance, pause=WEB_PAUSE, resume=WEB_PLAY, trace=append_pafplayer_trace)',1)
old="                'PlaybackPaused': int(playback_paused_state[0] and not external_media_controller.auto_paused),"
new="                'PlaybackPaused': int(persisted_settings.get('PlaybackPaused', 0)) if simple_instance else int(playback_paused_state[0] and not external_media_controller.auto_paused),"
assert old in m;m=m.replace(old,new,1)
lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_playback_focus']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
for raw in ('docs/README.md','docs/PAFPlayer_changelog.md'):
 p=root/raw;backup(p,'docs/backups');text=p.read_text(encoding='utf-8-sig')
 if p.name=='README.md':text+='\n\n### V758: simple-preview startup recovery\n\n`--simple` checks registered peer process liveness before connecting, archives registrations for exited processes under `workflows/playback-peers/retired/`, and traces focus startup, skipped dead peers, pause acknowledgements and readiness. This prevents accumulated crash leftovers from adding seconds of refused connections per old preview. A fresh preview starts unpaused and does not overwrite the main player\'s saved pause setting.\n\nThe newest preview takes priority over older preview startups. Older previews acknowledge their silent pre-decoder state and wait for the newer preview to finish, rather than both startup threads waiting for pause commands neither can consume. Existing pause leases continue to preserve the main player\'s original state.\n'
 else:text=text.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V758 — November 25, 2026\n\nRecover simple-preview startup by skipping/archiving exited peer registrations, tracing pause coordination, handling overlapping startups without mutual waits, and isolating preview initial/persisted pause state. [Release notes](../releases/PAFPlayer_v758_simple_startup_release_notes.md).\n',1)
 p.write_text(text,encoding='utf-8')
print('V758 startup fixes applied; originals backed up and verified.')
