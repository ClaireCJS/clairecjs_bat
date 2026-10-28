"""Mark only verified TODO items; retain a verified backup at each checkpoint."""
from pafplayer_v416_edit import ROOT, replace_file

def complete(*starts):
    path=ROOT/'PAFPlayer_TODO.md'; text=path.read_text(encoding='utf-8')
    for start in starts:
        needle='- [ ] '+start
        assert text.count(needle)==1, (start,text.count(needle))
        text=text.replace(needle,'- [x] '+start,1)
    replace_file(path,text)
    for rel in ('docs/PAFPlayer/PAFPlayer_TODO.md',):
        replace_file(ROOT/rel,text)

if __name__=='__main__':
    complete('When reporting `Saved Developer’s Choice', 'If `C:\\BAT\\PAFPlayer.py` exists', 'Before replacing the existing `.dcc` file', 'Restore the terminal cursor color')
