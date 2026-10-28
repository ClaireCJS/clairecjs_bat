"""Install the PAFPlayer Windows 10 lock-screen status companion.

Run from the interactive Windows account that should see the lock-screen status.
Only certificate trust is elevated; AppX registration stays in that account.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile


PACKAGE_NAME = "ClaireCJS.PAFPlayer.LockScreen.Recovery"
PACKAGE_VERSION = "530.0.0.0"
PACKAGE_DISPLAY_NAME = "PAFPlayer Lock Screen V530"
PACKAGE_FAMILY = "ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2"
CERT_THUMBPRINT = "08AC642F1C17B503BC857189AE8C78E76B3358EC"
PACKAGE_FILE = "PAFPlayerLockScreen_v530_x64.msix"
RUNTIME_FILE = "PAFPlayerLockScreen.exe"
CERT_FILE = "PAFPlayerLockScreen_v505.cer"
DEPENDENCIES = ()  # Uses Windows' .NET Framework, not the UWP .NET Native runtime.
EXPECTED_SHA256 = {
    PACKAGE_FILE: "1436ce789ae6ac09b4a67e0ea25f37aabf716abfed21f2fdb67b0037171c6669",
    RUNTIME_FILE: "dad0ab47511b5cf9dba9cd07db5b271150ad3ba887e4607ec8d0ad371b622f8c",
    CERT_FILE: "ada1449f903cdd9eba33578400d81ad612374da12fcf300b059d3e39c1ed1fc2",
}
FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
UAP10 = UAP + "/10"
COM = "http://schemas.microsoft.com/appx/manifest/com/windows10"
BACKGROUND_CLSID = "12BF3FEC-09DF-41BB-BB38-9881E610AA91"


class InstallerError(RuntimeError):
    pass


def artifacts(root: Path) -> tuple[Path, Path, tuple[Path, ...]]:
    dist = root / "dist"
    release = dist / "v530"
    return release / PACKAGE_FILE, dist / CERT_FILE, ()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_artifacts(package: Path, certificate: Path, dependencies: tuple[Path, ...]) -> None:
    for path in (package, certificate, *dependencies):
        if not path.is_file():
            raise InstallerError(f"Missing installation file: {path}")
        expected = EXPECTED_SHA256.get(path.name)
        if not expected or sha256(path) != expected:
            raise InstallerError(f"File differs from the verified V530 build: {path}")
    try:
        with zipfile.ZipFile(package) as archive:
            manifest = ET.fromstring(archive.read("AppxManifest.xml"))
            if "AppxSignature.p7x" not in archive.namelist():
                raise InstallerError("The identity package is not signed.")
            if hashlib.sha256(archive.read(RUNTIME_FILE)).hexdigest() != EXPECTED_SHA256[RUNTIME_FILE]:
                raise InstallerError("The packaged runtime differs from the verified V530 build.")
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as error:
        raise InstallerError(f"Invalid package manifest: {error}") from error
    identity = manifest.find(f"{{{FOUNDATION}}}Identity")
    app = manifest.find(f"{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application")
    visual = app.find(f"{{{UAP}}}VisualElements") if app is not None else None
    lockscreen = visual.find(f"{{{UAP}}}LockScreen") if visual is not None else None
    server = app.find(f"{{{FOUNDATION}}}Extensions/{{{COM}}}Extension/{{{COM}}}ComServer/{{{COM}}}ExeServer") if app is not None else None
    background_class = server.find(f"{{{COM}}}Class") if server is not None else None
    if (identity is None or identity.get("Name") != PACKAGE_NAME or
            identity.get("Version") != PACKAGE_VERSION or
            identity.get("Publisher") != "CN=PAFPlayerLocal" or
            identity.get("ProcessorArchitecture") != "x64" or
            app is None or app.get("Id") != "App" or
            app.get("Executable") != RUNTIME_FILE or
            app.get(f"{{{UAP10}}}RuntimeBehavior") != "packagedClassicApp" or
            app.get(f"{{{UAP10}}}TrustLevel") != "mediumIL" or
            manifest.find(f"{{{FOUNDATION}}}Properties/{{{UAP10}}}AllowExternalContent") is not None or
            manifest.findtext(f"{{{FOUNDATION}}}Properties/{{{FOUNDATION}}}DisplayName") != PACKAGE_DISPLAY_NAME or
            lockscreen is None or lockscreen.get("Notification") != "badgeAndTileText" or
            visual.get("DisplayName") != PACKAGE_DISPLAY_NAME or
            server is None or server.get("Executable") != RUNTIME_FILE or
            server.get("Arguments") != "--background-task" or
            background_class is None or background_class.get("Id") != BACKGROUND_CLSID or
            visual.find(f"{{{UAP}}}DefaultTile") is None):
        raise InstallerError("Package does not declare the expected x64 lock-screen app.")


def require_windows_10() -> None:
    if platform.system() != "Windows" or not hasattr(sys, "getwindowsversion"):
        raise InstallerError("This installer must run on Windows 10.")
    build = sys.getwindowsversion().build
    if build < 19041 or build >= 22000:
        raise InstallerError(f"Windows build {build} is outside the supported Windows 10 range.")
    if (os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE", "")).upper() != "AMD64":
        raise InstallerError("This package requires 64-bit Windows and an x64-compatible CPU.")


def ps_literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def powershell_executable() -> Path:
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    sysnative = windows / "Sysnative" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    system32 = windows / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    return sysnative if sysnative.is_file() else system32


def ps_args(command: str) -> list[str]:
    # The parent process may prepend PowerShell 7 modules to PSModulePath.
    # Windows PowerShell 5.1 then autoloads incompatible copies of built-in
    # modules (including Microsoft.PowerShell.Security). Use its own modules.
    command = (r"[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); $env:PSModulePath = $env:WINDIR + '\System32\WindowsPowerShell\v1.0\Modules'; "
               + command)
    encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    return [str(powershell_executable()), "-NoLogo", "-NoProfile", "-NonInteractive",
            "-EncodedCommand", encoded]


class WindowsBackend:
    def run_ps(self, command: str) -> str:
        # Share the launcher's bounded environment even when this installer is
        # invoked directly from the user's large TCC/music-shell environment.
        try:
            from PAFPlayer_lockscreen import activation_environment
        except ImportError:
            activation_environment = runpy.run_path(
                str(Path(__file__).with_name('src') / 'PAFPlayer_lockscreen.py')
            )['activation_environment']
        child_env = activation_environment()
        wrapper = ("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; try { " + command +
                   " } catch { [Console]::Error.WriteLine($_.Exception.GetBaseException().Message); exit 1 }")
        result = subprocess.run(ps_args(wrapper),
                                capture_output=True, text=True, encoding="utf-8-sig", errors="replace", timeout=120,
                                env=child_env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            raise InstallerError(detail or f"Windows PowerShell failed ({result.returncode}).")
        return result.stdout.strip()

    def installed_version(self) -> str:
        command = ("$p = Get-AppxPackage -Name " + ps_literal(PACKAGE_NAME) +
                   "; if ($p) { [string]$p.Version }")
        output = self.run_ps(command)
        return output.splitlines()[-1] if output else ""

    def uac_enabled(self) -> bool:
        command = ("[int](Get-ItemProperty -Path "
                   "'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
                   "-Name EnableLUA).EnableLUA")
        return self.run_ps(command).splitlines()[-1] == "1"

    def trusted(self) -> bool:
        return self.run_ps("[bool](Get-ChildItem Cert:\\LocalMachine\\TrustedPeople\\" +
                           CERT_THUMBPRINT + " -ErrorAction SilentlyContinue)").lower() == "true"

    def signature_matches(self, package: Path, certificate: Path) -> None:
        command = ("$c = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(" +
                   ps_literal(certificate) + "); " +
                   "$s = Get-AuthenticodeSignature -LiteralPath " + ps_literal(package) + "; " +
                   "if (-not $s.SignerCertificate -or $s.SignerCertificate.Thumbprint -ne $c.Thumbprint " +
                   "-or $c.Thumbprint -ne " + ps_literal(CERT_THUMBPRINT) +
                   ") { throw 'Package signer does not match the verified PAFPlayer certificate.' }")
        self.run_ps(command)

    def elevate_certificate_import(self, certificate: Path) -> None:
        # ShellExecuteW uses UAC for this one machine-store operation. The
        # unelevated Python process remains the user's AppX installation owner.
        import ctypes
        command = ("$ErrorActionPreference='Stop'; Import-Certificate -FilePath " +
                   ps_literal(certificate) +
                   " -CertStoreLocation 'Cert:\\LocalMachine\\TrustedPeople' | Out-Null")
        args = ps_args(command)
        parameters = subprocess.list2cmdline(args[1:])
        shell_execute = ctypes.windll.shell32.ShellExecuteW
        shell_execute.restype = ctypes.c_void_p
        result = shell_execute(None, "runas", args[0], parameters, None, 1)
        if not result or int(result) <= 32:
            raise InstallerError("Certificate trust was not approved or could not be started.")
        for _ in range(90):
            if self.trusted():
                return
            time.sleep(1)
        raise InstallerError("Certificate trust was not confirmed. Registration was not attempted.")

    def register(self, package: Path, dependencies: tuple[Path, ...]) -> None:
        self.run_ps("Add-AppxPackage -Path " + ps_literal(package) +
                    " -ForceTargetApplicationShutdown -ErrorAction Stop")

    def activate(self, arguments: str) -> int:
        code = '''using System;
using System.Runtime.InteropServices;
[ComImport, Guid("2e941141-7f97-4756-ba1d-9decde894a3d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IActivation { [PreserveSig] int ActivateApplication([MarshalAs(UnmanagedType.LPWStr)] string app, [MarshalAs(UnmanagedType.LPWStr)] string args, uint options, out uint pid); }
public static class Launch { public static uint Run(string app, string args) {
var manager=(IActivation)Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")));
uint pid; int hr=manager.ActivateApplication(app,args,0,out pid);
if(hr<0) Marshal.ThrowExceptionForHR(hr); return pid; } }'''
        result = self.run_ps("Add-Type -TypeDefinition " + ps_literal(code) +
                             "; [Launch]::Run(" + ps_literal(PACKAGE_FAMILY + "!App") + "," + ps_literal(arguments) + ")")
        return int(result.splitlines()[-1])

    def verify_publication(self, root: Path) -> dict:
        report_dir = root.parent / "tests" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report = report_dir / ("v530-publication-" + uuid.uuid4().hex + ".json")
        # Activation uses the same app identity as Start, not an unpackaged exe.
        self.activate(subprocess.list2cmdline(["--verify", str(report)]))
        for _ in range(150):
            if report.is_file():
                try:
                    data = json.loads(report.read_text(encoding="utf-8-sig"))
                    data["reportPath"] = str(report)
                    return data
                except (OSError, ValueError):
                    pass  # Writer may still be completing its unique receipt.
            time.sleep(0.1)
        raise InstallerError("Windows activation returned, but no publication receipt arrived within 15 seconds.")

    def verify_background_server(self) -> None:
        # Registration alone hid a real COM launch-permission failure in the
        # first V520 candidate. Activate the actual class and require its ABI.
        self.run_ps("$task=[Activator]::CreateInstance([type]::GetTypeFromCLSID([guid]" + ps_literal(BACKGROUND_CLSID) + ")); " + r'''
$iid=[Windows.ApplicationModel.Background.IBackgroundTask,Windows.ApplicationModel,ContentType=WindowsRuntime].GUID;
$unknown=[Runtime.InteropServices.Marshal]::GetIUnknownForObject($task); $iface=[IntPtr]::Zero;
try {
    $hr=[Runtime.InteropServices.Marshal]::QueryInterface($unknown,[ref]$iid,[ref]$iface);
    if ($hr -ne 0) { [Runtime.InteropServices.Marshal]::ThrowExceptionForHR($hr) }
} finally {
    if ($iface -ne [IntPtr]::Zero) { [void][Runtime.InteropServices.Marshal]::Release($iface) }
    [void][Runtime.InteropServices.Marshal]::Release($unknown);
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($task)
}''')


def manual_steps() -> None:
    print("\nFinish these steps in your Windows account:")
    print("  1. Start PAFPlayer with its web server reachable from this computer.")
    print("  2. In PAFPlayer V530, enable Windows Lock Screen in web configuration.")
    print("     PAFPlayer starts and stops its publisher automatically; an explicit saved companion choice is migrated.")
    print("  3. Open Settings > Personalization > Lock screen. Under")
    print("     'Choose one app to show detailed status', select PAFPlayer Lock Screen V530.")
    print("     Select PAFPlayer Lock Screen V530 again for a quick-status slot to see the playing/paused/offline badge.")
    print("     The old music-note entry belongs to a different app. Open each picker to check the name.")
    print("  4. Keep PAFPlayer running. Lock with Win+L and visually check both slots.")
    print("     Windows controls rendering and truncation; publication is not visual proof.")


def install(root: Path, backend: WindowsBackend, *, check_only: bool = False,
            ask=input) -> int:
    require_windows_10()
    package, certificate, dependencies = artifacts(root)
    validate_artifacts(package, certificate, dependencies)
    for signed in (package, *dependencies):
        backend.signature_matches(signed, certificate)
    installed = backend.installed_version()
    print("EnableLUA=" + ("1" if backend.uac_enabled() else "0") + "; no UAC setting will be changed.")
    if check_only:
        print(f"V530 artifacts verified; installed version: {installed or 'none'}.")
        print("Read-only check: activation and publication were not tested.")
        return 0 if installed == PACKAGE_VERSION else 1
    if installed and tuple(map(int, installed.split('.'))) > tuple(map(int, PACKAGE_VERSION.split('.'))):
        raise InstallerError("A newer companion is installed; refusing to downgrade it.")
    if installed:
        print(f"PAFPlayer Lock Screen currently registered: {installed}.")
    if not backend.trusted():
        print("\nThe package uses a self-signed PAFPlayerLocal development certificate.")
        print("Trusting it in LocalMachine\\TrustedPeople lets Windows accept packages")
        print("signed by that certificate. Windows will ask for administrator approval.")
        try:
            consent = ask("Trust this certificate and install PAFPlayer Lock Screen? [y/N] ")
        except (EOFError, KeyboardInterrupt):
            consent = ""
        if consent.strip().casefold() not in ("y", "yes"):
            print("No certificate trust or app registration was changed.")
            return 2
        backend.elevate_certificate_import(certificate)
        if not backend.trusted():
            raise InstallerError("Certificate trust could not be verified.")
    if installed != PACKAGE_VERSION:
        print("Installing the V530 desktop publisher's signed Recovery identity package...")
        print("Only an existing Recovery publisher may close during this upgrade; PAFPlayer keeps playing.")
        backend.register(package, dependencies)
    installed = backend.installed_version()
    if installed != PACKAGE_VERSION:
        raise InstallerError("Windows did not report V530 registered for this account.")
    receipt = backend.verify_publication(root)
    expected_package = PACKAGE_NAME + "_" + PACKAGE_VERSION + "_x64__vz06efybxc4j2"
    if receipt.get("startupError") or receipt.get("package") != expected_package:
        raise InstallerError("Activation did not produce the expected package identity: " + str(receipt))
    if not receipt.get("published") and receipt.get("enabled") is not False:
        raise InstallerError("Windows notification publication failed: " + str(receipt))
    if receipt.get("enabled") is not False and (
            receipt.get("backgroundRegistered") is not True or receipt.get("backgroundRegistrationError") or
            receipt.get("backgroundDiagnosticError") or
            receipt.get("backgroundAccess") not in ("AlwaysAllowed", "AllowedSubjectToSystemPolicy", "AllowedWithAlwaysOnRealTimeConnectivity", "AllowedMayUseActiveRealTimeConnectivity")):
        raise InstallerError("Windows background registration is not ready: " + str(receipt))
    if receipt.get("enabled") is not False:
        backend.verify_background_server()
    backend.activate("")  # Keep an independent publisher running after the probe exits.
    if receipt.get("enabled") is False:
        print("Companion activated; publishing remains disabled in your saved settings.")
    else:
        print("Verified: V530 activated and submitted a tile and badge to Windows.")
        print("Windows background refresh registration, access and COM activation verified.")
        if not receipt.get("officialVerified"):
            print("Official player unavailable/unverified: displaying offline status.")
    print("Locked-screen appearance still requires the visual check below.")
    manual_steps()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate files and check this account; change nothing")
    args = parser.parse_args(argv)
    try:
        return install(Path(__file__).resolve().parent, WindowsBackend(), check_only=args.check)
    except (InstallerError, OSError, subprocess.TimeoutExpired, ValueError) as error:
        print(f"Installer stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
