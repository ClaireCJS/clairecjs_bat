from pathlib import Path
import datetime,hashlib,shutil

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
anchor='def dj_key_file():'
insert='''DJ_TALK_LOG_PATH = Path(r'C:\\logs\\PAFPlayer\\dj.log') if os.name == 'nt' else Path('/logs/PAFPlayer/dj.log')


def append_talk_log(history, lines, opts, path=None, now=None):
    """Append generated dialogue and its input tracks without altering prior entries."""
    target = Path(path) if path is not None else DJ_TALK_LOG_PATH
    instant = now if now is not None else datetime.now().astimezone()
    def oneline(value): return ' '.join(str(value or '').split())
    output = ['', '━━━━━━━━━━━━━━━━━━━━━━', '', '⭐DATE:  '+instant.strftime('%Y%m%d  %I:%M%p'), '']
    for number, track in enumerate(reversed(history), 1):
        output.append(f"⛧LAST SONG #{number}: {oneline(track.get('artist'))} - {oneline(track.get('title'))}")
    output.append('')
    for speaker, line in lines:
        icon = '👩🗣️' if speaker <= opts['women'] else '👨🗣️'
        output.append(f'{icon} {oneline(line)}')
    entry = '\\n'.join(output)+'\\n\\n'
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a', encoding='utf8', newline='\\n') as stream:
        stream.write(entry)


'''+anchor
s=once(s,anchor,insert)
s=once(s,'        self.commentary=[]\n        self.sunrise_location',"        self.commentary=[];self.talk_log_error=''\n        self.sunrise_location")
s=once(s,"'warnings':self.credit_warnings.messages()+([sleep_notice] if sleep_notice else [])", "'warnings':self.credit_warnings.messages()+([sleep_notice] if sleep_notice else [])+([self.talk_log_error] if self.talk_log_error else [])")
s=once(s,'return self.credit_warnings.messages()+([note] if note else [])','return self.credit_warnings.messages()+([note] if note else [])+([self.talk_log_error] if self.talk_log_error else [])')
s=once(s,'return (tuple(self.commentary), stage, self.error, self.notice, self.options[\'enabled\'])',"return (tuple(self.commentary), stage, self.error, '; '.join(x for x in (self.notice,self.talk_log_error) if x), self.options['enabled'])")
old="                    self.commentary=list(lines);published.append(True);self.log.write('text.ready', job=token, turns=len(lines))"
new="""                    self.commentary=list(lines);published.append(True);self.log.write('text.ready', job=token, turns=len(lines))
                    try:
                        append_talk_log(history,lines,opts)
                        self.talk_log_error='';self.log.write('talk_log.written',job=token,turns=len(lines))
                    except (OSError, UnicodeError, ValueError) as exc:
                        self.talk_log_error='AI DJ conversation log could not be written to '+str(DJ_TALK_LOG_PATH)
                        self.log.write('talk_log.failed',job=token,**_error_fields(exc))"""
s=once(s,old,new);compile(s,str(src),'exec')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines)
text=once(text,"'2026-11-12-v666-dj-force'","'2026-11-12-v667-dj-conversation-log'")
text=once(text,"PROGRAM_VERSION                = 'V666'","PROGRAM_VERSION                = 'V667'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V666'","PROGRAM_RELEASE_LABEL          = 'V667'");compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v667_dj_conversation_log.py';notes=root/'releases/PAFPlayer_v667_dj_conversation_log_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8')
docs=once(docs,'Current release: **V666** — forced DJ overrides sleep; default cast is one woman and one man.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v666_dj_force_release_notes.md).','Current release: **V667** — readable DJ conversation log.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v667_dj_conversation_log_release_notes.md).')
docs=once(docs,'DJ diagnostics are saved as separate append-only JSONL files',r'DJ dialogue and recent artist/title metadata are appended to `C:\logs\PAFPlayer\dj.log` when text is generated, including when voice synthesis later fails or the prepared speech is not played. Entries show local date and time, most recent song first, and gender-marked speaker turns. This log contains listening history and dialogue. A write failure is shown in Help and Warnings; playback continues. In contrast, DJ diagnostics are saved as separate append-only JSONL files')
changelog=root/'docs/PAFPlayer_changelog.md';change=changelog.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V667 — November 12, 2026\n\nAppend generated DJ conversation and recent tracks to a readable local DJ log, with write failures surfaced in Help and Warnings. [Release notes](../releases/PAFPlayer_v667_dj_conversation_log_release_notes.md).\n')
replace(src,s,root/'backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V667 — DJ conversation log\n\nAppend generated dialogue and its recent track context to `C:\\logs\\PAFPlayer\\dj.log`: local date and time, most recent track first, and gender-marked dialogue turns. Entries are logged as soon as text is generated, even if speech later fails or does not play. A log write failure is visible in Help and Warnings and does not interrupt the DJ. The separate diagnostic JSONL still excludes track metadata and dialogue.\n',encoding='utf8')
print('Published V667 workspace player and documentation with verified backups.')
