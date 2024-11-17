@echo off

:DESCRIPTION: Backs a file up to every \BACKUPS\ folder on every drive!  C:\BACKUPS, D:\BACKUPS, E:\BACKUPS, etc
:USAGE:       set PARALLEL_BACKUP=1 if you want 1 to open a window for each drive and run all copies in parallel
:USAGE:       backup {file}




rem CONFIGURATION:
        set MINIMUMDELAY_BETWEEN_EACH_WINDOW_LAUNCH=250      %+ rem how many milliseconds between each file copy


rem MAKE SURE WE'RE RUNNING IT RIGHT:
        call validate-environment-variable THE_ALPHABET      %+ rem set THE_ALPHABET=A B C D E F G H I J K L M N O P Q R S T U V W X Y Z except we already have this done as part of environment and rather than re-define it here, we want to defer to our environment because that makes for easier debugging
        call validate-in-path echos fast_cat delay start
        if "" eq "%1" (goto :usage)
        if isdir "%1" (call warning "This behavior (backing up a folder to every drive letter) is not currently developed for this script" %+ goto :END)
        rem TODO: though probably to do a folder, just make a /s with the copy, and just add \${folder} to end of the target - could be done easily, just haven't had a need yet


rem BACK UP THE FILE TO EACH DRIVE LETTER:
        for %driveLetter in (%THE_ALPHABET%)  gosub backup %driveLetter%


    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    goto :Skip_Subroutines
        :backup [letter]
            rem Ensure drive is ready:
                    if "0" eq "%@READY[%letter%:]" (return)

            rem Check that \BACKUPS\ folder exists:
                    if not isdir %letter%:\backups\ (return)

            rem We can set environment variables to do these in parallel (multi-window) or sequential (same-window)
                                                    unset /q COMMANDPREFIX
                    if   "%PARALLEL_BACKUP%" eq "1"  (set    COMMANDPREFIX=start /POS=-1000,-1000,0,0 exitafter)
                    if "%SEQUENTIAL_BACKUP%" eq "1"  (set    COMMANDPREFIX=)

            rem Give each file a random color, and pipe it to fast_cat to fix TCC+WT ansi rendering failures:
                    echos %@ANSI_RANDFG[] | fast_cat

            rem Actually back up the file:
                    %COMMANDPREFIX% copy /g %1 %letter%:\backups

            rem Throttle our speed as per the configuration delay defined at the top of this file:
                    delay /m %MINIMUMDELAY_BETWEEN_EACH_WINDOW_LAUNCH%
        return
    :Skip_Subroutines
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::: SAY SOME STUFF UNLESS WE'RE TOLD NOT TO:
    if "%2"=="quiet" goto :quiet
        :usage
            %COLOR_ADVICE%
            echo.
            echo OTHER PROGRAMS:
            echo   backup-folder:  backs a folder up to 1G RAR files with 10% parity
            echo   backup-thing:   backs a file   up to 1G RAR files with 10% parity
            echo   backup-stuff:   backs up all important files on the current computer to all backup areas
            echo   backup-to-dvds: backs up to 1/4th-dvd sized RAR files
            echo   backup-to-bdrs: backs up to 1/7th-bdr sized RAR files
            echo USAGE:
            echo   backup [file/dir]        to backup to all backup areas
            echo   backup [file/dir] [name] to backup to all backup areas using a different filename
        goto :END
    :quiet

:END

:HISTORY: 2002-ish: Created
:HISTORY: 20140714: Now with less screaming!
:HISTORY: 20240820: Finally publishing!


