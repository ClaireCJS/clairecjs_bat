"""Use the established encoder for exact full-frame row strings; verified backup first."""
import ast
import hashlib
from prepare_v642_artwork_chrome import ROOT,write

p=ROOT/'PAFPlayer.py';source=p.read_text(encoding='utf8')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='5768b4c8bda0173248785406c627a9305ad49bc45a00557bfde6d9b4f94f0670'
helper='''def _visualizer_native_full_art_lines(packed_rows, omit_erase_eol):
    """Reuse the native encoder, preserving the legacy full-row strings exactly."""
    if (not packed_rows or _visualizer_numpy() is None
            or _visualizer_artwork_encoder() is None):
        return None
    width = len(packed_rows[0])
    if not width or width % 7 or any(not isinstance(row, bytes) or len(row) != width for row in packed_rows):
        return None
    try:
        # The native ABI requires a nonempty origin. Its temporary CR/CUP is
        # stripped in memory; the caller retains all original row positioning.
        encoded, _runs = _visualizer_packed_art_delta(packed_rows, None, ["\\r"] * len(packed_rows))
        end = "\\033(B\\033[0m"
        parts = encoded.split(end)
        prefix = "\\r\\033[1G"
        if len(parts) != len(packed_rows) + 1 or parts[-1] or any(not part.startswith(prefix) for part in parts[:-1]):
            return None
        suffix = end + ("" if omit_erase_eol else "\\033[K")
        return [part[len(prefix):] + suffix for part in parts[:-1]]
    except (AttributeError, OSError, ValueError):
        return None


'''
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_visualizer_native_rows_output')
lines=source.splitlines(True);body=''.join(lines[node.lineno-1:node.end_lineno])
start=body.index('    lines = []\n');end=body.index('    if rows_out is not None:',start)
old=body[start:end]
body=body[:start]+'    lines = _visualizer_native_full_art_lines(packed_rows, omit_erase_eol)\n    if lines is None:\n'+''.join('    '+line for line in old.splitlines(True))+body[end:]
source=''.join(lines[:node.lineno-1])+helper+body+''.join(lines[node.end_lineno:])
for a,b in (("'2026-11-11-v653-native-poll-retention-idle-art-music-dance'","'2026-11-11-v654-native-full-frames'"),("PROGRAM_VERSION                = 'V653'","PROGRAM_VERSION                = 'V654'"),("PROGRAM_RELEASE_LABEL          = 'V653'","PROGRAM_RELEASE_LABEL          = 'V654'")):
    assert source.count(a)==1;source=source.replace(a,b,1)
compile(source,str(p),'exec');write('PAFPlayer.py',source)
