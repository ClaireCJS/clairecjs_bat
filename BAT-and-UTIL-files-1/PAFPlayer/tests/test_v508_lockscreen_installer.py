"""Regression checks for the Windows 10 lock-screen companion installer."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lockscreen" / "lockscreen_installer.py"
SPEC = importlib.util.spec_from_file_location("paf_lockscreen_installer", SOURCE)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class FakeBackend:
    def __init__(self, *, installed="", trusted=False, uac_enabled=True, publication=True, activation=True):
        self.version = installed
        self.has_trust = trusted
        self.has_uac = uac_enabled
        self.calls = []
        self.publication = publication
        self.activation = activation

    def signature_matches(self, package, certificate):
        self.calls.append("signature")

    def installed_version(self):
        self.calls.append("query")
        return self.version

    def uac_enabled(self):
        self.calls.append("uac-query")
        return self.has_uac

    def trusted(self):
        self.calls.append("trust-query")
        return self.has_trust

    def elevate_certificate_import(self, certificate):
        self.calls.append("trust-import")
        self.has_trust = True

    def register(self, package, dependencies):
        self.calls.append("register")
        assert dependencies == ()
        self.version = installer.PACKAGE_VERSION

    def verify_publication(self, root):
        self.calls.append("publication")
        if not self.activation:
            raise installer.InstallerError("0x80270254")
        return {"package": installer.PACKAGE_NAME + "_" + installer.PACKAGE_VERSION + "_x64__vz06efybxc4j2",
                "enabled": True, "published": self.publication, "officialVerified": True,
                "backgroundAccess": "AllowedSubjectToSystemPolicy", "backgroundRegistered": True,
                "backgroundRegistrationError": ""}

    def activate(self, args):
        self.calls.append("activate")
        return 123

    def verify_background_server(self):
        self.calls.append("background-activation")


class LockScreenInstallerTests(unittest.TestCase):
    def setUp(self):
        self.windows = mock.patch.object(installer, "require_windows_10")
        self.windows.start()
        self.addCleanup(self.windows.stop)

    def run_install(self, backend, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = installer.install(ROOT / "lockscreen", backend, **kwargs)
        return result, output.getvalue()

    def test_artifacts_include_packaged_runtime_and_lock_screen_manifest(self):
        paths = installer.artifacts(ROOT / "lockscreen")
        self.assertEqual(paths[2], ())
        installer.validate_artifacts(*paths)

    def test_explicit_trust_consent_then_registers_for_current_user(self):
        backend = FakeBackend()
        result, output = self.run_install(backend, ask=lambda _: "yes")
        self.assertEqual(result, 0)
        self.assertEqual(backend.calls.count("trust-import"), 1)
        self.assertEqual(backend.calls.count("register"), 1)
        self.assertLess(backend.calls.index("trust-import"), backend.calls.index("register"))
        self.assertIn(f"Verified: V{installer.PACKAGE_VERSION.split('.')[0]} activated and submitted", output)
        self.assertLess(backend.calls.index("publication"), backend.calls.index("activate"))
        self.assertLess(backend.calls.index("background-activation"), backend.calls.index("activate"))
        self.assertIn("Choose one app to show detailed status", output)

    def test_no_consent_changes_nothing(self):
        backend = FakeBackend()
        result, output = self.run_install(backend, ask=lambda _: "no")
        self.assertEqual(result, 2)
        self.assertNotIn("trust-import", backend.calls)
        self.assertNotIn("register", backend.calls)
        self.assertIn("No certificate trust or app registration was changed", output)

    def test_pretrusted_certificate_installs_without_prompt(self):
        backend = FakeBackend(trusted=True)
        result, _ = self.run_install(backend, ask=lambda _: self.fail("unexpected prompt"))
        self.assertEqual(result, 0)
        self.assertNotIn("trust-import", backend.calls)
        self.assertIn("register", backend.calls)

    def test_check_only_never_installs(self):
        backend = FakeBackend()
        result, output = self.run_install(backend, check_only=True)
        self.assertEqual(result, 1)
        self.assertNotIn("trust-query", backend.calls)
        self.assertNotIn("register", backend.calls)
        self.assertIn("installed version: none", output)

    def test_installed_package_is_not_replaced(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
        result, _ = self.run_install(backend)
        self.assertEqual(result, 0)
        self.assertNotIn("register", backend.calls)
        self.assertIn("publication", backend.calls)

    def test_v528_is_upgraded_without_retrusting_certificate(self):
        backend = FakeBackend(installed="528.0.0.0", trusted=True)
        result, output = self.run_install(backend)
        self.assertEqual(result, 0)
        self.assertIn("register", backend.calls)
        self.assertNotIn("trust-import", backend.calls)
        self.assertIn(f"Installing the V{installer.PACKAGE_VERSION.split('.')[0]} desktop publisher", output)

    def test_disabled_uac_does_not_block_real_publication_test(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, uac_enabled=False, trusted=True)
        result, output = self.run_install(backend)
        self.assertEqual(result, 0)
        self.assertIn("EnableLUA=0", output)
        self.assertNotIn("register", backend.calls)
        self.assertIn("publication", backend.calls)
        self.assertNotIn("Enable UAC", output)

    def test_healthy_registration_cannot_hide_activation_failure(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True, activation=False)
        with self.assertRaisesRegex(installer.InstallerError, "0x80270254"):
            self.run_install(backend)
        self.assertNotIn("activate", backend.calls)

    def test_successful_activation_cannot_hide_publication_failure(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True, publication=False)
        with self.assertRaisesRegex(installer.InstallerError, "publication failed"):
            self.run_install(backend)

    def test_read_only_check_never_publishes_even_when_installed(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
        result, output = self.run_install(backend, check_only=True)
        self.assertEqual(result, 0)
        self.assertNotIn("publication", backend.calls)
        self.assertNotIn("activate", backend.calls)
        self.assertIn("publication were not tested", output)

    def test_refuses_newer_version_downgrade(self):
        with self.assertRaisesRegex(installer.InstallerError, "newer companion"):
            self.run_install(FakeBackend(installed="999.0.0.0", trusted=True))

    def test_notification_success_does_not_hide_background_failure(self):
        for change in ({"backgroundRegistered": False}, {"backgroundAccess": "DeniedByUser"},
                       {"backgroundRegistrationError": "registration failed"}, {"backgroundDiagnosticError": "query failed"}):
            with self.subTest(change=change):
                backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
                original = backend.verify_publication
                backend.verify_publication = lambda root: {**original(root), **change}
                with self.assertRaisesRegex(installer.InstallerError, "background registration is not ready"):
                    self.run_install(backend)
                self.assertNotIn("activate", backend.calls)

    def test_registered_task_does_not_hide_com_activation_failure(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
        backend.verify_background_server = mock.Mock(side_effect=installer.InstallerError("COM access denied"))
        with self.assertRaisesRegex(installer.InstallerError, "COM access denied"):
            self.run_install(backend)
        self.assertNotIn("activate", backend.calls)

    def test_wrong_identity_in_receipt_is_rejected(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
        backend.verify_publication = lambda root: {"package": "Wrong", "published": True}
        with self.assertRaisesRegex(installer.InstallerError, "expected package identity"):
            self.run_install(backend)

    def test_saved_disabled_setting_is_preserved(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
        original = backend.verify_publication
        backend.verify_publication = lambda root: {**original(root), "enabled": False, "published": False,
                                                   "backgroundRegistered": False, "backgroundAccess": "Unspecified"}
        result, output = self.run_install(backend)
        self.assertEqual(result, 0)
        self.assertIn("remains disabled", output)
        self.assertNotIn("background-activation", backend.calls)

    def test_unreachable_player_starts_offline_publisher(self):
        backend = FakeBackend(installed=installer.PACKAGE_VERSION, trusted=True)
        original = backend.verify_publication
        backend.verify_publication = lambda root: {**original(root), "officialVerified": False}
        result, output = self.run_install(backend)
        self.assertEqual(result, 0)
        self.assertIn("offline status", output)
        self.assertIn("activate", backend.calls)

    def test_changed_package_is_rejected_before_windows_changes(self):
        package, certificate, dependencies = installer.artifacts(ROOT / "lockscreen")
        real_sha = installer.sha256
        with mock.patch.object(installer, "sha256", side_effect=lambda p: "0" * 64 if p == package else real_sha(p)):
            with self.assertRaisesRegex(installer.InstallerError, "differs from the verified"):
                installer.validate_artifacts(package, certificate, dependencies)

    def test_powershell_paths_are_literal_and_command_is_encoded(self):
        path = "C:\\Users\\A'B\\file.msix"
        quoted = installer.ps_literal(path)
        self.assertEqual(quoted, "'C:\\Users\\A''B\\file.msix'")
        args = installer.ps_args("Write-Output " + quoted)
        import base64
        decoded = base64.b64decode(args[-1]).decode("utf-16le")
        self.assertIn("$env:PSModulePath", decoded)
        self.assertTrue(decoded.endswith("Write-Output " + quoted))

    def test_recovery_upgrade_targets_only_recovery_package(self):
        backend = installer.WindowsBackend()
        backend.run_ps = mock.Mock(return_value="")
        package, _, runtime = installer.artifacts(ROOT / "lockscreen")
        backend.register(package, runtime)
        command = backend.run_ps.call_args.args[0]
        self.assertIn("-ForceTargetApplicationShutdown", command)
        self.assertNotIn("Remove-AppxPackage", command)
        self.assertNotIn("-ExternalLocation", command)
        backend.installed_version()
        self.assertIn("-Name 'ClaireCJS.PAFPlayer.LockScreen.Recovery'", backend.run_ps.call_args.args[0])

    def test_manual_steps_identify_recovery_in_both_slots(self):
        result, output = self.run_install(FakeBackend(trusted=True))
        self.assertEqual(result, 0)
        self.assertIn(f"select {installer.PACKAGE_DISPLAY_NAME}", output)
        self.assertIn(f"Select {installer.PACKAGE_DISPLAY_NAME} again for a quick-status slot", output)
        self.assertIn("different app", output)


if __name__ == "__main__":
    unittest.main()
