from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
 assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
 while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';s=src.read_text(encoding='utf8')
s=once(s,'def ensure_piper(stage, valid, root=None):', '''_PIPER_SETUP_LOCK = threading.RLock()


def ensure_piper(stage, valid, root=None):
    with _PIPER_SETUP_LOCK:
        return _ensure_piper_unlocked(stage, valid, root)


def _ensure_piper_unlocked(stage, valid, root=None):''')
s=once(s,'def ensure_piper_male(auto_exe, stage, valid, root=None):', '''def ensure_piper_male(auto_exe, stage, valid, root=None):
    with _PIPER_SETUP_LOCK:
        return _ensure_piper_male_unlocked(auto_exe, stage, valid, root)


def _ensure_piper_male_unlocked(auto_exe, stage, valid, root=None):''')
anchor='def synthesize(history,opts,stage,valid,on_dialogue=None):'
helper='''def installed_piper_male(root=None):
    base=Path(root) if root is not None else piper_support_root()
    for folder in sorted(base.glob('male-voice-*')) if base.is_dir() else ():
        voice=folder/'en_US-ryan-medium.onnx';config=voice.with_name(voice.name+'.json')
        try:
            if (folder/'complete').is_file() and voice.is_file() and voice.stat().st_size>44 and config.is_file():return str(voice)
        except OSError:continue
    return None


'''+anchor
s=once(s,anchor,helper)
old="    voices=[x.strip() for x in opts['piper_voices'].splitlines() if x.strip()]\n    exe=opts['piper_executable'] or shutil.which('piper')"
new="""    configured=[x.strip() for x in opts['piper_voices'].splitlines() if x.strip()]
    voices=[x for x in configured if Path(x).is_file()]
    configured_exe=opts['piper_executable']
    exe=(configured_exe if configured_exe and Path(configured_exe).is_file() else '') or shutil.which('piper')
    if (configured_exe and not Path(configured_exe).is_file()) or len(voices)!=len(configured):
        warning=(warning+'; ' if warning else '')+'Some Piper paths were missing; using available or automatic voices'"""
s=once(s,old,new)
s=once(s,"self.commentary=[];self.talk_log_error='';self.recent_dialogues=deque(maxlen=3);self.ready_dialogue=None", "self.commentary=[];self.talk_log_error='';self.recent_dialogues=deque(maxlen=3);self.ready_dialogue=None;self.piper_setup_running=False;self.piper_setup_stage='';self.piper_setup_error=''")
s=once(s,"        with self.lock:\n            self.options=settings({**self.options,**patch},changed);", "        with self.lock:\n            was_enabled=self.options['enabled']\n            self.options=settings({**self.options,**patch},changed);")
s=once(s,"            if not self.options['enabled']:self.cancel_playback()\n            return dict(self.options)", "            if not self.options['enabled']:self.cancel_playback()\n            elif not was_enabled and getattr(self.runtime,'app',None) is not None:self.start_piper_setup()\n            return dict(self.options)")
anchor='    def sleep_status(self):'
method='''    def start_piper_setup(self, force=False):
        """Prepare free local speech once at startup or on an explicit retry."""
        with self.lock:
            if self.piper_setup_running:return False
            opts=dict(self.options)
            configured=[x.strip() for x in opts['piper_voices'].splitlines() if x.strip()]
            custom_exe=opts['piper_executable']
            exe_ok=bool((custom_exe and Path(custom_exe).is_file()) or shutil.which('piper'))
            if not force and exe_ok and configured and all(Path(x).is_file() for x in configured):
                self.piper_setup_stage='Configured Piper voices are ready';return False
            self.piper_setup_running=True;self.piper_setup_error='';self.piper_setup_stage='Preparing free Piper voices';self.notice=self.piper_setup_stage
        def stage(message):
            with self.lock:self.piper_setup_stage=message
            self.log.write('piper.setup.stage',stage=message)
        def valid():return not self.runtime.stop_event.is_set()
        def work():
            try:
                exe,_voice=ensure_piper(stage,valid)
                if opts['men'] and opts['speakers']>1:ensure_piper_male(exe,stage,valid)
                with self.lock:self.piper_setup_stage='Free Piper voices are ready';self.notice=self.piper_setup_stage
                self.log.write('piper.setup.complete')
            except InterruptedError:
                with self.lock:self.piper_setup_stage='Piper setup stopped'
                self.log.write('piper.setup.cancelled')
            except Exception as exc:
                with self.lock:self.piper_setup_error='Piper setup failed; check network and use Download / repair to retry';self.notice=self.piper_setup_error
                self.log.write('piper.setup.failed',**_error_fields(exc))
            finally:
                with self.lock:self.piper_setup_running=False
        threading.Thread(target=work,name='paf-piper-setup',daemon=True).start();return True

'''+anchor
s=once(s,anchor,method)
s=once(s,"            private = installed_piper()\n            sleep_reason,sleep_notice=self.sleep_status()", "            private = installed_piper();male=installed_piper_male()\n            configured=[x.strip() for x in self.options['piper_voices'].splitlines() if x.strip()]\n            missing=[x for x in configured if not Path(x).is_file()]\n            if self.options['piper_executable'] and not Path(self.options['piper_executable']).is_file():missing.insert(0,self.options['piper_executable'])\n            sleep_reason,sleep_notice=self.sleep_status()")
s=once(s,"return {'prompt_builtins':dict(BUILTIN_PROMPTS),", "return {'piper_setup_running':self.piper_setup_running,'piper_setup_stage':self.piper_setup_stage,'piper_setup_error':self.piper_setup_error,'piper_auto_executable':private[0] if private else '', 'piper_auto_voices':([private[1]] if private else [])+([male] if male else []),'piper_missing_paths':missing,'prompt_builtins':dict(BUILTIN_PROMPTS),")
s=once(s,"if value is None:value=runtime.ai_dj_controller=Controller(runtime)\n        return value", "if value is None:\n            value=runtime.ai_dj_controller=Controller(runtime)\n            if value.options['enabled'] and getattr(runtime,'app',None) is not None:value.start_piper_setup()\n        return value")
compile(s,str(src),'exec')
wfpath=root/'src/PAFPlayer_web_workflows.py';wf=wfpath.read_text(encoding='utf8')
old="""            changed=payload.pop('changed',None)
            data={'settings':get_controller(runtime).configure(payload,changed)}"""
new="""            controller=get_controller(runtime)
            if 'setup_piper' in payload:
                if payload!={'setup_piper':True}:raise ValueError('Invalid Piper setup request')
                data={'started':controller.start_piper_setup(force=True)}
            else:
                changed=payload.pop('changed',None)
                data={'settings':controller.configure(payload,changed)}"""
wf=once(wf,old,new);compile(wf,str(wfpath),'exec')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True)
i=[n for n,l in enumerate(lines) if l.startswith('_PAF_BUNDLED_SOURCES = ')];assert len(i)==1
bundle=ast.literal_eval(lines[i[0]].split(' = ',1)[1]);bundle['PAFPlayer_web_workflows']=wf;lines[i[0]]='_PAF_BUNDLED_SOURCES = '+repr(bundle)+'\n'
i=[n for n,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(i)==1;lines[i[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines)
anchor='<label>Piper voice model paths, one per line <textarea id="dj_piper_voices" rows="2"></textarea></label>'
markup=anchor+'''\n<p>Leave the fields blank for automatic free Piper setup. If a configured path is missing, PAFPlayer uses available automatic voices instead.</p>
<pre id="djPiperDetails" style="white-space:pre-wrap;overflow-wrap:anywhere">Checking installed Piper voices…</pre>
<button id="djPiperSetup" type="button" disabled>Download / repair free Piper voices</button><p id="djPiperSetupStatus" role="status">Checking Piper setup…</p>'''
text=once(text,anchor,markup)
text=once(text,'When local speech is needed, PAFPlayer automatically installs Piper and a default voice in private storage if needed.', 'When AI DJ is enabled, PAFPlayer prepares free Piper voices in the background on startup if needed; use Download / repair to retry.')
js=(root/'tests/runs/v672_piper_setup_ui.js').read_text(encoding='utf8');anchor='    return (\n        html.replace("__POLL_MS__", str(WEB_STATUS_POLL_MILLISECONDS))';text=once(text,anchor,'    html = html.replace("</body>", '+repr('<script>\n'+js+'\n</script></body>')+', 1)\n'+anchor)
text=once(text,"'2026-11-12-v671-dj-variety'","'2026-11-12-v672-piper-startup'")
text=once(text,"PROGRAM_VERSION                = 'V671'","PROGRAM_VERSION                = 'V672'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V671'","PROGRAM_RELEASE_LABEL          = 'V672'");compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v672_piper_startup.py';notes=root/'releases/PAFPlayer_v672_piper_startup_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8');docs=once(docs,'Current release: **V671** — varied DJ conversations using newly played tracks.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v671_dj_variety_release_notes.md).','Current release: **V672** — automatic Piper voice preparation and visible setup.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v672_piper_startup_release_notes.md).')
anchor='## AI Podcaster / DJ';docs=once(docs,anchor,anchor+'\n\nWhen AI DJ is enabled, the player prepares free Piper voices in the background at startup if needed. The AI DJ tab shows detected automatic executable and voice paths, missing configured paths, setup progress and a **Download / repair free Piper voices** retry button. Blank paths mean automatic setup. Missing configured paths are skipped in favor of working paths or the automatic install; existing choices are preserved. Downloads use disk space and network bandwidth.\n')
changelog=root/'docs/PAFPlayer_changelog.md';change=changelog.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V672 — November 12, 2026\n\nPrepare free Piper voices on AI DJ startup, show discovered paths and setup progress, and recover from missing custom paths. [Release notes](../releases/PAFPlayer_v672_piper_startup_release_notes.md).\n')
replace(src,s,root/'backups');replace(wfpath,wf,root/'src/backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V672 — Piper startup preparation\n\nPrepare free local Piper voices in the background when AI DJ starts. The DJ tab displays detected model paths and setup progress and offers a retry button. Missing custom executable or model paths fall back to working automatic paths. Installations are serialized so startup and speech synthesis do not race.\n',encoding='utf8')
print('Published V672 with verified backups.')
