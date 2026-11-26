from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
def backup(p,folder):
 base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');i=0
 while b.exists():i+=1;b=p.with_name(base+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 dest=root/folder/b.name;dest.parent.mkdir(parents=True,exist_ok=True)
 while dest.exists():i+=1;dest=root/folder/(base+f' ({i}).bak')
 b.rename(dest)
p=root/'src/PAFPlayer_dj.py';backup(p,'src/backups');d=p.read_text(encoding='utf-8-sig')
needle='    def help_snapshot(self):'
addition='''    def hud_warning_messages(self):
        """Credit history is informational unless an enabled DJ chain has failed."""
        messages = self.warning_messages()
        options = self.options
        order = options.get('text_precedence') or LEGACY_PRECEDENCE.get(options.get('text_provider', 'auto'), TEXT_PRECEDENCE)
        uses_openai = 'openai' in order or options.get('speech_provider', 'auto') == 'auto'
        blocked = (not AI_DISABLED and options.get('enabled', False) and uses_openai
                   and self.stage == 'Failed' and bool(self.error)
                   and not self.ready and not self.working)
        return [message for message in messages if message != OPENAI_CREDIT_WARNING or blocked]

'''
assert d.count(needle)==1;d=d.replace(needle,addition+needle)
needle="        self.log.write('controller.start', enabled=self.options['enabled'], interval=self.options['interval'], text_provider=self.options['text_provider'], speech_provider=self.options['speech_provider'])"
assert needle in d;d=d.replace(needle,needle+"\n        if self.credit_warnings.active:\n            self.log.write('openai.credit.warning', severity='minor', message=OPENAI_CREDIT_WARNING)",1)
compile(d,str(p),'exec');p.write_text(d,encoding='utf-8')
p=root/'PAFPlayer.py';backup(p,'releases');s=p.read_text(encoding='utf-8');s=s.replace("= 'V755'","= 'V756'").replace('2026-11-25-v755-preview-focus-bottom-row','2026-11-25-v756-speed-confirmation-minor-credit')
s=s.replace("f'  Current: {current_speed():g}×   Speed: {digits or \"▏\"}   (= resets to 1×)'", "f'  Playing: {current_speed():g}×   Pending: {digits or \"▏\"}   (Enter applies; = resets to 1×)'")
s=s.replace("getattr(controller, 'warning_messages', lambda: [])()", "getattr(controller, 'hud_warning_messages', getattr(controller, 'warning_messages', lambda: []))()",1)
s=s.replace("for warning in getattr(dj_controller, 'warning_messages', lambda: [])():", "for warning in getattr(dj_controller, 'hud_warning_messages', getattr(dj_controller, 'warning_messages', lambda: []))():",1)
needle='''                        stop_process(process)
                        break
                    # Even if already at 1×, an explicit speed-reset action from'''
replacement='''                        stop_process(process)
                        redraw_entire_player_ui(position, indicator, clear_art=False)
                        break
                    # Even if already at 1×, an explicit speed-reset action from'''
assert needle in s;s=s.replace(needle,replacement,1)
needle='''                    render_controls(playback_fraction(displayed_position))
                    continue
                if action in {OUTPUT_STEREO, OUTPUT_51, OUTPUT_71}:'''
assert needle in s;s=s.replace(needle,'''                    redraw_entire_player_ui(displayed_position, indicator, clear_art=False)
                    continue
                if action in {OUTPUT_STEREO, OUTPUT_51, OUTPUT_71}:''',1)
needle='''                            render_controls(playback_fraction(position))
                            show_status(position, "⏸️")
                        if paused_action in VOLUME_STEPS'''
assert needle in s;s=s.replace(needle,'''                            redraw_entire_player_ui(position, "⏸️", clear_art=False)
                        if paused_action in VOLUME_STEPS''',1)
lines=s.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  modules=ast.literal_eval(line.split(' = ',1)[1]);modules['PAFPlayer_dj']=d;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(modules)+'\n'
 elif line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ") or line.startswith('_PAF_BUNDLED_SOURCES["PAFPlayer_dj"] = '):
  lines[i]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(d)+'\n'
s=''.join(lines);compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
for raw in ('docs/README.md','docs/PAFPlayer_changelog.md'):
 p=root/raw;backup(p,'docs/backups');text=p.read_text(encoding='utf-8-sig')
 if p.name=='README.md':text+='\n\n### V756: exact speed confirmation and minor credit warnings\n\nThe X menu labels the active speed as Playing and the typed value as Pending until Enter. Applying or resetting a speed clears the menu and redraws the HUD with the actual custom multiplier, including while paused. The decoder retains the precise multiplier.\n\nPast OpenAI credit exhaustion stays in Web Warnings and DJ diagnostics as a minor issue. It appears in the HUD/help warning list only when DJs are enabled, OpenAI participates in the configured text/speech chain, and the latest generation has failed without a ready fallback result. This decision uses cached job state and makes no network requests on the playback thread.\n'
 else:text=text.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V756 — November 25, 2026\n\nClear the X menu after applying the exact multiplier; distinguish Playing from Pending. Keep OpenAI credit history in Web Warnings and logs, escalating only for an enabled, failed DJ chain that uses OpenAI. [Release notes](../releases/PAFPlayer_v756_speed_credit_release_notes.md).\n',1)
 p.write_text(text,encoding='utf-8')
print('Updated V756; original contents backed up and verified.')
