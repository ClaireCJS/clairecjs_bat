from pathlib import Path
import ast, datetime, hashlib, shutil

root = Path(__file__).resolve().parents[2]
player = root / 'PAFPlayer.py'
source = root / 'src/PAFPlayer_dj.py'
candidate = root / 'tests/runs/dj-v657-stage/PAFPlayer_dj_candidate_v7.py'

def once(s, old, new):
    assert s.count(old) == 1, (old[:100], s.count(old))
    return s.replace(old, new, 1)

def backup(p):
    name = p.name + datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
    dst = p.with_name(name)
    i = 0
    while dst.exists():
        i += 1
        dst = p.with_name(name[:-4] + f' ({i}).bak')
    shutil.copy2(p, dst)
    assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256(dst.read_bytes()).digest()
    return dst

old_helpers = source.read_text(encoding='utf-8')
helpers = old_helpers[old_helpers.index('DJ_DEFAULTS ='):]
dj = candidate.read_text(encoding='utf-8') + '\n\n# Additional presentation helpers.\n' + helpers
dj = once(dj, 'def synthesize(history,opts,stage,valid):', 'def synthesize(history,opts,stage,valid,on_dialogue=None):')
dj = once(dj, "    lines,warning=dialogue(history,opts)\n    selected_voices", "    lines,warning=dialogue(history,opts)\n    if not valid(): raise InterruptedError()\n    if on_dialogue is not None: on_dialogue(lines)\n    selected_voices")
dj = once(dj, "        self.ready=None;self.forced=False;self.stage='';self.error='';self.notice='';self.attempted=-1", "        self.ready=None;self.forced=False;self.stage='';self.error='';self.notice='';self.attempted=-1\n        self.commentary=[]")
dj = once(dj, '    def record(self,artist,title,prepare=True):', '''    def help_snapshot(self):
        with self.lock:
            return (tuple(self.commentary), self.stage, self.error, self.notice, self.options['enabled'])

    def record(self,artist,title,prepare=True):''')
dj = once(dj, '        def work():\n            try:\n                result,warning=self.producer(history,opts,stage,valid)', '''        def publish_dialogue(lines):
            with self.lock:
                if valid(): self.commentary=list(lines)
        def work():
            try:
                if self.producer is synthesize:
                    result,warning=self.producer(history,opts,stage,valid,on_dialogue=publish_dialogue)
                else:
                    result,warning=self.producer(history,opts,stage,valid)''')
dj = once(dj, "                    if valid():self.error='DJ generation failed; check OpenAI, Ollama, and Piper settings';self.stage='Failed';self.forced=False", "                    if valid():\n                        self.error=('DJ speech failed; text is available in Help. Check OpenAI and Piper settings' if self.commentary else 'DJ text generation failed; check OpenAI and Ollama settings')\n                        self.stage='Failed';self.forced=False")

text = player.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
indexes = [i for i, line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")]
assert len(indexes) == 1
lines[indexes[0]] = "_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = " + repr(dj) + '\n'
text = ''.join(lines)
text = once(text, "'2026-11-11-v657-experimental-ai-dj'", "'2026-11-11-v658-dj-help-commentary'")
text = once(text, "PROGRAM_VERSION                = 'V657'", "PROGRAM_VERSION                = 'V658'")
text = once(text, "PROGRAM_RELEASE_LABEL          = 'V657'", "PROGRAM_RELEASE_LABEL          = 'V658'")
marker = 'def play_audio_file(\n'
helper = '''def dj_help_rows(controller, width: int) -> list[str]:
    """Return safe, wrapped DJ status and text for the local help overlay."""
    snapshot = getattr(controller, 'help_snapshot', lambda: ((), '', '', '', False))()
    commentary, stage, error, notice, enabled = snapshot
    def clean(value):
        return ''.join(ch if ch.isprintable() else ' ' for ch in str(value))
    rows = ['AI DJ: ' + ('on' if enabled else 'off') + (' · ' + clean(stage) if stage else '')]
    if error: rows.extend(wrap_to_cells(clean(error), width))
    elif notice: rows.extend(wrap_to_cells(clean(notice), width))
    for speaker, line in commentary:
        rows.extend(wrap_to_cells(f'Speaker {speaker}: {clean(line)}', width))
    if not commentary:
        rows.append('No commentary yet. Use #djforce after playing a track.')
    return rows


'''
text = once(text, marker, helper + marker)
text = once(text, '        if help_key_order_mode:\n            by_base = {}', '''        # Keep commentary below track diagnostics and before the shortcut list.
        # It participates in normal help pagination so long dialogue remains readable.
        masthead_rows = len(rendered)
        rendered.extend("\\033[38;2;205;190;255m" + row + "\\033[0m"
                        for row in dj_help_rows(dj_controller, available))
        rendered.append("\\033[38;2;85;195;185m" + divider_plain + "\\033[0m")
        if help_key_order_mode:
            by_base = {}''')
text = once(text, '        masthead_rows = 5 + len(track_alert_help_rows)\n        masthead = rendered[:masthead_rows]', '        masthead = rendered[:masthead_rows]')
text = once(text, "    help_overlay_rows = 0\n", "    help_overlay_rows = 0\n    help_dj_snapshot = None\n")
text = once(text, '                if help_overlay_until:\n                    modifier_down = any(', '''                if help_overlay_until:
                    current_dj_snapshot = getattr(dj_controller, 'help_snapshot', lambda: None)()
                    if current_dj_snapshot != help_dj_snapshot:
                        help_dj_snapshot = current_dj_snapshot
                        render_help_overlay()
                    modifier_down = any(''')
compile(dj, str(source), 'exec')
compile(text, str(player), 'exec')
assert (root/'releases/PAFPlayer_v658_dj_help_commentary.py').exists() is False
for path, data in ((source,dj), (player,text)):
    saved = backup(path)
    path.write_text(data, encoding='utf-8', newline='')
    archive = root / ('releases' if path == player else 'backups') / saved.name
    assert not archive.exists()
    shutil.move(str(saved), str(archive))
(root/'releases/PAFPlayer_v658_dj_help_commentary.py').write_text(text,encoding='utf-8',newline='')
print('Updated DJ source and player; created V658 release; archived verified backups.')
