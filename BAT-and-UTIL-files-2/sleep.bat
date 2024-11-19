@Echo Off
 on break cancel

:USAGE: sleep <seconds to sleep> [silent/clock] [custom clock message with special substitution for {seconds}]

iff "%1" eq "" then
        repeat 10 echo.
        call divider
        %COLOR_ADVICE%
        echo USAGE: sleep 60 ————————————————————————————————————————— sleeps 60 seconds
        echo USAGE: sleep 60 clock ——————————————————————————————————— sleeps 60 seconds, displaying a clock.  The "wait" command created by wait.bat uses this.
        echo USAGE: sleep 60 clock "wait a min" —————————————————————— sleeps 60 seconds, displaying a clock, with a custom message next to it.
        echo USAGE: sleep 60 clock "Only {seconds} seconds left!" ———— sleeps 60 seconds, displaying a clock, with a custom message next to it, with dynamic substitution of remaining seconds replacing "{seconds}"
        call divider
        pause
        goto :END
endiff

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

            rem And if silent mode is specified, do that:
                    set silent=1
                    if "%2" eq "silent" (set silent=1) 
                    if "%2" eq "clock"  (set silent=0) 

            rem And grab any optional message for clock-mode:
                    unset   /q         SLEEP_MESSAGE
                    if "%3" ne "" (set SLEEP_MESSAGE=%%@randfg_soft[]%@UNQUOTE[%3$])

            rem Temporarily change cursor to the vertical blinking bar, which is the least obtustive to the animated clock:
                    if %silent ne 1 (echos %ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING%) else (echos %ANSI_CURSOR_CHANGE_TO_BLOCK_STEADY%)

            do second = %SLEEP_TIME% to 0 by -1 

                    rem Animate our sleep/wait countdown:                        
                            iff %silent ne 1 then
                                    rem Determine which clock emoji to use at this second:
                                            set emoji_to_use=%EMOJI_STOPWATCH%
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
                                                    set emoji_to_use=%EMOJI_STOPWATCH%
                                            endswitch

                                    rem Decorate our optional message:
                                                                       set SLEEP_MESSAGE_PREFIX=
                                            if "" != "%SLEEP_MESSAGE%" set SLEEP_MESSAGE_PREFIX=%%@randfg_soft[] ... ``

                                    rem Perform sleep message substitutions:
                                            set SLEEP_MESSAGE_TO_USE=%@REReplace[\{seconds\},%second%,%SLEEP_MESSAGE%]

                                    rem Assemble our clock + countdown + optional message:
                                            set  line=%emoji_to_use%%italics%%@cool_number[%second%]%italics_off%%SLEEP_MESSAGE_PREFIX%%SLEEP_MESSAGE_TO_USE%

                                    rem And echo it as double-height text, along with some extra spaces to erase digits leftover when counting down to a fewer-digit number, i.e. 10->9, 100->99, 1000->999:
                                            echo %big_top%%line%      ``
                                            echo %big_bot%%line%      ``

                                    rem Move back to the position we started at, so we can draw over ourselves to animate:
                                            echos %@ANSI_MOVE_UP[2]

                                    rem Set cursor color to be a random-colored vertical blinking bar, now visible:
                                            echos %@RANDOM_CURSOR_COLOR[]%ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING%%ANSI_CURSOR_VISIBLE%

                                    rem Update window title:
                                            title %emoji_to_use% Wait: %second% more seconds %emoji_to_use%

                                    rem Do our actual sleep:
                                            if "%second" != "0" (*delay 1)

                                    rem Turn the cursor off, which makes the blinking stay in a consistent location instead of being all bouncy:
                                            if %silent ne 1 (echos %ANSI_CURSOR_INVISIBLE%) 
                            else
                                    rem Update window title:
                                            title %emoji_to_use% Sleep: %second% more seconds %emoji_to_use%

                                    rem Do the actual 'sleep':
                                            rem echos %@RANDOM_CURSOR_COLOR[]%ANSI_CURSOR_CHANGE_TO_BLOCK_STEADY%
                                            echos %@randcursor[]
                                            if "%second" != "0" (*delay 1)
                            endiff




            enddo

            
            rem Reset our cursor back to the user-preferred shape & color, reset all ansi status, draw our final clock, and leave us in the right place:
                    iff %silent ne 1 then
                        echo %CURSOR_RESET%%ANSI_RESET%%ANSI_EOL%%EMOJI_ALARM_CLOCK%%CHECK%%ANSI_SAVE_POSITION%%ANSI_ERASE_TO_END_OF_LINE%%ANSI_RESTORE_POSITION%%@ANSI_MOVE_DOWN[1]%@ANSI_MOVE_LEFT[4]%EMOJI_ALARM_CLOCK%%CHECK%%ANSI_ERASE_TO_END_OF_LINE%
                    else
                        echos %CURSOR_RESET%%ANSI_RESET%
                    endiff

            goto :END







rem —————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
                    :XP
                    :2K
                    :ME
                    :98
                    :95
                            %UTIL%\sleep %*
                    goto :END
rem —————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————




:END
    title TCC

