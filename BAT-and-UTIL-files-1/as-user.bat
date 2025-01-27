@Echo OFF

::::: Change username to 1st parameter:
    set TMPUSERNAME=%USERNAME
    set username=%1
    if "%1" eq "Carolyn"  (set username=carolyn)
    if "%1" eq "Claire"   (set username=claire )
    if "%1" eq "Cl"       (set username=claire )
    if "%1" eq "Cl"       (set username=claire )
    if "%1" eq "Ca"       (set username=carolyn)
    if "%1" eq "Cs"       (set username=carolyn)
    if "%1" eq "Cas"      (set username=carolyn)
    if "%1" eq "Casl"     (set username=carolyn)
    if "%1" eq "Clio"     (set username=claire )
    if "%1" eq "Cleo"     (set username=claire )

::::: Set known_name:
    if "%username%" eq "clio"    (set KNOWNNAME=Claire )
    if "%username%" eq "claire"  (set KNOWNNAME=Claire )
    if "%username%" eq "carolyn" (set KNOWNNAME=Carolyn)
    set KNOWN_NAME=%KNOWNNAME%

::::: Re-run environment without changing username:
    set      ENVIRONM_BAT_DO_NOT_SET_USERNAME=1
    set      ENVIRONM_BAT_DO_NOT_SET_PROMPT=1
    call     ENVIRONM force
    unset /q ENVIRONM_BAT_DO_NOT_SET_USERNAME
    unset /q ENVIRONM_BAT_DO_NOT_SET_PROMPT

::::: Do what we do, which hopefully has fewer than 9 parameters, lol:
    call %2 %3 %4 %5 %6 %7 %8 %9 

::::: Revert username, redundantly re-run environment 'just in case':
    set         USERNAME=%TMPUSERNAME%
    unset /q TMPUSERNAME
    call        environm

