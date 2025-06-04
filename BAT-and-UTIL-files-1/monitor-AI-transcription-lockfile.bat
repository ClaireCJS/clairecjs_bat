@echo off
@on break cancel

call validate-in-path divider display-date-and-time-nicely type sleep

pushd .
call util2
cd Faster-Whisper-XXL\

call set-tmp-file "ai transcription lockfile monitor"

unset /q lockfile_present
call divider
:again
        call display-date-and-time-nicely
        rem echos %STAR% [lockfile_present=%lockfile_present%] More specifically, it is: 
        set timet=%@EXECSTR[time /t]
        echo                  (and %@right[2,%timet%] seconds)

        iff not exist *.lock then 
                if "%lockfile_present%" == "1" (repeat 3 beep %+ call alarm-charge %+ window /flash)
                set  lockfile_present=0
                call less_important "No lockfile present right now!" big
        else
                echo.
                set  lockfile_present=1
                type *.lock
        endiff


        echo.
        tasklist |:u8 grep faster-whisper |:u8 grep -v TCC |:u8 insert-before-each-line.py "       %EMOJI_EAR% %ansi_color_run%" >:u8%tmpfile1%
        call fast_cat %tmpfile%

        echo.
        call divider

        sleep 3
goto :again

unset /q lockfile_present
popd