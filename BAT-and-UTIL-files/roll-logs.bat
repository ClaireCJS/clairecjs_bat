@echo off

rem SET UP FOLDER LOCATIONS:
        if ""  ==    "%LOGPARENTDIR" (set  LOGPARENTDIR="c:\backups\logs")
        if ""  ==    "%LOGDIR"       (set        LOGDIR="c:\backups\logs")
        if not isdir "%LOGPARENTDIR" (md "%LOGPARENTDIR"                 )
        if not isdir "%LOGDIR"       (md "%LOGDIR"                       )

rem VALIDATE ENVIRONMENT:
        call validate-environment-variables LOCALAPPDATA WINDIR ProgramData LOGDIR LOGPARENTDIR LOCALAPPDATA ProgramData WINDIR
        call validate-in-path               less_important roll-log-madvr roll-lastfm-log

rem LET USER KNOW WHAT WE'RE DOING:
         call less_important "Rolling wanted log files into: %italics_on%%bold_on%%LOGDIR%%bold_off%%italics_off%"

rem EASY CLEANUPS:
        if exist c:\*.log          (move /q /a: c:\*.log          %LOGDIR)
        if exist c:\bootlog*.*     (move /q /a: c:\bootlog*.*     %LOGDIR)
        if exist c:\util\wget-log* (move /q /a: c:\util\wget-log* %LOGDIR)

rem CLEANUPS MOVED TO OTHER SCRIPTS:                         {add any new ones to the validate-in-path command above}
        call roll-log-madvr
        call roll-lastfm-log

rem DELETE VARIOUS LOG FILES THAT EAT UP SPACE:
        echos %ANSI_COLOR_LESS_IMPORTANT%%STAR% Deleting unwanted log files
        set MASK=*.*            %+ set TARGET=%ProgramData%\Microsoft\Windows\WER\ReportQueue\ %+ gosub RecursivelyCleanMaskFromTarget %+ rem WER_WindowsErrorReportQueue
        set MASK=*.mdmp;*.hdmp  %+ set TARGET=%LOCALAPPDATA\Microsoft\Windows\WER\             %+ gosub RecursivelyCleanMaskFromTarget %+ rem WER_WindowsErrorReportQueue
        set MASK=*.log          %+ set TARGET=%WINDIR%\logs\cbs\                               %+ gosub RecursivelyCleanMaskFromTarget %+ rem WindowsLogsCBS
        set MASK=*.*            %+ set TARGET=%LOCALAPPDATA%\temp\                             %+ gosub RecursivelyCleanMaskFromTarget %+ rem temp folders

goto :END


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :RecursivelyCleanMaskFromTarget
        call randfg
        echos %ANSI_SAVE_POSITION%%TARGET%
        if isdir %TARGET% ((echo yr|*del /s %TARGET%\%MASK%))>nul>&>nul
        echos %ANSI_RESTORE_POSITION%.%ANSI_ERASE_TO_EOL%
    return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
    unset /q LOGDIR
    unset /q LOGPARENTDIR
    echo %ANSI_COLOR_SUCCESS%done!
    if /i "%1"=="exit" (exit)
    