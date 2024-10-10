@Echo Off

rem Before Windows  7, we used a 32-bit sleep.exe in our %UTIL% folder, but
rem After  Windows XP, we redirect sleep commands to the internal *delay command:
        goto :%OS


:Windows_NT
:10
:11
:7
    
    goto :New_Way

    :Old_Way
            rem Cute screen output, except when we don't want it:
                    if "%2" eq "silent" (goto :silent_1)
                            rem  %ANSI_COLOR_DEBUG%%@CHAR[9201]%@CHAR[65039]%FAINT_ON% delay %* %FAINT_OFF%%ANSI_RESET%
                            echo %ANSI_COLOR_DEBUG%%EMOJI_STOPWATCH%%ZZZZZZ%%FAINT_ON% delay %* %FAINT_OFF%%ANSI_RESET%
                    :silent_1

            rem Do the actual sleep using the TCC internal DELAY command —- experimenting with new methods:
                    *delay %*
    
    
    :New_Way
            rem ⚠ Using default time of 3:
                    set SLEEP_TIME=3

            rem  But if a time is specified, use that time:
                    if  "%1" !=  ""  (set SLEEP_TIME=%1)

            rem Cheap way to make sure it's a number:
                    rem NUM_SECONDS=%@EVAL[%SLEEP_TIME]
                    set NUM_SECONDS=%SLEEP_TIME%

            echos %ANSI_SAVE_POSITION%%ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING%

            do second = %num_seconds% to 0 by -1 

                    set emoji_to_use=%emoji_stopwatch%

                    set                          last_digit=%@INSTR[%@EVAL[%@LEN[%second]-1],1,%second%]
                                            set last2digits=%@INSTR[%@EVAL[%@LEN[%second]-1],1,%second%]
                    if %@LEN[%second] gt 1 (set last2digits=%@INSTR[%@EVAL[%@LEN[%second]-2],2,%second%])
                    switch %last_digit%
                        case 0
                            set                            emoji_to_use=%EMOJI_TWELVE_OCLOCK%
                            if "%last2digits" == "10" (set emoji_to_use=%EMOJI_TEN_OCLOCK%)
                        case 1
                                                       set emoji_to_use=%EMOJI_ONE_OCLOCK%
                            if "%last2digits" == "11" (set emoji_to_use=%EMOJI_ELEVEN_OCLOCK%)
                        case 2
                                                       set emoji_to_use=%EMOJI_TWO_OCLOCK%
                            if "%last2digits" == "12" (set emoji_to_use=%EMOJI_TWELVE_OCLOCK%)
                        case 3
                            set emoji_to_use=%EMOJI_THREE_OCLOCK%
                        case 4
                            set emoji_to_use=%EMOJI_FOUR_OCLOCK%
                        case 5
                            set emoji_to_use=%EMOJI_FIVE_OCLOCK%
                        case 6
                            set emoji_to_use=%EMOJI_SIX_OCLOCK%
                        case 7
                            set emoji_to_use=%EMOJI_SEVEN_OCLOCK%
                        case 8
                            set emoji_to_use=%EMOJI_EIGHT_OCLOCK%
                        case 9
                            set emoji_to_use=%EMOJI_NINE_OCLOCK%
                        default
                            set emoji_to_use=%emoji_stopwatch%
                    endswitch

                    set  line=%emoji_to_use%%italics%%@cool_number[%second%]%italics_off%
                    echo %big_top%%line%      ``
                    echo %big_bot%%line%      ``
    
                    echos %@ANSI_MOVE_UP[2]
                    echos %@RANDOM_CURSOR_COLOR[]
                    echos %ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING%%ANSI_CURSOR_VISIBLE%
                    title %emoji_stopwatch% Sleeping %second% seconds...
                    if "%second" != "" (delay 1)

                    echos %ANSI_CURSOR_INVISIBLE% %+ rem Makes cursor blink in 1 row instead of being all bouncy

            enddo
            echo %CURSOR_RESET%%ANSI_RESET%%ANSI_EOL%%EMOJI_ALARM_CLOCK%%CHECK%%@ANSI_MOVE_DOWN[1]%@ANSI_MOVE_LEFT[4]%EMOJI_ALARM_CLOCK%%CHECK%
            goto :END


:XP
:2K
:ME
:98
:95
    %UTIL%\sleep %*
goto :END


:END
title TCC


