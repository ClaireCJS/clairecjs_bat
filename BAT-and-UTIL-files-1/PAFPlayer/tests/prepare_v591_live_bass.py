"""One-time V590 -> V591 source update with verified replacement backup."""
from pathlib import Path
import hashlib
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'monkeymote/research'))
from edit_v568 import write

path = root / 'PAFPlayer.py'
assert hashlib.sha256(path.read_bytes()).hexdigest() == '6bf1a41c0dae1fb02572596beb61ffd1c801d4b0a08641a3b463da689e718aab'
source = path.read_text(encoding='utf-8')
def change(before, after):
    global source
    assert source.count(before) == 1, (before[:120], source.count(before))
    source = source.replace(before, after, 1)

change("'2026-10-20-v590-locked-bass-session-detection'", "'2026-10-21-v591-live-bass-transitions'")
change("PROGRAM_VERSION                = 'V590'", "PROGRAM_VERSION                = 'V591'")
change("PROGRAM_RELEASE_LABEL          = 'V590'", "PROGRAM_RELEASE_LABEL          = 'V591'")
# Only the buffered renderer opts into a private interactive filter pipe.
start = source.index('def matrixmixer_inspired_ffmpeg_command(')
end = source.index('\ndef matrixmixer_read_pcm_block', start)
block = source[start:end]
block = block.replace('    session_locked: bool | None = None,',
                      '    session_locked: bool | None = None,\n    live_bass: bool = False,')
block = block.replace('str(executable), "-nostdin",', 'str(executable), "-stdin" if live_bass else "-nostdin",')
block = block.replace('    if not math.isclose(bass_db, 0.0, abs_tol=1e-12):\n        filters.append(f"bass=g={bass_db:.3g}:f=120:w=0.7")',
'''    if live_bass:
        # Retain the named filter even at unity so lock/unlock can change gain
        # in this decoder. Placement before expansion preserves LFE semantics.
        filters.append(f"bass@paf_bass=g={bass_db:.3g}:f=120:w=0.7")
    elif not math.isclose(bass_db, 0.0, abs_tol=1e-12):
        filters.append(f"bass=g={bass_db:.3g}:f=120:w=0.7")''')
source = source[:start] + block + source[end:]
change('        self._live_volume = min(400, max(0, int(initial_volume)))',
'''        self._live_volume = min(400, max(0, int(initial_volume)))
        self._bass_command_lock = threading.Lock()
        self._live_bass = "-stdin" in command and any("bass@paf_bass=" in part for part in command)
        self._last_bass_db = None''')
start = source.index('class MatrixMixerInspiredWaveOutProcess:')
end = source.index('class MultiOutputWaveOutProcess:', start)
block = source[start:end].replace('stdin=subprocess.DEVNULL,', 'stdin=subprocess.PIPE if self._live_bass else subprocess.DEVNULL,', 1)
source = source[:start] + block + source[end:]
change('    def set_volume(self, volume: int) -> bool:\n        """The owner updates gain without disturbing the active PCM pump."""',
'''    def set_bass_db(self, gain: float) -> bool:
        """Change FFmpeg's existing shelf without resetting PCM or WaveOut.

        FFmpeg's interactive `c` command accepts a complete newline-terminated
        command on its private stdin pipe, including on Windows without a console.
        No stdin from the user's terminal is inherited. Numeric input is bounded;
        duplicate requests do not accumulate while the decoder is backpressured.
        """
        try:
            gain = float(gain)
            if not math.isfinite(gain):
                return False
            gain = max(-20.0, min(20.0, gain))
            with self._bass_command_lock:
                if not self._live_bass or self._stop.is_set() or self._ffmpeg.poll() is not None:
                    return False
                if gain != self._last_bass_db:
                    self._ffmpeg.stdin.write(f"cbass@paf_bass -1 gain {gain:.3g}\\n".encode("ascii"))
                    self._ffmpeg.stdin.flush()
                    self._last_bass_db = gain
            return True
        except (OSError, ValueError, TypeError):
            return False

    def set_volume(self, volume: int) -> bool:
        """The owner updates gain without disturbing the active PCM pump."""''')
change('''        finally:
            self._pending_headers = ()
            remove_matrix_output_levels(self._meter_source_id)''',
'''        finally:
            self._pending_headers = ()
            with self._bass_command_lock:
                with contextlib.suppress(OSError, ValueError, AttributeError):
                    self._ffmpeg.stdin.close()
            remove_matrix_output_levels(self._meter_source_id)''')
change('''                if isinstance(message, dict) and "paused" in message:
                    for process in tuple(processes):''',
'''                if isinstance(message, dict) and "bass_db" in message:
                    for process in tuple(processes):
                        process.set_bass_db(message["bass_db"])
                if isinstance(message, dict) and "paused" in message:
                    for process in tuple(processes):''')
change('''    def wait_primed(self, timeout: float = 3.0) -> bool:
        return self._primed.wait(timeout) and self.poll() is None''',
'''    def set_bass_db(self, gain: float) -> bool:
        """Keep the audio worker, decoder, device queue and sample clock intact."""
        if self._stop_sent or self.poll() is not None:
            return False
        try:
            gain = float(gain)
            if not math.isfinite(gain):
                return False
            self._process.stdin.write(json.dumps({"bass_db": max(-20.0, min(20.0, gain))}) + "\\n")
            self._process.stdin.flush()
            return True
        except (OSError, ValueError, TypeError):
            return False

    def wait_primed(self, timeout: float = 3.0) -> bool:
        return self._primed.wait(timeout) and self.poll() is None''')
change('''        output_rate, output_bit_depth, end_seconds=end_seconds, replaygain_info=replaygain_info,
    )
    command = apply_external_resume_fade''',
'''        output_rate, output_bit_depth, end_seconds=end_seconds, replaygain_info=replaygain_info,
        live_bass=True,
    )
    command = apply_external_resume_fade''')
change('''            restart_required = current_db != previous_db
            # Seed the monitor too: one audible change must not restart twice.''',
'''            restart_required = current_db != previous_db
            if restart_required and getattr(process, "set_bass_db", lambda _db: False)(current_db):
                restart_required = False
            # Seed the monitor too: one audible change must not apply twice.''')
change('''                # FFplay filters are immutable after launch.  Poll at one hertz
                # (not on the render path) and reconstruct only when a user who
                # enabled sleep bass crosses the Windows lock boundary.''',
'''                # Poll lock state at one hertz. The buffered renderer changes
                # its existing FFmpeg filter through a private command pipe;
                # legacy FFplay retains the same-position restart fallback.''')
change('''                    if bass_filter_changed:
                        resume_after_pause = True  # Short interactive preroll for an audible filter change.''',
'''                    if bass_filter_changed and not getattr(process, "set_bass_db", lambda _db: False)(bass_filter_signature):
                        resume_after_pause = True  # Legacy FFplay fallback only.''')
compile(source, str(path), 'exec')
write('PAFPlayer.py', source)
