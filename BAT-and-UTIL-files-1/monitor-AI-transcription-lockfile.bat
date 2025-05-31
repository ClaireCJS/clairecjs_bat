@echo off
@on break cancel

call validate-in-path divider display-date-and-time-nicely type sleep

pushd .
call util2
cd Faster-Whisper-XXL\

unset /q lockfile_present
call divider
:again
        call display-date-and-time-nicely
        rem echos %STAR% [lockfile_present=%lockfile_present%] More specifically, it is: 
        time /t

        iff not exist *.lock then 
                if "%lockfile_present%" == "1" (repeat 3 beep %+ call alarm-charge %+ window /flash)
                set  lockfile_present=0
                call less_important "No lockfile present right now!" big
        else
                set  lockfile_present=1
                type *.lock
        endiff

        pg faster-whisper|gr -v TCC
        @echo off

        echo.
        call divider

        sleep 3
goto :again

unset /q lockfile_present
popd