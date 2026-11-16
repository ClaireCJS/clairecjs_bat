"""Remove bulk registry reads from the periodic frame-loop status publication."""
import hashlib
from prepare_v642_artwork_chrome import ROOT, write

path=ROOT/'PAFPlayer.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='9c0c52dddcb8b6971cf8c269b67703e1de33fe12ee75c6d7e7d28245cf6beb65'
source=path.read_text(encoding='utf-8')
for before,after in (
    ("PROGRAM_VERSION                = 'V646'", "PROGRAM_VERSION                = 'V647'"),
    ("PROGRAM_RELEASE_LABEL          = 'V646'", "PROGRAM_RELEASE_LABEL          = 'V647'"),
    ("'2026-11-09-v646-karaoke-render-load'", "'2026-11-09-v647-status-publication-stalls'"),
    ('                        console_title_style=int(load_player_settings().get("ConsoleTitleStyle", 1)),',
     '                        # Use the live values already updated by controls/defaults.\n'
     '                        # Re-reading every saved setting here releases/reacquires\n'
     '                        # the GIL hundreds of times, stalling frames under lyric load.\n'
     '                        console_title_style=console_title_style,'),
    ('                        console_title_content=int(load_player_settings().get("ConsoleTitleContent", 1)),',
     '                        console_title_content=console_title_content,'),
):
    assert source.count(before)==1,before
    source=source.replace(before,after,1)
compile(source,str(path),'exec')
write('PAFPlayer.py',source)
