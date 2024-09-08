@Echo off

rem This cleans files in the rocksmith DLC/song folder, to prevent Rocksmith startup crashes:
rem         1) we    delete duplicate Rocksmith songs (files with [1], [2], [3], [4] in them)
rem         2) we sequester  disabled Rocksmith songs (files with .disabled.psarc at the end) into a quarantined folder


if exist *([1-4])*.psarc (del *([1-4])*.psarc)

set                                  BADDIR=..\cdlc_quarantined
call validate-environment-variables  BADDIR
mv   *.disabled.psarc               %BADDIR%

