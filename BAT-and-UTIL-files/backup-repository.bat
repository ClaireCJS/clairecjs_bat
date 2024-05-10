@Echo OFF

rem Capture and validate parameters:
        set SOURCE=%1
        set TARGET=%2
        call validate-environment-variables SOURCE TARGET


rem Make a pretty, *aligned* header:
        set USAGE_TEXT_1=[Repository-VarName]
        set USAGE_TEXT_2=[BackupLocation-VarName]

                                                set FIELD1_LEN=%@LEN[%[%1]] 
        if %@LEN[%1]            gt %FIELD1_LEN (set FIELD1_LEN=%@LEN[%1])
        if %@LEN[%USAGE_TEXT_1] gt %FIELD1_LEN (set FIELD1_LEN=%@LEN[%USAGE_TEXT_1])

                                                set FIELD2_LEN=%@LEN[%[%2]] 
        if %@LEN[%2]            gt %FIELD2_LEN (set FIELD2_LEN=%@LEN[%2])
        if %@LEN[%USAGE_TEXT_2] gt %FIELD2_LEN (set FIELD2_LEN=%@LEN[%USAGE_TEXT_2])

        echo.
        call advice  "             %underline_on%USAGE%underline_off%:%ANSI_COLOR_CYAN%  Backup-Repository  %zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz%%@FORMAT[%FIELD1_LEN,%USAGE_TEXT_1]  %zzzzzzzzzzzzzzzzzzzzzzzz%%@FORMAT[%FIELD2_LEN,%USAGE_TEXT_2]  ['GIT']"
        call important       "%underline_on%INVOCATION%underline_off%:%ANSI_COLOR_CYAN%  Backup-Repository  %ANSI_COLOR_BRIGHT_GREEN%%italics_on%%@FORMAT[%FIELD1_LEN,%1]%zzzzzzzzz%  %ANSI_COLOR_BRIGHT_YELLOW%%@FORMAT[%FIELD2_LEN,%2]%italics_off% %ANSI_COLOR_GREEN%%@FORMAT[7,%[3] ] %[4] %[5] %[6] %[7] %[8] %[9]"
        call important       "  %underline_on%EXPANDED%underline_off%:%ANSI_COLOR_CYAN%  Backup-Repository  %ANSI_COLOR_BRIGHT_GREEN%%zzzzzzzzzz%%@FORMAT[%FIELD1_LEN,%[%1]]%zzzzzz%  %ANSI_COLOR_BRIGHT_YELLOW%%@FORMAT[%FIELD2_LEN,%[%2]]%zzzzzzzz% %ANSI_COLOR_GREEN%%@FORMAT[7,%[%3] ] %[%4] %[%5] %[%6] %[%7] %[%8] %[%9]"




set   SYNCSOURCE=%[%SOURCE%]
set   SYNCTARGET=%[%TARGET%]
set   SYNCTRIGER=__ last synced from master %SOURCE% collection __   

::::: DECIDE IF WE WILL BACKUP .BAK FILES OR NOT
    set BACKUP_BAK_FILES=0
    if  "%SOURCE%" == "MP3AUX"  (set BACKUP_BAK_FILES=1) %+ REM Careful, this uses environment variable name not folder name, so MP3AUX not \mp3-aux\
    if %BACKUP_BAK_FILES% == 0 (set EXCLUSIONS=.git all.m3u these.m3u *.bak)
    if %BACKUP_BAK_FILES% == 1 (set EXCLUSIONS=.git all.m3u these.m3u      )


goto :NoDebug
    %color_debug%
    echo SYNCSOURCE=%SYNCSOURCE%
    echo     TARGET=%SYNCTARGET%
    echo    TRIGGER=%SYNCTRIGER%
:NoDebug

::::: GIT-COMMIT IF APPLICABLE:
    if "%3" ne "GIT" (goto :GIT_No)
        call important "* Committing any changes to GIT first..."
            %SYNCSOURCE%\
                set NOPAUSETEMP=%NOPAUSE%
                set NOPAUSE=1
                    call git-commit
                    rem call sync-a-folder-to-somewhere.bat /[!%EXCLUSIONS%]
                        call sync-a-folder-to-somewhere.bat /[!%EXCLUSIONS%]
                set NOPAUSE=%NOPAUSETEMP%
            goto :GIT_Done
    :GIT_No
        call print-if-debug "        ...Not using GIT in this situation"
        call                 sync-a-folder-to-somewhere.bat /[!%EXCLUSIONS%]
        call errorlevel
        REM call print-if-debug "sync-a-folder-to-somewhere.bat /[!%EXCLUSIONS%] returned an errorlevel of %_?"
    :GIT_Done


if "%3" eq "exitafter" (exit)

if %BACKING_UP_MULTIPLE_REPOSITORIES eq 1 (
    call randFG
    call divider
)

