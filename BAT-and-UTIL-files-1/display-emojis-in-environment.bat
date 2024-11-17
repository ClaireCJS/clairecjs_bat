@Echo off


:cls
set SILENT=0
if "%1" eq "silent" set SILENT=1
if "%1" eq "tight"  set TIGHT=1

call settmpfile
call important "dumping variables"
set|sed "s/=.*$//ig" >"%TMPFILE%"
:DEBUG: (set|:u8sed "s/=.*$//ig") %+ echo TMPFILE: %+ type "%TMPFILE%" %+ pause
call important "processing variables"
for /f "tokens=1-999" %co in (%TMPFILE%) gosub ProcessEnvVar %co%


goto :END
    :ProcessEnvVar [var]
        REM if  "%VAR%" eq "LAST_RANDCOLOR" set ADD_TO_ALL_COLORS=0 %+ REM  don't add this one to our ALL_COLORS list because it's an audit color not one of our messaging colors .. any LAST_.*COLOR really would be, but this is the only one bothering us
        REM echo processing %var
        if "%@REGEX[EMOJI_,%VAR]" ne "1" goto :Continue
        if %SILENT ne 1 (
            if %TIGHT eq 1 (
                echos %[%VAR]
            ) else (
                call bigecho "%[%VAR] - %VAR"
            )
        )
        :Continue
    return
:END
echo.


REM echo. %+ call debug "ALL_COLORS is now set to '%ALL_COLORS%'"
