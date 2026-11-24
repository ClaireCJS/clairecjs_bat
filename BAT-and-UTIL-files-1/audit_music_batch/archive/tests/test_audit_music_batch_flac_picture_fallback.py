import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_music_batch as audit


def u32(value):
    return struct.pack(">I", value)


def picture_block(data, mime=b"application/x-unknown", kind=3, desc=b"cover"):
    body = u32(kind) + u32(len(mime)) + mime + u32(len(desc)) + desc
    body += u32(1) * 4 + u32(len(data)) + data
    return bytes([0x86]) + len(body).to_bytes(3, "big") + body


def flac_with_picture(data):
    return b"fLaC" + b"\x00\x00\x00\x00" + picture_block(data)


class FlacPictureFallbackTests(unittest.TestCase):
    def test_direct_flac_block_reader_recovers_bytes_and_sniffs_mime(self):
        jpeg = b"\xff\xd8\xffpayload"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cover.flac"
            path.write_bytes(flac_with_picture(jpeg))
            found = audit.flac_picture_blocks(path)
        self.assertEqual([(jpeg, "image/jpeg", 3, "cover")], found)

    def test_embedded_picture_reader_falls_back_when_mutagen_cannot_load_art(self):
        png = b"\x89PNG\r\n\x1a\nimage"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "track.flac"
            path.write_bytes(flac_with_picture(png))
            with mock.patch.object(audit, "mutagen_file", side_effect=ValueError("bad picture")):
                found = audit.embedded_pictures(path)
        self.assertEqual([(png, "image/png", 3, "cover")], found)

    def test_truncated_picture_block_is_ignored(self):
        malformed = bytes([0x86 | 0x80]) + (4).to_bytes(3, "big") + b"oops"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.flac"
            path.write_bytes(b"fLaC" + malformed)
            self.assertEqual([], audit.flac_picture_blocks(path))


if __name__ == "__main__":
    unittest.main()
