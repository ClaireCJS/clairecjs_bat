# PAFPlayer V726 — Allow Windows 11 lock-screen attempts

The V530 lock-screen installer no longer rejects Windows 11 or future Windows builds solely because their build number is 22000 or higher. Tray-only automatic setup uses the same check, so Carolyn’s reported build 26300 can reach the installer. The existing minimum Windows build 19041, x64 requirement, signed-payload checks, certificate trust, and Windows administrator consent remain in place.

Windows 11 installation and actual lock-screen status display are not yet verified. Windows may expose different selection or notification behavior; an accepted installation attempt is not proof of visible lock-screen status.

Regression checks cover source and bundled installers on Windows 10, Windows 11 build 26300, other newer builds, unsupported older builds and architectures, tray-only automatic inspection, installer safety, and single-file bundle parity. No real installation or lock-screen change was performed.
