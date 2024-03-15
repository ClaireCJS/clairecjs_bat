@Echo OFF

call advice "       USAGE:  Backup-Repository [REPO-VARNAME] [BACKUPLOCATION-VARNAME] [GIT]"
call important "  INVOCATION:  Backup-Repository %1 %2 %3 %4 %5 %6 %7 %8 %9"
call important "    EXPANDED:  Backup-Repository %[%1] %[%2] %[%3] %[%4] %[%5] %[%6] %[%7] %[%8] %[%9]"



:::: This *does* validate the source and target, but it does it within a subordinate script.



set SOURCE=%1
set TARGET=%2

call validate-environment-variables SOURCE TARGET

set   SYNCSOURCE=%[%SOURCE%]
set   SYNCTARGET=%[%TARGET%]
set   SYNCTRIGER=__ last synced from master %SOURCE% collection __   

::::: DECIDE IF WE WILL BACKUP .BAK FILES OR NOT
    set BACKUP_BAK_FILES=0
    if  "%SOURCE" == "MP3AUX"  (set BACKUP_BAK_FILES=1) %+ REM Careful, this uses environment variable name not folder name, so MP3AUX not \mp3-aux\
    if %BACKUP_BAK_FILES% == 0 (set EXCLUSIONS=.git all.m3u these.m3u *.bak)
    if %BACKUP_BAK_FILES% == 1 (set EXCLUSIONS=.git all.m3u these.m3u      )


goto :NoDebug
    %color_debug%
    ECHO SYNCSOURCE=%SYNCSOURCE%
    ECHO     TARGET=%SYNCTARGET%
    ECHO    TRIGGER=%SYNCTRIGER%
:NoDebug

::::: GIT-COMMIT IF APPLICABLE:
    if "%3" ne "GIT" (goto :GIT_No)
        call important "* Committing any changes to GIT first..."
            %SYNCSOURCE%\
                set NOPAUSETEMP=%NOPAUSE%
                set NOPAUSE=1
                    call git-commit
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


