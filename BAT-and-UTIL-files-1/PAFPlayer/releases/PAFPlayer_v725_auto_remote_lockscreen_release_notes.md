# PAFPlayer V725 — Automatic tray-only lock-screen setup

Tray-only lock-screen status defaults on unless the user previously explicitly disabled it. At startup, even while the music server is disconnected, PAFPlayer checks supported Windows, companion registration and certificate trust. A missing or repairable companion is installed using the existing bundled installer without a tray-menu action; a Windows administrator/UAC prompt remains necessary when certificate trust requires it. A compatible, trusted installation is not reinstalled. A newer companion is not downgraded.

The setup window opens when Windows selection, approval, troubleshooting or publisher-error attention is needed. Its acknowledgement records that the user selected PAFPlayer; it does not claim to read or verify Windows' selected lock-screen slot. Explicit off remains respected. V530 supports 64-bit Windows 10 build 19041 or newer, not Windows 11.

Regression checks use fake installers and test default-on and explicit-off behavior, installed and newer versions, UAC-off and unsupported-Windows handling, disconnected startup, re-enabling, installation failure, publisher failure, existing bridge behavior and source/bundle parity. No actual installation or locked-screen visual verification was performed.
