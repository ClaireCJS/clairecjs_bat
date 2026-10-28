"""Private FFmpeg setup is explicit, hash-checked, and path-safe."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import PAFPlayer_ffmpeg_setup as setup


def make_zip(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return output.getvalue()


class FFmpegSetupTests(unittest.TestCase):
    def test_explicit_consent_precedes_network_and_disk_changes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / 'private'
            with self.assertRaises(InterruptedError):
                setup.install('https://example.test/ffmpeg.zip', 'a' * 64,
                              confirm=lambda _prompt: 'NO',
                              opener=lambda *_a, **_kw: self.fail('opened without consent'), root=root)
            self.assertFalse(root.exists())

    def test_validated_zip_is_installed_privately_and_rescanned(self):
        data = make_zip({'ffmpeg-package/bin/ffmpeg.exe': b'ffmpeg',
                         'ffmpeg-package/bin/ffplay.exe': b'ffplay',
                         'ffmpeg-package/LICENSE.txt': b'license'})
        digest = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as raw, patch.object(setup, '_version', return_value='ffmpeg version test'):
            root = Path(raw) / 'support'
            opened = []
            def opener(url, timeout):
                opened.append(url)
                return io.BytesIO(data)
            result = setup.install('https://example.test/build.zip', digest,
                                   confirm=lambda _prompt: 'YES', opener=opener, root=root)
            self.assertEqual(1, len(opened))
            self.assertEqual('ffmpeg version test', result['version'])
            bin_dir = Path(result['path'])
            self.assertEqual(b'ffmpeg', (bin_dir / 'ffmpeg.exe').read_bytes())
            self.assertEqual(b'ffplay', (bin_dir / 'ffplay.exe').read_bytes())
            self.assertEqual(digest, json.loads((root / digest / 'manifest.json').read_text())['sha256'])
            self.assertEqual(bin_dir / 'ffmpeg.exe', setup.private_binary('ffmpeg', root))
            second = setup.install('https://example.test/build.zip', digest,
                                   confirm=lambda _prompt: 'YES', opener=opener, root=root)
            self.assertTrue(second['already_installed'])
            self.assertEqual(1, len(opened))

    def test_zip_path_escape_is_rejected(self):
        data = make_zip({'../outside.exe': b'bad'})
        with tempfile.TemporaryDirectory() as raw:
            archive = Path(raw) / 'archive.zip'
            archive.write_bytes(data)
            with self.assertRaises(ValueError):
                setup._safe_extract(archive, Path(raw) / 'payload')
            self.assertFalse((Path(raw).parent / 'outside.exe').exists())

    def test_source_requires_https_and_complete_digest(self):
        for source, digest in [('http://example.test/build.zip', 'a' * 64),
                               ('https://user:pass@example.test/build.zip', 'a' * 64),
                               ('https://example.test/build.zip', 'short')]:
            with self.subTest(source=source, digest=digest), self.assertRaises(ValueError):
                setup._validate_source(source, digest)


if __name__ == '__main__':
    unittest.main()
