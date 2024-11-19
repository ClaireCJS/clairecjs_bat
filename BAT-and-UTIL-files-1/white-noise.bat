@Echo Off
 on break cancel

:::: CONFIG:
        set    DEFAULT_SECONDS=1
        set BEEP_FREQUENCY_MIN=38
        set BEEP_FREQUENCY_MAX=9900
        set BEEP_INTERVALL_MIN=0
        set BEEP_INTERVALL_MAX=4
        set       EXITAFTER_WN=0                                                 %+ REM  A default that should probably never be changed!
        set COLOR_ALARM_ORIGINAL=%COLOR_ALARM%                                   %+ REM  Store, becuase we will be changing it.

:::: PARAMETERS:
         if      "%1"        ne "" (set SECONDS=%1)
         if      "%SECONDS%" eq "" (set SECONDS=%DEFAULT_SECONDS%)
         if %@LEN[%SECONDS%] gt  2 (set SECONDS=%DEFAULT_SECONDS%)               %+ REM annoyance protection from more than 99 seconds!
         if "%@UPPER[%1]" eq "EXITAFTER" .or. "%@UPPER[%2]" eq "EXITAFTER" (set EXITAFTER_WN=1)

::::: SET INTERVAL VALUE, WHICH IS NUM_SECONDS * 18:
        set INTERVAL_TO_USE=%@EVAL[%SECONDS% * 17]                               %+ REM Is actually 18, but allowing for overhead.
        if not defined INTERVAL_TO_USE (set INTERVAL_TO_USE=17)                  %+ REM in case our eval fails for some reason

:::: MINIMIZE IN THIS SITUATION::
        if "%EXITAFTER_WN%" eq "1" (window minimize)

:::: NOISE!!:
        set INTERVAL_USED=0
        :Beep_Again
                ::::: GENERATE RANDOM BEEP LENGTH & PITCH:
                        set BEEP_INTERVALL_TEMP=%@RANDOM[%BEEP_INTERVALL_MIN%,%BEEP_INTERVALL_MAX%]
                        set BEEP_FREQUENCY_TEMP=%@RANDOM[%BEEP_FREQUENCY_MIN%,%BEEP_FREQUENCY_MAX%]

                :::::: LOGARITHMIC PITCH SHIFT KLUDGE:
                        if  %@RANDOM[1,10] gt 6 (set BEEP_FREQUENCY_TEMP=%@FLOOR[%@EVAL[BEEP_FREQUENCY_TEMP / 10]] %+ color bright black on black %+ REM call print-if-debug `         * log_reduce, beep_freq now %BEEP_FREQUENCY_TEMP%`)
                        if  %@RANDOM[1,10] gt 9 (set BEEP_FREQUENCY_TEMP=%@FLOOR[%@EVAL[BEEP_FREQUENCY_TEMP / 10]] %+ color bright black on black %+ REM call print-if-debug `         * log_reduce, beep_freq now %BEEP_FREQUENCY_TEMP%`)
                        if  %@RANDOM[1,10] gt 8 (set BEEP_FREQUENCY_TEMP=%@FLOOR[%@EVAL[BEEP_FREQUENCY_TEMP / 10]] %+ color bright black on black %+ REM call print-if-debug `         * log_reduce, beep_freq now %BEEP_FREQUENCY_TEMP%`)
            :           if  %@RANDOM[1,10] gt 5 (set BEEP_FREQUENCY_TEMP=%@FLOOR[%@EVAL[BEEP_FREQUENCY_TEMP / 10]] %+ color bright black on black %+ REM call print-if-debug `         * log_reduce, beep_freq now %BEEP_FREQUENCY_TEMP%`)
                        if %BEEP_FREQUENCY_TEMP% lt %BEEP_FREQUENCY_MIN% set BEEP_FREQUENCY_TEMP=%@EVAL[BEEP_FREQUENCY_MIN +  %@RANDOM[0,20]]


                ::::: KEEP TRACK OF HOW MUCH TIME ("INTERVAL") WE HAVE USED, SO WE DON'T GO OVER:
                        set INTERVAL_USED=%@EVAL[INTERVAL_USED + BEEP_INTERVALL_TEMP]
                        REM DEBUG: echo call print-if-debug `   * temp-interval=%BEEP_INTERVALL_TEMP%, INTERVAL_USED=%INTERVAL_USED%, temp-freq = %BEEP_FREQUENCY_TEMP%`

                ::::: iF BEEP_INTERVALL_TEMP IS NOT 0, WE SHOULD DELAY AT LEAST 1 INTERVAL:
                        if %BEEP_INTERVALL_TEMP ne 0 (delay  /m  55)                          %+ REM 55ms = 1/18th second = interval of 1

                if %BEEP_INTERVALL_TEMP == 0 (goto :Silence)
                        rem If someone is asleep / we are in silent mode, we will make random-colored dots, instead of noise:
                                SET FG=%@RANDOM[0,15] 
                                :ReBG
                                SET BG=%@RANDOM[0,15]
                                if "%BG%" eq "%FG%" (goto :ReBG)
                        rem echo debug:        *beep %BEEP_FREQUENCY_TEMP% %BEEP_INTERVALL_TEMP%
                        if %sleeping ne 1 (    *beep %BEEP_FREQUENCY_TEMP% %BEEP_INTERVALL_TEMP%)
                        if %sleeping eq 1 (call beep %BEEP_FREQUENCY_TEMP% %BEEP_INTERVALL_TEMP%)
                :Silence
                echos %@randcursor[]
        if not %INTERVAL_USED% gt %INTERVAL_TO_USE% (goto :Beep_Again)

:::: CLEANUP:
        if "%SLEEPING%"     eq "1" (echo.                             )
        if "%EXITAFTER_WN%" eq "1" (echo (no longer: endlocal) %+ exit)
        echos %CURSOR_RESET%