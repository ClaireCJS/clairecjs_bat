@on break cancel
@Echo Off

:DESCRIPTION: Used to reliably distribute BAT files to other computers [and update our GIT repo] ... repliate c:\bat to d:\bat, e:\bat, to EVERY READY DRIVE LETTER that has a \bat\ folder


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
        call validate-environment-variables space
        call validate-in-path               sleep checkmappings all-ready-drives wake-all-drives important divider

::::: NON-SCROLLABLE HEADER:
        call footer unlock
        cls
        repeat 1 echo.
        call footer "Distributing BAT file folder to all drives..."

::::: PREPARE FOR COPY:
        pushd
        call go-to-bat-file-folder
        if exist *.bak (*del /q *.bak)

::::: BRANCH TO DIFFERENT BEHAVIORS BASED ON PARAMETERS:
        set Command_To_Use=*copy /g /h /u /[!.git *.bak] %1%SPACE
        if "%1"==""                                   (                         goto :usage         )
        if "%1"=="full"                               (                         goto :full          )
        if "%1"=="full" .and. "%2"=="fast"            (set DIST_NOCHECKMAP=1 %+ goto :full_fast     )
        if "%1"=="full" .and. "%2"=="nocheckmappings" (set DIST_NOCHECKMAP=1 %+ goto :full_fast     )
        if not exist %1                               (                         goto :Custom_Command)

::::: MAKE SURE ALL OUR DRIVES ARE MAPPED:
        rem  checkmappings.bat nopause ———— we no longer do this with the 'nopause' option, but we used to
        rem  checkmappings.bat  ————————————— 20241013: changing back to nopause because this is run from autoexec:
        if 1 ne %DIST_NOCHECKMAP (call checkmappings.bat once nopause) %+ rem 2024/12/30: once only currently works with “once nopause” but not “nopause once”


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
    if "%DIST_DELAY%" != "" (%COLOR_DEBUG% %+ echo %EMOJI_STOPWATCH%%EMOJI_STOPWATCH% (waiting %DIST_DELAY% seconds) %EMOJI_STOPWATCH%%EMOJI_STOPWATCH% %+ %COLOR_NORMAL% %+ sleep %DIST_DELAY%)
return
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:doit2024
    call less_important "Distributing just one file"
    set OPTION_SKIP_SAME_C=1
    set OPTION_ECHO_RAYRAY=1
    set OPTION_ARD_POSTPROCESS=0 %+ rem 20241013 turning this back to 0
    rem no /s here:
    
    rem all-ready-drives sometimes has trouble copying itself when open, so we'll copy it to \recycled\ and run the copy instead:
            set TEMP_ALL_AREADY_DRIVES_SCRIPT_NAME=c:\recycled\all-ready-drives-temp-%_DATETIME.bat %+ rem make name
            echo ray | *copy /q /r c:\bat\all-ready-drives.bat %TEMP_ALL_AREADY_DRIVES_SCRIPT_NAME% %+ rem copy it to name
            call validate-environment-variable TEMP_ALL_AREADY_DRIVES_SCRIPT_NAME                   %+ rem make sure it copied, then run it:
            
    rem ACTUALLY DISTRIBUTE THE BAT FILES TO EVERY DRIVE:                    
            call %TEMP_ALL_AREADY_DRIVES_SCRIPT_NAME% "if exist DRIVE_LETTER:\bat *copy /Nt /RCT /k /l /u /a: /[!.git *.bak  setpath.cmd] /r /h /z /k /g \bat\%1 DRIVE_LETTER:\bat"

    set OPTION_ARD_POSTPROCESS=0
goto :Cleanup
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:full
    rem cls

    rem COPY TO ALL FOLDERS USING SCRIPT TO RUN A COMMAND ON EVERY DRIVE LETTER THAT EIXSTS:
            set OPTION_SKIP_SAME_C=1
            set OPTION_ECHO_RAYRAY=1
            set OPTION_ARD_POSTPROCESS=1
                    rem We don't dist setpath.cmd because it is dynamically generated per-computer:
                    (call all-ready-drives "if exist DRIVE_LETTER:\bat (*copy /e /w /u /s /a: /[!.git *.bak setpath.cmd] /h /z /k /g \bat\ DRIVE_LETTER:\bat)") 
            unset OPTION_SKIP_SAME_C
            unset OPTION_ECHO_RAYRAY
            unset OPTION_ARD_POSTPROCESS

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

    rem update to github...
            call askYN "Update to %italics_on%GitHub%italics_off% as well?" yes 600
            if %ANSWER eq Y (call publish-bat-updates-to-github.bat)


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
    if "%1" == "MINIMIZE" .or. "%2" == "MINIMIZE" .or. "%3" == "MINIMIZE" .or. "%4" == "MINIMIZE" (  set    MIN=/min)
    set Command_To_Use=start "Dist'ing..." %MIN% if isdir c:\bat exitcopy /s /e /u /w /a: /[!.git *.bak] c:\bat
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
   if "%@READY[M]" == "1" if isdir M:\bat %Command_To_Use M:\bat\%TailCmd
   if "%@READY[K]" == "1" if isdir K:\bat %Command_To_Use K:\bat\%TailCmd
   gosub delay
   if "%@READY[A]" == "1" if isdir A:\bat %Command_To_Use A:\bat\%TailCmd
   if "%@READY[B]" == "1" if isdir B:\bat %Command_To_Use B:\bat\%TailCmd
   if "%@READY[C]" == "1" if isdir C:\bat %Command_To_Use C:\bat\%TailCmd
   gosub delay
   if "%@READY[D]" == "1" if isdir D:\bat %Command_To_Use D:\bat\%TailCmd
   if "%@READY[E]" == "1" if isdir E:\bat %Command_To_Use E:\bat\%TailCmd
   if "%@READY[F]" == "1" if isdir F:\bat %Command_To_Use F:\bat\%TailCmd
   if "%@READY[G]" == "1" if isdir G:\bat %Command_To_Use G:\bat\%TailCmd
   gosub delay
   if "%@READY[H]" == "1" if isdir H:\bat %Command_To_Use H:\bat\%TailCmd
   if "%@READY[I]" == "1" if isdir I:\bat %Command_To_Use I:\bat\%TailCmd
   if "%@READY[J]" == "1" if isdir J:\bat %Command_To_Use J:\bat\%TailCmd
   if "%@READY[L]" == "1" if isdir L:\bat %Command_To_Use L:\bat\%TailCmd
   if "%@READY[N]" == "1" if isdir N:\bat %Command_To_Use N:\bat\%TailCmd
   gosub delay
   if "%@READY[O]" == "1" if isdir O:\bat %Command_To_Use O:\bat\%TailCmd
   if "%@READY[P]" == "1" if isdir P:\bat %Command_To_Use P:\bat\%TailCmd
   if "%@READY[Q]" == "1" if isdir Q:\bat %Command_To_Use Q:\bat\%TailCmd
   if "%@READY[R]" == "1" if isdir R:\bat %Command_To_Use R:\bat\%TailCmd
   if "%@READY[S]" == "1" if isdir S:\bat %Command_To_Use S:\bat\%TailCmd
   if "%@READY[T]" == "1" if isdir T:\bat %Command_To_Use T:\bat\%TailCmd
   gosub delay
   if "%@READY[U]" == "1" if isdir U:\bat %Command_To_Use U:\bat\%TailCmd
   if "%@READY[V]" == "1" if isdir V:\bat %Command_To_Use V:\bat\%TailCmd
   if "%@READY[W]" == "1" if isdir W:\bat %Command_To_Use W:\bat\%TailCmd
   if "%@READY[X]" == "1" if isdir X:\bat %Command_To_Use X:\bat\%TailCmd
   if "%@READY[Y]" == "1" if isdir Y:\bat %Command_To_Use Y:\bat\%TailCmd
   if "%@READY[Z]" == "1" if isdir Z:\bat %Command_To_Use Z:\bat\%TailCmd

    if "%2"== "noWAN"   (return)
    if ""  != "%HDWORK" (%Command_To_Use %HDWORK:\bat\%TailCmd)
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


































::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:doit_OLD_DEPRECATED
    REM THIS IS THE OLD DEPRECATED HARDCODED WAYS THAT WERE REFACTORED AND NO LONGER USED:

    call wake-all-drives
       if "%@READY[A]" == "1" if isdir A:\bat %Command_To_Use A:\bat
       if "%@READY[K]" == "1" if isdir K:\bat %Command_To_Use K:\bat
           gosub delay
       if "%@READY[M]" == "1" if isdir M:\bat %Command_To_Use M:\bat
       if "%@READY[B]" == "1" if isdir B:\bat %Command_To_Use B:\bat
       if "%@READY[C]" == "1" if isdir C:\bat %Command_To_Use C:\bat
       if "%@READY[D]" == "1" if isdir D:\bat %Command_To_Use D:\bat
           gosub delay
       if "%@READY[E]" == "1" if isdir E:\bat %Command_To_Use E:\bat
       if "%@READY[F]" == "1" if isdir F:\bat %Command_To_Use F:\bat
       if "%@READY[G]" == "1" if isdir G:\bat %Command_To_Use G:\bat
       if "%@READY[H]" == "1" if isdir H:\bat %Command_To_Use H:\bat
       if "%@READY[I]" == "1" if isdir I:\bat %Command_To_Use I:\bat
           gosub delay
       if "%@READY[J]" == "1" if isdir J:\bat %Command_To_Use J:\bat
       if "%@READY[L]" == "1" if isdir L:\bat %Command_To_Use L:\bat
       if "%@READY[N]" == "1" if isdir N:\bat %Command_To_Use N:\bat
       if "%@READY[O]" == "1" if isdir O:\bat %Command_To_Use O:\bat
       if "%@READY[P]" == "1" if isdir P:\bat %Command_To_Use P:\bat
           gosub delay
       if "%@READY[Q]" == "1" if isdir Q:\bat %Command_To_Use Q:\bat
       if "%@READY[R]" == "1" if isdir R:\bat %Command_To_Use R:\bat
       if "%@READY[S]" == "1" if isdir S:\bat %Command_To_Use S:\bat
       if "%@READY[T]" == "1" if isdir T:\bat %Command_To_Use T:\bat
       if "%@READY[U]" == "1" if isdir U:\bat %Command_To_Use U:\bat
           gosub delay
       if "%@READY[V]" == "1" if isdir V:\bat %Command_To_Use V:\bat
       if "%@READY[W]" == "1" if isdir W:\bat %Command_To_Use W:\bat
       if "%@READY[X]" == "1" if isdir X:\bat %Command_To_Use X:\bat
       if "%@READY[Y]" == "1" if isdir Y:\bat %Command_To_Use Y:\bat
       if "%@READY[Z]" == "1" if isdir Z:\bat %Command_To_Use Z:\bat

        if "%2" == "noWAN"   (return)
        if ""   != "%HDWORK" (%Command_To_Use %HDWORK:\bat)
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



















:END
        call footer unlock

