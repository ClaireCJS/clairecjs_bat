import hashlib
import json
from pathlib import Path
from pafplayer_v416_edit import ROOT, replace_file, unique

notes = '''# PAFPlayer V429 — circled ten in Windows Terminal

September 22, 2026. Build `2026-09-22-v429-circled-ten-terminal-spacing`.

The screenshot's `all ❿of My ...` collision exposed an omitted glyph: the terminal-only Emojimaxx spacing set ended at ❾, although ten/10/tens map to ❿. The existing test also stopped at nine. Windows Terminal therefore received only the source separator after ❿, without the safety cells used for the other negative circled numbers.

The compatibility set now includes ❿. It receives the same two generated safety cells plus the original word separator, before wrapping, centering and coloring. Sung, scrolling and neighboring lines share this substitution path. The correction is scoped to generated Windows Terminal replacements; literal circled numbers, web/Tk lyrics, existing compound-number spacing and other glyph rules retain their behavior. This release builds on V428 and preserves its shutdown fix and intervening changes.

Validation: the new regression reproduced the screenshot phrase and failed on the original implementation specifically for ten. After the correction, 13 focused tests passed. Coverage includes ten/10/tens, all ten negative circled glyphs across three text styles, sung/neighbor parity, wrapping at exact cell boundaries, all karaoke color treatments, literal glyphs, other surfaces, and existing tens compounds. The older every-digit regression now includes ten. Source compilation passed. No live Windows Terminal pixel comparison was available in this session; these checks verify emitted text and cell accounting, not the user's font rasterization. The full historical suite was not rerun.

Restart PAFPlayer and confirm V429 to load the correction.
'''
replace_file(ROOT/'play_audio_file_v429_release_notes.md',notes)
for rel in ('PAFPlayer_changelog.md','docs/PAFPlayer_changelog.md'):
    path=ROOT/rel
    prefix='../' if rel.startswith('docs/') else ''
    entry=f'''## V429 — September 22, 2026

Added the missing circled ten (❿) to Windows Terminal's generated-number spacing rule, fixing the unprotected gap in `ten of`. Extended the former 1–9 regression through 10 and added screenshot-phrase/wrapping/color tests; 13 focused checks pass. Preserves V428. [Details and verification limits]({prefix}play_audio_file_v429_release_notes.md).

'''
    replace_file(path,path.read_text(encoding='utf-8').replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n'+entry,1))
data=(ROOT/'play_audio_file.py').read_bytes()
compile(data,str(ROOT/'play_audio_file.py'),'exec')
snapshot=unique(ROOT/'play_audio_file_v429_circled_ten_terminal_spacing.py')
snapshot.write_bytes(data)
assert snapshot.read_bytes()==data
manifest={'source':str(ROOT/'play_audio_file.py'),'versioned_source':str(snapshot),'sha256':hashlib.sha256(data).hexdigest(),'installed_before_sha256':hashlib.sha256(Path(r'C:\BAT\play_audio_file.py').read_bytes()).hexdigest()}
replace_file(ROOT/'pafplayer_v429_release_manifest.json',json.dumps(manifest,indent=2))
deploy=(ROOT/'pafplayer_v421_deploy.py').read_text(encoding='utf-8').replace('pafplayer_v421_release_manifest','pafplayer_v429_release_manifest').replace('pafplayer_v421_deployment','pafplayer_v429_deployment')
replace_file(ROOT/'pafplayer_v429_deploy.py',deploy)
print(json.dumps(manifest,indent=2))
