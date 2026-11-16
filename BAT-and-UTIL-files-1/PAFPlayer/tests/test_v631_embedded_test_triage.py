"""V631 embedded suite keeps known failures visible and detects repairs."""
import contextlib
import io
import unittest
from unittest import mock

import PAFPlayer as player
import PAFPlayer_test_triage as triage


class TriageRunnerTests(unittest.TestCase):
    def test_raw_cli_reaches_unmarked_runner(self):
        with mock.patch.object(player,'run_unit_tests',return_value=7) as run:
            self.assertEqual(7,player.main(['--unit-tests-raw']))
        run.assert_called_once_with(raw=True)

    def test_manifest_is_exact_and_nonempty(self):
        self.assertEqual(57,len(triage.EXPECTED_FAILURES))
        self.assertEqual(39,len(triage.EXPECTED_FAILURE_GROUPS['historical source or layout assertion']))
        self.assertEqual(18,len(triage.EXPECTED_FAILURE_GROUPS['behavior or fixture discrepancy still requiring reassessment']))

    def test_expected_mode_and_raw_mode_both_run_the_test(self):
        class DeliberateLegacyFailure(unittest.TestCase):
            def test_known_failure(self):
                self.fail('historical expectation')
        def suite(*_args):
            return unittest.defaultTestLoader.loadTestsFromTestCase(DeliberateLegacyFailure)
        groups={'fixture': frozenset({'test_known_failure'})}
        errors=io.StringIO()
        with mock.patch.object(player.unittest.defaultTestLoader,'loadTestsFromModule',side_effect=suite), \
             mock.patch.object(triage,'EXPECTED_FAILURES',{'test_known_failure':'fixture'}), \
             mock.patch.object(triage,'EXPECTED_FAILURE_GROUPS',groups), \
             contextlib.redirect_stderr(errors):
            self.assertEqual(0,player.run_unit_tests())
            self.assertEqual(1,player.run_unit_tests(raw=True))
        self.assertIn('expected failure',errors.getvalue())
        self.assertFalse(hasattr(DeliberateLegacyFailure.test_known_failure,
                                 '__unittest_expecting_failure__'))

    def test_newly_passing_expected_test_fails_the_audit(self):
        class Repaired(unittest.TestCase):
            def test_known_failure(self):
                pass
        groups={'fixture': frozenset({'test_known_failure'})}
        with mock.patch.object(player.unittest.defaultTestLoader,'loadTestsFromModule',
                               return_value=unittest.defaultTestLoader.loadTestsFromTestCase(Repaired)), \
             mock.patch.object(triage,'EXPECTED_FAILURES',{'test_known_failure':'fixture'}), \
             mock.patch.object(triage,'EXPECTED_FAILURE_GROUPS',groups), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1,player.run_unit_tests())


if __name__=='__main__': unittest.main()
