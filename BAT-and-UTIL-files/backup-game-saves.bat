@Echo Off


rem Validate the environment:
        call validate-in-path AskYN backup-RockSmith
        cls
        

rem Round #1: Ask for backup decisions in advance, but in a way that falls back to automatic (via timers) if no one is there to answer
rem Round #2: Do  the backups
        :First_Pass
        call  bigEcho "%ANSI_COLOR_RED%%STAR% Optionally answer:" %+ echo.
        unset /q ASKED_ALREADY

        :Main
            gosub ask_about_backup "Rogue Legacy" ROGUE_LEGACY backup-Rogue_Legacy_2
            gosub ask_about_backup "RockSmith"    ROCKSMITH    backup-RockSmith

            if "%ASKED_ALREADY%" == "1" (goto :Main_Complete)
            set  ASKED_ALREADY=1
            goto :Main
        :Main_Complete




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :END
        :ask_about_backup [description VarNameSegment BackupCommand]
                set DO_BACKUP_VARNAME=DO_BACKUP_%VarNameSegment%

                if not "1" == "%ASKED_ALREADY%" (
                        call validate-in-path %BackupCommand%
                        unset /q %DO_BACKUP_VARNAME%
                        call AskYN "Backup %italics_on%%@UNQUOTE[%description%]%italics_off%" no 20
                                    if "N" == "%ANSWER%" (set %DO_BACKUP_VARNAME%=0)
                                    if "Y" == "%ANSWER%" (set %DO_BACKUP_VARNAME%=1)
                )

                if "1" == "%ASKED_ALREADY%" (
                        if "1" == "%[%DO_BACKUP_VARNAME]" (call %BackupCommand%)
                ) 
        return

:END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

echo.
call celebration "Game save backups complete"

