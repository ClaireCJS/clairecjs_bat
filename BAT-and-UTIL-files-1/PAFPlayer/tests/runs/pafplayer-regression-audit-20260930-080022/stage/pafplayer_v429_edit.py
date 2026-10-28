from pafplayer_v416_edit import ROOT, edit, sub, replace_file

def transform(s):
    s = sub(s, '2026-09-22-v428-fast-ctrl-break-shutdown', '2026-09-22-v429-circled-ten-terminal-spacing')
    s = sub(s, '"V428"', '"V429"', 2)
    s = sub(s, 'WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS = "❶❷❸❹❺❻❼❽❾"',
               'WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS = "❶❷❸❹❺❻❼❽❾❿"')
    s = sub(s, '''    cell after a negative circled digit.  Existing one-digit behavior remains
    unchanged.  V390 additionally recognizes a tens compound such as ``❹⓿``''', '''    cell after a negative circled number. V429 includes the last member, ❿:
    ten is one glyph too and needs the same safety cells as ❶ through ❾.
    V390 additionally recognizes a tens compound such as ``❹⓿``''')
    return s

edit(transform)
path = ROOT / 'test_play_audio_file_v416.py'
s = sub(path.read_text(encoding='utf-8'), '        for number in range(1, 10):', '        for number in range(1, 11):')
replace_file(path, s)
