from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
    assert s.count(a)==1,(a[:110],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
    name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
    while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
    while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
    if dest!=b:shutil.move(str(b),str(dest))
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf8')
s=once(s,"_HASH_COMMAND_ENTRY = PAFHashCommandEntry()",'''def hash_command_prompt(entry):
    """Return the current extended-command prompt, or None when dismissed."""
    return None if entry.buffer is None else '#' + entry.buffer + '▌'


_HASH_COMMAND_ENTRY = PAFHashCommandEntry()''')
anchor='    def render_live_audio_tags(*, force: bool = False) -> None:'
helper='''    def paint_hash_command_prompt() -> bool:
        prompt = hash_command_prompt(_HASH_COMMAND_ENTRY)
        if prompt is None:
            return False
        available = max(1, shutil.get_terminal_size((120, 30)).columns - 1)
        write_console(move_to(CONTROLS_ROW) + "\\033[1;38;2;255;220;90m"
                      + truncate_ansi_to_cells(prompt, available) + "\\033[0m\\033[K\\033[?25l")
        return True

'''+anchor
s=once(s,anchor,helper)
s=once(s,'        last_all_audio_tags_render = now_render\n\n    def set_live_audio_tags', '        last_all_audio_tags_render = now_render\n        paint_hash_command_prompt()\n\n    def set_live_audio_tags')
anchor='''            for index, line in enumerate(paginated[:overlay_rows])
        ) + "\\033[?25l")

    def start_interaction_visual_feedback('''
replacement='''            for index, line in enumerate(paginated[:overlay_rows])
        ) + "\\033[?25l")
        paint_hash_command_prompt()

    def start_interaction_visual_feedback('''
s=once(s,anchor,replacement)
s=once(s,'''            set_console_cursor_visible(True)
            return
        if all_audio_tags_active:
            return
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)''','''            set_console_cursor_visible(True)
            return
        if paint_hash_command_prompt():
            return
        if all_audio_tags_active:
            return
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)''')
s=once(s,'''                else:
                    action_value = (
                        key_action_reader(rename_editor=rename_editor)''','''                else:
                    hash_before = _HASH_COMMAND_ENTRY.buffer
                    action_value = (
                        key_action_reader(rename_editor=rename_editor)''')
s=once(s,'''                    if rename_editor.active and rename_editor.dirty:
                        render_controls(playback_fraction(current_prompt_position()))
                    if action_value is None and web_server is not None:''','''                    if rename_editor.active and rename_editor.dirty:
                        render_controls(playback_fraction(current_prompt_position()))
                    elif hash_before != _HASH_COMMAND_ENTRY.buffer:
                        if help_overlay_until:
                            render_help_overlay()
                        elif all_audio_tags_active:
                            render_live_audio_tags(force=True)
                        else:
                            render_controls(playback_fraction(current_prompt_position()))
                    if action_value is None and web_server is not None:''')
s=once(s,"'2026-11-12-v668-playlist-errors'","'2026-11-12-v669-hash-prompt'")
s=once(s,"PROGRAM_VERSION                = 'V668'","PROGRAM_VERSION                = 'V669'")
s=once(s,"PROGRAM_RELEASE_LABEL          = 'V668'","PROGRAM_RELEASE_LABEL          = 'V669'")
compile(s,str(p),'exec')
release=root/'releases/PAFPlayer_v669_hash_prompt.py';notes=root/'releases/PAFPlayer_v669_hash_prompt_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8')
docs=once(docs,'Current release: **V668** — missing playlist entries appear in the web Errors tab.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v668_playlist_errors_release_notes.md).','Current release: **V669** — visible console extended-command prompt.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v669_hash_prompt_release_notes.md).')
docs=once(docs,'During playback or pause, type `#` followed by a command, then press Enter or wait 1.5 seconds. Backspace edits and Escape cancels.', 'During playback or pause, type `#` to show an editable command prompt in the console. The typed characters appear as you enter them; press Enter or wait 1.5 seconds to execute a nonempty command and dismiss the prompt. Backspace edits, Escape cancels, and an empty prompt simply disappears after 1.5 seconds.')
changefile=root/'docs/PAFPlayer_changelog.md';change=changefile.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V669 — November 12, 2026\n\nShow an editable `#` extended-command prompt in the console while playing or paused. [Release notes](../releases/PAFPlayer_v669_hash_prompt_release_notes.md).\n')
replace(p,s,root/'releases');release.write_text(s,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changefile,change,root/'backups')
notes.write_text('# PAFPlayer V669 — Visible extended-command prompt\n\nTyping `#` displays the command and an insertion marker in the console while music plays or is paused. Backspace edits; Escape cancels. Enter or 1.5 seconds of inactivity submits a nonempty command, and an empty prompt disappears. The current display is restored on dismissal; Help and tag views retain prompt visibility.\n',encoding='utf8')
print('Published V669 workspace release with verified backups.')
