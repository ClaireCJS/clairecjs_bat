import contextlib
import io
import unittest

import audit_music_batch as audit


class V193FinalAuditVerificationTests(unittest.TestCase):
    def test_clean_fresh_scan_prints_unmistakable_completion(self) -> None:
        verification = {
            "counts": {"files": 87},
            "findings": [
                {"severity": "info", "category": "context", "path": "note.txt"}
            ],
        }
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = audit.print_final_audit_verification(
                verification,
                action_failures=0,
                waveform_result={"failed": [], "problems": []},
                waveform_handoff_failed=False,
                use_color=False,
            )
        rendered = output.getvalue()
        self.assertTrue(status["complete"])
        self.assertIn("AUDIT COMPLETE", rendered)
        self.assertIn("Final fresh verification examined 87 files", rendered)
        self.assertIn("returning to the shell", rendered)

    def test_remaining_finding_cannot_be_mistaken_for_clean_completion(self) -> None:
        verification = {
            "counts": {"files": 15},
            "findings": [
                {
                    "severity": "safe_fix",
                    "category": "missing_replaygain",
                    "path": "album",
                },
                {
                    "severity": "ask_first",
                    "category": "missing_plain_lyrics",
                    "path": "track.flac",
                },
            ],
        }
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = audit.print_final_audit_verification(
                verification,
                action_failures=0,
                waveform_result={"failed": [], "problems": []},
                waveform_handoff_failed=False,
                use_color=False,
            )
        rendered = output.getvalue()
        self.assertFalse(status["complete"])
        self.assertIn("AUDIT FINISHED — MORE WORK REMAINS", rendered)
        self.assertIn("1 fixes", rendered)
        self.assertIn("1 review items", rendered)
        self.assertIn("has not converged", rendered)


if __name__ == "__main__":
    unittest.main()
