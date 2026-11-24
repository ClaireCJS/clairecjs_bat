"""Exercise the installed decoder against synthetic audio, never user music."""
from pathlib import Path
import shutil
import tempfile
import unittest
import wave

import audit_music_batch as audit


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg not installed")
class DecodeIntegrationTests(unittest.TestCase):
    def test_real_decoder_accepts_pcm_and_rejects_invalid_flac(self):
        root = Path(tempfile.mkdtemp(prefix="audit-decode-test-"))
        valid = root / "valid.wav"
        with wave.open(str(valid), "wb") as audio:
            audio.setnchannels(2)
            audio.setsampwidth(2)
            audio.setframerate(44100)
            audio.writeframes(b"\x00" * 44100 * 4)
        audit.validate_audio_decode(valid, shutil.which("ffmpeg"), visible=False)
        invalid = root / "invalid.flac"
        invalid.write_bytes(b"fLaC" + b"invalid audio data" * 50)
        with self.assertRaisesRegex(RuntimeError, "Audio integrity check failed"):
            audit.validate_audio_decode(invalid, shutil.which("ffmpeg"), visible=False)
        self.assertEqual(invalid.read_bytes(), b"fLaC" + b"invalid audio data" * 50)


if __name__ == "__main__":
    unittest.main()
