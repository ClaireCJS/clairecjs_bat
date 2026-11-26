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
s=s.replace("resume='web_play', trace=None):","resume='web_play', trace=None, guarded=False):",1)
s=s.replace('        self.restore = False\n        self.peers', '        self.restore = False\n        self.guarded = guarded\n        self.pending_pause = False\n        self.pending_resume = False\n        self.resume_inflight = False\n        self.peers',1)
s=s.replace('''                if not self.leases:
                    self.restore = not bool(self.paused[0])
                self.leases[key]''','''                if not self.leases:
                    self.restore = self.pending_resume or self.resume_inflight or not bool(self.paused[0])
                self.pending_resume = False
                self.resume_inflight = False
                self.trace('preview.focus.lease', paused_before=bool(self.paused[0]),
                           resume_owned=self.restore, leases=len(self.leases) + int(key not in self.leases))
                self.leases[key]''',1)
s=s.replace('''                elif not self.paused[0]:
                    self.enqueue(self.pause)''','''                elif not self.paused[0]:
                    if self.guarded:
                        self.pending_pause = True
                    else:
                        self.enqueue(self.pause)''',1)
s=s.replace('''            else:
                self.enqueue(self.resume)

    def claim(self):''','''            elif self.guarded:
                self.pending_resume = True
            else:
                self.enqueue(self.resume)
            self.trace('preview.focus.restore-pending', guarded=self.guarded,
                       paused=bool(self.paused[0]), pending_resume=self.pending_resume)

    def observe_action(self, action, paused, *, toggle='pause-toggle', stop='web-stop'):
        """An explicit user Pause/Stop revokes any preview-owned future resume."""
        if action in {self.pause, stop} or (action == toggle and not paused):
            with self.lock:
                self.restore = False
                self.pending_resume = False
                self.resume_inflight = False
                self.trace('preview.focus.manual-hold', paused=bool(paused), leases=len(self.leases))

    def pop_action(self):
        """Resolve preview transport on the audio owner thread against current leases."""
        with self.lock:
            if self.pending_pause:
                self.pending_pause = False
                if self.leases and not self.paused[0]:
                    return self.pause
            if self.pending_resume:
                self.pending_resume = False
                if not self.leases and self.paused[0]:
                    self.resume_inflight = True
                    self.trace('preview.focus.restore-approved')
                    return self.resume
        return None

    def guard_action(self, action, paused, *, toggle='pause-toggle', external_resume='external-media-resume'):
        """A preview pause cannot be undone by stale Play or automatic media resume."""
        with self.lock:
            if self.leases and (action in {self.resume, external_resume} or (action == toggle and paused)):
                self.trace('preview.focus.resume-blocked', action=action, leases=len(self.leases))
                return None
        return action

    def claim(self):''',1)
compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';backup(p,'releases');m=p.read_text(encoding='utf-8-sig');m=m.replace("= 'V758'","= 'V759'").replace('2026-11-25-v758-simple-startup-recovery','2026-11-25-v759-preserve-main-pause')
m=m.replace('resume=WEB_PLAY, trace=append_pafplayer_trace)', 'resume=WEB_PLAY, trace=append_pafplayer_trace, guarded=True)',1)
needle='''                if action_value == PLAYLIST_WINDOW_TOGGLE:
'''
new='''                if playback_focus is not None:
                    if action_value is None:
                        action_value = playback_focus.pop_action()
                    else:
                        playback_focus.observe_action(action_value, bool(prompt_paused_state[0]),
                                                      toggle=PAUSE_TOGGLE, stop=WEB_STOP)
                if action_value == PLAYLIST_WINDOW_TOGGLE:
'''
assert m.count(needle)==1;m=m.replace(needle,new,1)
needle='''                        paused_action = external_media_controller.filter_action(paused_action, True, paused_now)
'''
new=needle+'''                        if playback_focus is not None:
                            paused_action = playback_focus.guard_action(paused_action, True,
                                toggle=PAUSE_TOGGLE, external_resume=EXTERNAL_MEDIA_RESUME)
'''
assert m.count(needle)==1;m=m.replace(needle,new,1)
lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_playback_focus']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
for raw in ('docs/README.md','docs/PAFPlayer_changelog.md'):
 p=root/raw;backup(p,'docs/backups');text=p.read_text(encoding='utf-8-sig')
 if p.name=='README.md':text+='\n\n### V759: preserve paused/stopped players during previews\n\nA player that was already paused or stopped stays that way when a simple preview starts and exits. Preview-owned transport is resolved on the audio thread against current leases, so a pending restore cannot restart a player after another preview has taken over. Explicit Pause/Stop revokes preview restore ownership. Automatic external-media resume and stale Play commands are held while a preview lease is active. Diagnostic events record lease ownership and approved/blocked restoration without authentication data.\n\nRestart the main player once as well as previews to load the receiver-side guards. Only players that a preview actually paused are eligible for automatic restoration.\n'
 else:text=text.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V759 — November 25, 2026\n\nResolve preview restore on the audio thread, preserve explicit Pause/Stop intent, and block stale/automatic resume while another preview holds a lease. [Release notes](../releases/PAFPlayer_v759_preserve_main_pause_release_notes.md).\n',1)
 p.write_text(text,encoding='utf-8')
print('V759 guarded restoration applied; originals backed up and verified.')
