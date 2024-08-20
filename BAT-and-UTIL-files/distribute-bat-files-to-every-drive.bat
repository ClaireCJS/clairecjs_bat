@Echo Off

:DESCRIPTION: Used to reliably distribute BAT files to other computers [and update our GIT repo]

:USAGE: Dist full         - recursively updates whole \BAT\ dir to all other computers' \BAT\ folder in a single window, one drive at a time
:USAGE: Dist full fast    - recursively updates whole \BAT\ dir to all other computers' \BAT\ folder in a separate window for each drive, with less comprehensive git-add coverage and no git-commit
:USAGE: Dist whatever.bat - distributes whatever.bat            to all other computers' \BAT\ folder
:USAGE: Dist {command}    - runs command                        in all other computers' \BAT\ folder
:USAGE:          EXAMPLE: dist del foo.exe would delete foo.exe in all other computers' \BAT\ folder 

:HISTORY:     2000ish: created
:HISTORY:     2015xxx: now maintanance free! 
:HISTORY:     2024xxx: fixed up and published


::::: CONFIGURATION:
        set FILES_TO_ADD_TO_GIT_IN_QUICK_MODE=*.bat *.btm *.py *.pl *.txt *.env *.ahk *.BAT *.BTM *.PL *.TXT .gitignore msirepair.reg
        set DIST_DELAY=1                       %+ rem How many seconds to wait in situations where we decide to wait between eachcopy

::::: VALIDATE ENVIRONMENT:
        call  validate-environment-variables space
        call  validate-in-path               sleep checkmappings all-ready-drives wake-all-drives important divider
        rem   checkmappings.bat nopause ———— we no longer do this with the 'nopause' option, but we used to
        call  checkmappings.bat 

::::: PREPARE FOR COPY:
        pushd
        call go-to-bat-file-folder
        if exist *.bak (*del *.bak)

::::: BRANCH TO DIFFERENT BEHAVIORS BASED ON PARAMETERS:
        set Command_To_Use=copy /g /h /u /[!.git *.bak] %1%SPACE
        if "%1"==""                        (goto :usage         )
        if "%1"=="full"                    (goto :full          )
        if "%1"=="full" .and. "%2"=="fast" (goto :full_fast     )
        if not exist %1                    (goto :Custom_Command)

        rem gosub :doit —— was the old/inelegant way we used for decades, we now use :doit2024:
            gosub :doit2024
            goto  :Cleanup


::::: CLEAN UP WHEN DONE:
        :Cleanup
            :unset /q Command_To_Use
            if defined DIST_DELAY (set LAST_DIST_DELAY=%DIST_DELAY% %+ unset /q DIST_DELAY)
        goto :END



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:usage
    %COLOR_ADVICE%
    echo Dist full             - recursively updates whole \BAT\ dir to all other computers' \BAT\ folder in a single window, one drive at a time
    echo Dist full fast        - recursively updates whole \BAT\ dir to all other computers' \BAT\ folder in a separate window for each drive, with less comprehensive git-add coverage, and no git-commit
    echo Dist whatever.bat     - distributes whatever.bat            to all other computers' \BAT\ folder
    echo Dist {command}        - runs command                        in all other computers' \BAT\ folder
    echo                         for example: %italics_on%dist del foo.exe%italics_off%  would delete foo.exe in all other computers' \BAT\ folder 
    %COLOR_NORMAL%
goto :Cleanup
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Delay
    if "%DIST_DELAY%" ne "" (%COLOR_DEBUG% %+ echo %EMOJI_STOPWATCH%%EMOJI_STOPWATCH% (waiting %DIST_DELAY% seconds) %EMOJI_STOPWATCH%%EMOJI_STOPWATCH% %+ %COLOR_NORMAL% %+ sleep %DIST_DELAY%)
return
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:doit2024
    call less_important "Distributing just one file"
    set OPTION_SKIP_SAME_C=1
    set OPTION_ECHO_RAYRAY=1
    rem no /s here:
    call all-ready-drives "if exist DRIVE_LETTER:\bat copy /u /a: /[!.git *.bak] /r /h /z /k /g \bat\%1 DRIVE_LETTER:\bat"
goto :Cleanup
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:full
    cls

    rem COPY TO ALL FOLDERS USING SCRIPT TO RUN A COMMAND ON EVERY DRIVE LETTER THAT EIXSTS:
            set OPTION_SKIP_SAME_C=1
            set OPTION_ECHO_RAYRAY=1
            call all-ready-drives "if exist DRIVE_LETTER:\bat copy /e /w /u /s /a: /[!.git *.bak] /h /z /k /g \bat\ DRIVE_LETTER:\bat"

    rem DRAW A PRETTY DIVIDER:
            echo.
            call divider
            echo.

    rem ADD/UPDATE/COMMIT FILES TO OUR GIT REPO:
            set TEMP_OPTION=%NO_GIT_ADD_PAUSE%
            set NO_GIT_ADD_PAUSE=1
            call GIT-ADD *.*
            set NO_GIT_ADD_PAUSE=%TEMP_OPTION%
            call GIT-COMMIT nopause

goto :Cleanup
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:full_fast
    rem This does it in parallel with a less comprehensive git-ad command
    cls
    set NO_GIT_ADD_PAUSE=1
    call git-add %FILES_TO_ADD_TO_GIT_IN_QUICK_MODE%
    call git-commit nopause
    set NO_GIT_ADD_PAUSE=0
                                                                                                   unset /q MIN 
    if "%1" eq "MINIMIZE" .or. "%2" eq "MINIMIZE" .or. "%3" eq "MINIMIZE" .or. "%4" eq "MINIMIZE" (  set    MIN=/min)
    set Command_To_Use=start %MIN% if isdir c:\bat exitcopy /s /e /u /w /a: /[!.git *.bak] c:\bat
    gosub :doit
    rem Create a file as a way to timestamp the last time this was done:
    >"__ last dist __"
goto :Cleanup
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Custom_Command
    rem We force a preview before doing it, because this one is dangerous
    set Command_To_Use=echo %1
    set TailCmd=%2 %3 %4 %5 %6 %7 %8 %9
    repeat 6 echo. 
    gosub :doit_for_custom_commands
    repeat 2 echo. 
    call warning "Press Ctrl-Break NOW if the above does not look correct."
    repeat 2 echo. 
    repeat 5 pause pause
    set Command_To_Use=%1
    gosub :doit_for_custom_commands
goto :Cleanup
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:doit_for_custom_commands
    call wake-all-drives
   if "%@READY[M]" eq "1" if isdir M:\bat %Command_To_Use M:\bat\%TailCmd
   if "%@READY[K]" eq "1" if isdir K:\bat %Command_To_Use K:\bat\%TailCmd
   gosub delay
   if "%@READY[A]" eq "1" if isdir A:\bat %Command_To_Use A:\bat\%TailCmd
   if "%@READY[B]" eq "1" if isdir B:\bat %Command_To_Use B:\bat\%TailCmd
   if "%@READY[C]" eq "1" if isdir C:\bat %Command_To_Use C:\bat\%TailCmd
   gosub delay
   if "%@READY[D]" eq "1" if isdir D:\bat %Command_To_Use D:\bat\%TailCmd
   if "%@READY[E]" eq "1" if isdir E:\bat %Command_To_Use E:\bat\%TailCmd
   if "%@READY[F]" eq "1" if isdir F:\bat %Command_To_Use F:\bat\%TailCmd
   if "%@READY[G]" eq "1" if isdir G:\bat %Command_To_Use G:\bat\%TailCmd
   gosub delay
   if "%@READY[H]" eq "1" if isdir H:\bat %Command_To_Use H:\bat\%TailCmd
   if "%@READY[I]" eq "1" if isdir I:\bat %Command_To_Use I:\bat\%TailCmd
   if "%@READY[J]" eq "1" if isdir J:\bat %Command_To_Use J:\bat\%TailCmd
   if "%@READY[L]" eq "1" if isdir L:\bat %Command_To_Use L:\bat\%TailCmd
   if "%@READY[N]" eq "1" if isdir N:\bat %Command_To_Use N:\bat\%TailCmd
   gosub delay
   if "%@READY[O]" eq "1" if isdir O:\bat %Command_To_Use O:\bat\%TailCmd
   if "%@READY[P]" eq "1" if isdir P:\bat %Command_To_Use P:\bat\%TailCmd
   if "%@READY[Q]" eq "1" if isdir Q:\bat %Command_To_Use Q:\bat\%TailCmd
   if "%@READY[R]" eq "1" if isdir R:\bat %Command_To_Use R:\bat\%TailCmd
   if "%@READY[S]" eq "1" if isdir S:\bat %Command_To_Use S:\bat\%TailCmd
   if "%@READY[T]" eq "1" if isdir T:\bat %Command_To_Use T:\bat\%TailCmd
   gosub delay
   if "%@READY[U]" eq "1" if isdir U:\bat %Command_To_Use U:\bat\%TailCmd
   if "%@READY[V]" eq "1" if isdir V:\bat %Command_To_Use V:\bat\%TailCmd
   if "%@READY[W]" eq "1" if isdir W:\bat %Command_To_Use W:\bat\%TailCmd
   if "%@READY[X]" eq "1" if isdir X:\bat %Command_To_Use X:\bat\%TailCmd
   if "%@READY[Y]" eq "1" if isdir Y:\bat %Command_To_Use Y:\bat\%TailCmd
   if "%@READY[Z]" eq "1" if isdir Z:\bat %Command_To_Use Z:\bat\%TailCmd

    if "%2"== "noWAN"   (return)
    if ""  != "%HDWORK" (%Command_To_Use %HDWORK:\bat\%TailCmd)
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


































::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:doit_OLD_DEPRECATED
    REM THIS IS THE OLD DEPRECATED HARDCODED WAYS THAT WERE REFACTORED AND NO LONGER USED:

    call wake-all-drives
       if "%@READY[A]" eq "1" if isdir A:\bat %Command_To_Use A:\bat
       if "%@READY[K]" eq "1" if isdir K:\bat %Command_To_Use K:\bat
           gosub delay
       if "%@READY[M]" eq "1" if isdir M:\bat %Command_To_Use M:\bat
       if "%@READY[B]" eq "1" if isdir B:\bat %Command_To_Use B:\bat
       if "%@READY[C]" eq "1" if isdir C:\bat %Command_To_Use C:\bat
       if "%@READY[D]" eq "1" if isdir D:\bat %Command_To_Use D:\bat
           gosub delay
       if "%@READY[E]" eq "1" if isdir E:\bat %Command_To_Use E:\bat
       if "%@READY[F]" eq "1" if isdir F:\bat %Command_To_Use F:\bat
       if "%@READY[G]" eq "1" if isdir G:\bat %Command_To_Use G:\bat
       if "%@READY[H]" eq "1" if isdir H:\bat %Command_To_Use H:\bat
       if "%@READY[I]" eq "1" if isdir I:\bat %Command_To_Use I:\bat
           gosub delay
       if "%@READY[J]" eq "1" if isdir J:\bat %Command_To_Use J:\bat
       if "%@READY[L]" eq "1" if isdir L:\bat %Command_To_Use L:\bat
       if "%@READY[N]" eq "1" if isdir N:\bat %Command_To_Use N:\bat
       if "%@READY[O]" eq "1" if isdir O:\bat %Command_To_Use O:\bat
       if "%@READY[P]" eq "1" if isdir P:\bat %Command_To_Use P:\bat
           gosub delay
       if "%@READY[Q]" eq "1" if isdir Q:\bat %Command_To_Use Q:\bat
       if "%@READY[R]" eq "1" if isdir R:\bat %Command_To_Use R:\bat
       if "%@READY[S]" eq "1" if isdir S:\bat %Command_To_Use S:\bat
       if "%@READY[T]" eq "1" if isdir T:\bat %Command_To_Use T:\bat
       if "%@READY[U]" eq "1" if isdir U:\bat %Command_To_Use U:\bat
           gosub delay
       if "%@READY[V]" eq "1" if isdir V:\bat %Command_To_Use V:\bat
       if "%@READY[W]" eq "1" if isdir W:\bat %Command_To_Use W:\bat
       if "%@READY[X]" eq "1" if isdir X:\bat %Command_To_Use X:\bat
       if "%@READY[Y]" eq "1" if isdir Y:\bat %Command_To_Use Y:\bat
       if "%@READY[Z]" eq "1" if isdir Z:\bat %Command_To_Use Z:\bat

        if "%2" == "noWAN"   (return)
        if ""   != "%HDWORK" (%Command_To_Use %HDWORK:\bat)
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



















:END

