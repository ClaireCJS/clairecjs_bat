from pathlib import Path
from datetime import datetime
import hashlib,json
root=Path(__file__).resolve().parents[3];report=max((root/'tests/reports').glob('v657-dj-checks-*.json'),key=lambda p:p.stat().st_mtime);result=json.loads(report.read_text());source=(root/'PAFPlayer.py').read_bytes();assert result['version']=='V657' and result['sha256']==hashlib.sha256(source).hexdigest()
def update(rel,change,archive):
 p=root/rel;old=p.read_bytes();s=old.decode('utf8');new=change(s).encode('utf8');assert old!=new
 base=p.with_name(p.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'));b=base;n=0
 while b.exists() or (root/archive/b.name).exists():n+=1;b=base.with_name(f'{base.stem} ({n}){base.suffix}')
 with b.open('xb') as f:f.write(old)
 assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(old).digest();assert p.read_bytes()==old
 p.write_bytes(new);assert p.read_bytes()==new;b.rename(root/archive/b.name);print('Modified',p)
def manual(s):
 old='Current release: **V656** — nonblocking console command-entry foundation.\n[Release notes and current limitations](../releases/PAFPlayer_v656_hash_command_foundation_release_notes.md).'
 new='Current release: **V657** — experimental AI Podcaster / DJ.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v657_experimental_ai_dj_release_notes.md).'
 assert s.count(old)==1;s=s.replace(old,new,1)
 old='During playback or pause, type `#` followed by a command, then press Enter or wait 1.5 seconds. Backspace edits and Escape cancels. The command entry is a foundation only: no DJ commands or AI podcaster are implemented yet.'
 new='''During playback or pause, type `#` followed by a command, then press Enter or wait 1.5 seconds. Backspace edits and Escape cancels. `#dj` toggles the AI DJ; `#djforce` requests commentary now. Ctrl+Alt+D retains album-art download / DRCS.

## Experimental AI Podcaster / DJ

The feature is off by default. Open the web configurator’s **Experimental** section to enable it and configure recent-track history (default 10), frequency (2 qualifying tracks), approximate length (90 seconds), and speaker counts (two women by default). Changing either gender count balances the other; increasing the total adds women unless you change the counts. Gender is a requested cast, not a guaranteed characteristic of the provider’s voices.

PAFPlayer prepares a conversation on a background worker from the artist and title of tracks actually heard. It prefetches from the history available at preparation time, so a prepared segment may not include a track completed while it was being generated. It plays at the next eligible track when ready. It pauses music for commentary and resumes only a pause it owns. Pausing, stopping, seeking, or changing tracks cancels the active interruption. A forced request while music is already paused leaves it paused. A forced request needs a played track: the current track becomes eligible after at least three seconds of playback. A forced request joins an existing job; its HUD message reports stages rather than a percentage. Automatic retries stop after a provider failure until settings change or a new force request is made.

OpenAI Responses supplies text and OpenAI Realtime supplies speech by default, using `OPENAI_API_KEY` from the player’s environment. Artist and title information are sent to OpenAI when cloud providers are selected; voice audio is AI-generated. Requests may incur API charges. The key is not entered into or displayed by the web settings. OpenAI speech requires the optional `websocket-client` Python package in the player’s interpreter. The documented Realtime voice presets are selectable in order; they are distinct when enough presets are provided. Accent is an instruction, not a guaranteed voice characteristic.

If cloud text fails, PAFPlayer tries an available local Ollama model (or the configured model). Ollama supplies text only. If cloud speech fails, local speech requires Piper and one or more downloaded `.onnx` voices plus their matching `.onnx.json` files. You can select Ollama-only text and Piper-only speech. Piper model order controls speaker voices; models repeat when fewer are supplied than speakers. The web section shows whether the executable and configured voice model files are found; detection does not prove they work.

To set up Piper, follow the [Piper installation and voice-download guide](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md), using a new, empty environment and model directory so existing files are not overwritten. For example, `en_US-lessac-medium` contains a 63.2 MB ONNX model and a small JSON configuration; Piper and its dependencies are additional. Enter the resulting `piper.exe` path and full ONNX model paths in the web settings. Model licences and accents vary; consult the chosen model’s card. A running Ollama server with at least one downloaded model is separately required for local text.

Generated commentary WAVs are retained in uniquely named `PAFPlayer commentary` folders under the system temporary directory; they are not silently deleted. Speech currently uses FFplay’s default output device, which can differ from the configured music output. Provider and synthesis failures are shown without stopping music. V657’s cloud and Piper paths passed mocked tests but could not be verified live on this machine: the OpenAI request was unreachable, Ollama was not responding, and Piper was not installed.'''
 assert s.count(old)==1;return s.replace(old,new,1)
def changelog(s):
 head='# PAFPlayer changelog\n\n';assert s.startswith(head)
 return head+'''## V657 — November 11, 2026

Add opt-in AI Podcaster / DJ mode with nonblocking preparation, `#dj` and
`#djforce`, Experimental settings, transport-aware interruption, OpenAI and
Ollama text, and OpenAI Realtime / local Piper speech paths. Provider access
and actual Piper synthesis remain unverified live on this machine.
[Release notes](../releases/PAFPlayer_v657_experimental_ai_dj_release_notes.md).

'''+s[len(head):]
update('docs/README.md',manual,'docs');update('docs/PAFPlayer_changelog.md',changelog,'backups')
release=root/'releases/PAFPlayer_v657_experimental_ai_dj.py'
with release.open('xb') as f:f.write(source)
assert release.read_bytes()==source
notes=root/'releases/PAFPlayer_v657_experimental_ai_dj_release_notes.md'
with notes.open('x',encoding='utf8',newline='\n') as f:f.write(f'''# PAFPlayer V657 — experimental AI Podcaster / DJ

The opt-in DJ prepares dialogue about recently heard track metadata in the background. `#dj` toggles it; `#djforce` requests or joins preparation and reports stages. The web **Experimental** section controls timing, cast, models, voices, accent instructions, and local fallback paths. Music resumes only when the DJ owned its pause. Explicit transport changes cancel the interruption.

OpenAI Responses and Realtime are the primary paths. Ollama provides local text fallback; Piper is the separate local speech fallback. The UI discloses cloud track-data sharing and AI-generated speech and links to Piper setup. No keys are displayed or stored in DJ settings. Output files are retained under the system temporary directory. FFplay uses its default output device for commentary.

## Verification

- 22 DJ tests and seven command-entry tests pass, including mocked provider failure, cancellation, settings security, and actual player pause/resume simulations.
- Player and 28 bundled modules compile; all 28 editable sources match their bundles; nine generated JavaScript blocks pass syntax checks.
- Three selected existing tests were compared against V656: the same web-pause source-contract test fails in both, while the other two pass.
- [Test report](../tests/reports/{report.name}); source SHA-256 `{result['sha256']}`.

## Limitations

Cloud calls were unreachable in the live smoke test. Ollama was not responding, and Piper was not installed; neither fallback was verified with real synthesis. The Realtime and Piper paths use mocked tests, and `websocket-client` is an optional dependency. Piper installation is manual through the linked guide. Provider voices do not guarantee gender or accent, and a prefetched segment reflects the history at preparation time. No literal C:\\BAT path was changed.
''')
print('Created',release,notes)
