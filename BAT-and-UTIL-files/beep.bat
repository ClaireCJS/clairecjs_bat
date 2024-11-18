@Echo Off

rem title %0 %*


:USAGE: beep {freq}  {duration} ——— default invocation
:USAGE: beep highest {duration} ——— uses preset highest-audible-pick {may need to be tweaked per-computer}
:USAGE: beep lowest  {duration} ——— uses preset highest-audible-pick {may need to be tweaked per-computer}
:USAGE: beep  systemsoundtest   ——— perform a test of all the system sounds accessible by the TCC primitive *beep command


REM CONFIGURATION: SET THE HIGHEST BEEP ALLOWED:
        set  LOWEST_BEEP=39      %+ REM painstakingly tested this on 20230605 on computer DEMONA with Onkyo stereo 
        set HIGHEST_BEEP=13390   %+ REM painstakingly tested this on 20230605 on computer DEMONA with Onkyo stereo - 13391 actually is lower than 13390


set FREQ_OR_SYSTEMSOUND=%1
set DURATION=%2
set BEEPBAT_PARAM3=%3$


REM to test system sounds:
    if "%FREQ_OR_SYSTEMSOUND%" eq "test"       (goto :systemsoundtest)

REM we accept HIGHEST/LOWEST as a parameters to use the highest/lowest known beeps:
    set SKIP_FREQ_CHECK=0
    if "%FREQ_OR_SYSTEMSOUND%" eq "highest"    (set FREQ_OR_SYSTEMSOUND=%HIGHEST_BEEP% %+ set SKIP_FREQ_CHECK=1)
    if "%FREQ_OR_SYSTEMSOUND%" eq "lowest"     (set FREQ_OR_SYSTEMSOUND=%LOWEST_BEEP%  %+ set SKIP_FREQ_CHECK=1)

REM these system sound names are valid for *beep:
    if "%FREQ_OR_SYSTEMSOUND%" eq "question"        goto :parameters_have_been_validated
    if "%FREQ_OR_SYSTEMSOUND%" eq "exclamation"     goto :parameters_have_been_validated
    if "%FREQ_OR_SYSTEMSOUND%" eq "asterisk"        goto :parameters_have_been_validated
    if "%FREQ_OR_SYSTEMSOUND%" eq "hand"            goto :parameters_have_been_validated
    if "%FREQ_OR_SYSTEMSOUND%" eq "ok"              goto :parameters_have_been_validated
    if "%FREQ_OR_SYSTEMSOUND%" eq "systemsoundtest" goto :parameters_have_been_validated
                                                    

REM but also we have a value we don't want to go above based on testing our speakers/setup
if  %SKIP_FREQ_CHECK% ne 1 .and. defined HIGHEST_BEEP .and. %FREQ_OR_SYSTEMSOUND% gt %HIGHEST_BEEP% .and. "%FREQ_OR_SYSTEMSOUND%" ne "systemsoundtest" (
    call error "Beep value of %FREQ_OR_SYSTEMSOUND% is higher than HIGHEST_BEEP of %HIGHEST_BEEP, sorry!"
    rem call CANCELll / *cancel is really destructive to do right here
    goto :The_Very_END
)


:parameters_have_been_validated


REM branch based on awake/asleep value to not disturb others
    if "%SLEEPING%" eq "1" goto :Asleep
                           goto :Awake

                :Asleep
                        %COLOR_ALARM%   %+ echos %@randbg_soft[]%@randfg_soft[]!         %+ REM "see"  silent beeps
                        %COLOR_NORMAL%  %+ *beep 0 %DURATION% %BEEPBAT_PARAM3%           %+ REM "hear" silent beep to keep the same rhythm/duration -- makes a difference
                goto :END


                :Awake
                     rem *beep %FREQ_OR_SYSTEMSOUND% %DURATION% %BEEPBAT_PARAM3%         %+ REM Just beep normally
                         *beep %FREQ_OR_SYSTEMSOUND% %DURATION% %BEEPBAT_PARAM3%         %+ REM Just beep normally
                goto :END

                :systemsoundtest
                    echo.
                    call important "System sound test:"
                    echo.
                    for %snd in (asterisk exclamation hand ok question) (
                        set snd4print=%snd%
                        if "%snd%" eq "asterisk"    set "snd4print=%SND%    (windows: 'Asterisk')"
                        if "%snd%" eq "exclamation" set "snd4print=%SND% (windows: 'Exclamation')"
                        if "%snd%" eq "ok"          set "snd4print=%SND%          (windows: 'Default Beep')"
                        if "%snd%" eq "hand"        set "snd4print=%SND%        (windows: 'Program Error')"
                        if "%snd%" eq "question"    set "snd4print=%SND%    (windows: 'Question')"
                        call important_less "     - %snd4print%"
                        call beep.bat               %snd%
                        call sleep 1
                    )
                goto :END

:END


REM Add on our own options to /?
    if "%FREQ_OR_SYSTEMSOUND%" eq "/?" (
        echo.
        call important_less "Bonus usages:"
        %COLOR_ADVICE%
        echo       beep highest {duration}
        echo       beep lowest  {duration}
        echo       beep systemsoundtest
        %COLOR_NORMAL%

    )
:The_Very_END
