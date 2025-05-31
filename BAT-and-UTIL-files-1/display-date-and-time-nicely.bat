@on break cancel
@Echo Off
 echo.

:DESCRIPTION: This 25-year-old BAT file finally “graduated” on 12/30/2024. Don’t think there’s any further we can really go.. other than displaying seconds!

rem Minimum number of columns a date can take up:
        set DEFAULT_RIGHT_COLUMN=35 %+ rem 05/04/2025



rem Test suites for a date with each different length from 35–45:
        iff "%1" eq "test" then
                call yyyymmdd              %+ rem Preserve current date
                date 05/04/2025 %+ call %0 %+ rem len=35
                date 05/16/2025 %+ call %0 %+ rem len=36
                date 05/01/2025 %+ call %0 %+ rem len=37
                date 05/15/2025 %+ call %0 %+ rem len=38
                date 05/14/2025 %+ call %0 %+ rem len=39
                date 10/10/2025 %+ call %0 %+ rem len=40
                date 12/30/2024 %+ call %0 %+ rem len=41
                date 09/02/2024 %+ call %0 %+ rem len=42
                date 12/20/2025 %+ call %0 %+ rem len=43
                date 12/17/2025 %+ call %0 %+ rem len=44
                date 09/17/2025 %+ call %0 %+ rem len=45
                date %MM%/%DD%/%YYYY%      %+ rem Restore current date
                goto :END
        elseiff "%1" eq "test2" then
                call yyyymmddhhmmss         %+ rem Preserve current date & time
                time 12:01am %+ call %0 
                time 01:08am %+ call %0 
                time 02:18am %+ call %0 
                time 03:18am %+ call %0 
                time 04:28am %+ call %0 
                time 05:28am %+ call %0 
                time 06:38am %+ call %0 
                time 07:38am %+ call %0 
                time 08:48am %+ call %0 
                time 09:48am %+ call %0 
                time 10:08am %+ call %0 
                time 11:58am %+ call %0 
                time 12:08pm %+ call %0 
                time 01:08pm %+ call %0 
                time 02:18pm %+ call %0 
                time 03:18pm %+ call %0 
                time 04:28pm %+ call %0 
                time 05:08pm %+ call %0 
                time 06:38pm %+ call %0 
                time 07:38pm %+ call %0 
                time 08:08pm %+ call %0 
                time 09:48pm %+ call %0 
                time 10:08pm %+ call %0 
                time 11:58pm %+ call %0 
                date %MM%/%DD%/%YYYY%     %+ rem Restore current date & time
                time %HH%:%MIN%
                goto :END
        elseiff "%1" ne "" then
                %color_advice%
                call warning "%0 should only be called with options “test” to test boxing code or “test2” to test am/pm processing"
                pause /# 3
                %color_normal%
                goto :END
        endiff


rem redundant, defined elsewhere, redefined here for portability:
        if "" eq "%@function[ansi_fg_rgb]" function ANSI_FG_RGB=`%@CHAR[27][38;2;%1;%2;%3m`           
        if not defined ANSI_RESET               set ANSI_RESET=%@CHAR[27][0m
        if not defined FAINT_ON                 set FAINT_ON=%@CHAR[27][2m
        if not defined FAINT_OFF                set FAINT_OFF=%@CHAR[27][22m
        if not defined EMOJI_CALENDAR           set EMOJI_CALENDAR=%@CHAR[55357]%@CHAR[56517]
        if not defined EMOJI_TEAR_OFF_CALENDAR  set EMOJI_TEAR_OFF_CALENDAR=%@CHAR[55357]%@CHAR[56518]
        if not defined EMOJI_ONE_OCLOCK         set EMOJI_ONE_OCLOCK=%@CHAR[55357]%@CHAR[56656]
        if not defined EMOJI_TWO_OCLOCK         set EMOJI_TWO_OCLOCK=%@CHAR[55357]%@CHAR[56657]
        if not defined EMOJI_THREE_OCLOCK       set EMOJI_THREE_OCLOCK=%@CHAR[55357]%@CHAR[56658]
        if not defined EMOJI_FOUR_OCLOCK        set EMOJI_FOUR_OCLOCK=%@CHAR[55357]%@CHAR[56659]
        if not defined EMOJI_FIVE_OCLOCK        set EMOJI_FIVE_OCLOCK=%@CHAR[55357]%@CHAR[56660]
        if not defined EMOJI_SIX_OCLOCK         set EMOJI_SIX_OCLOCK=%@CHAR[55357]%@CHAR[56661]
        if not defined EMOJI_SEVEN_OCLOCK       set EMOJI_SEVEN_OCLOCK=%@CHAR[55357]%@CHAR[56662]
        if not defined EMOJI_EIGHT_OCLOCK       set EMOJI_EIGHT_OCLOCK=%@CHAR[55357]%@CHAR[56663]
        if not defined EMOJI_NINE_OCLOCK        set EMOJI_NINE_OCLOCK=%@CHAR[55357]%@CHAR[56664]
        if not defined EMOJI_TEN_OCLOCK         set EMOJI_TEN_OCLOCK=%@CHAR[55357]%@CHAR[56665]
        if not defined EMOJI_ELEVEN_OCLOCK      set EMOJI_ELEVEN_OCLOCK=%@CHAR[55357]%@CHAR[56666]
        if not defined EMOJI_TWELVE_OCLOCK      set EMOJI_TWELVE_OCLOCK=%@CHAR[55357]%@CHAR[56667]



rem Convert our day to the appropriate Calendar emoji —— There’s a 31ˢᵗ-specific emoji to use on the 31ˢᵗ, and a more generic calendar emoji for the other days:
        set                  CAL_EMO_TO_USE=%EMOJI_CALENDAR%
        if %_DAY  == 31 (set CAL_EMO_TO_USE=%EMOJI_TEAR_OFF_CALENDAR%)


rem Convert our hour to the appropriate clock emoji —— round to the nearest hour
        set                                       TIM_EMO_TO_USE=%EMOJI_NINE_OCLOCK%
        if %_HOUR == 00 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TWELVE_OCLOCK%)
        if %_HOUR == 00 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_ONE_OCLOCK%)
        if %_HOUR == 01 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_ONE_OCLOCK%)
        if %_HOUR == 01 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_TWO_OCLOCK%)
        if %_HOUR == 02 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TWO_OCLOCK%)
        if %_HOUR == 02 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_THREE_OCLOCK%)
        if %_HOUR == 03 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_THREE_OCLOCK%)
        if %_HOUR == 03 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_FOUR_OCLOCK%)
        if %_HOUR == 04 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_FOUR_OCLOCK%)
        if %_HOUR == 04 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_FIVE_OCLOCK%)
        if %_HOUR == 05 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_FIVE_OCLOCK%)
        if %_HOUR == 05 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_SIX_OCLOCK%)
        if %_HOUR == 06 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_SIX_OCLOCK%)
        if %_HOUR == 06 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_SEVEN_OCLOCK%)
        if %_HOUR == 07 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_SEVEN_OCLOCK%)
        if %_HOUR == 07 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_EIGHT_OCLOCK%)
        if %_HOUR == 08 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_EIGHT_OCLOCK%)
        if %_HOUR == 08 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_NINE_OCLOCK%)
        if %_HOUR == 09 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_NINE_OCLOCK%)
        if %_HOUR == 09 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_TEN_OCLOCK%)
        if %_HOUR == 10 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TEN_OCLOCK%)
        if %_HOUR == 10 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_ELEVEN_OCLOCK%)
        if %_HOUR == 11 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_ELEVEN_OCLOCK%)
        if %_HOUR == 11 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_TWELVE_OCLOCK%)
        if %_HOUR == 12 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TWELVE_OCLOCK%)
        if %_HOUR == 12 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_ONE_OCLOCK%)
        if %_HOUR == 13 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_ONE_OCLOCK%)
        if %_HOUR == 13 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_TWO_OCLOCK%)
        if %_HOUR == 14 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TWO_OCLOCK%)
        if %_HOUR == 14 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_THREE_OCLOCK%)
        if %_HOUR == 15 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_THREE_OCLOCK%)
        if %_HOUR == 15 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_FOUR_OCLOCK%)
        if %_HOUR == 16 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_FOUR_OCLOCK%)
        if %_HOUR == 16 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_FIVE_OCLOCK%)
        if %_HOUR == 17 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_FIVE_OCLOCK%)
        if %_HOUR == 17 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_SIX_OCLOCK%)
        if %_HOUR == 18 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_SIX_OCLOCK%)
        if %_HOUR == 18 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_SEVEN_OCLOCK%)
        if %_HOUR == 19 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_SEVEN_OCLOCK%)
        if %_HOUR == 19 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_EIGHT_OCLOCK%)
        if %_HOUR == 20 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_EIGHT_OCLOCK%)
        if %_HOUR == 20 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_NINE_OCLOCK%)
        if %_HOUR == 21 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_NINE_OCLOCK%)
        if %_HOUR == 21 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_TEN_OCLOCK%)
        if %_HOUR == 22 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TEN_OCLOCK%)
        if %_HOUR == 22 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_ELEVEN_OCLOCK%)
        if %_HOUR == 23 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_ELEVEN_OCLOCK%)
        if %_HOUR == 23 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_TWELVE_OCLOCK%)
        if %_HOUR == 24 .and. %_MINUTE lt 31 (set TIM_EMO_TO_USE=%EMOJI_TWELVE_OCLOCK%)
        if %_HOUR == 24 .and. %_MINUTE gt 31 (set TIM_EMO_TO_USE=%EMOJI_ONE_OCLOCK%)


rem Assemble beginning of date line:
        set MSG=%CAL_EMO_TO_USE% %faint_on%The%faint_off% date %faint_on%is:%faint_off% %@ANSI_FG_RGB[255,200,200]%_DOW%

rem Convert %_DOW (Day Of Week) to English day-of-week:
        if "%_DOW"=="Tue" goto   :Tuesday
        if "%_DOW"=="Wed" goto :Wednesday
        if "%_DOW"=="Thu" goto  :Thursday
        if "%_DOW"=="Sat" goto  :Saturday
                          goto :Normalday
        :Wednesday
            set MSG=%MSG%nes
            goto :Normalday
        :Thursday
            set MSG=%MSG%rs
            goto :Normalday
        :Tuesday
            set MSG=%MSG%s
            goto :Normalday
        :Saturday
            set MSG=%MSG%ur
            goto :Normalday
        :Normalday
            set MSG=%MSG%day,

rem Convert %_MONTH to English word:
        if "%_MONTH"=="1"  set MSG=%MSG% January %_DAY, %_YEAR
        if "%_MONTH"=="2"  set MSG=%MSG% February %_DAY, %_YEAR
        if "%_MONTH"=="3"  set MSG=%MSG% March %_DAY, %_YEAR
        if "%_MONTH"=="4"  set MSG=%MSG% April %_DAY, %_YEAR
        if "%_MONTH"=="5"  set MSG=%MSG% May %_DAY, %_YEAR
        if "%_MONTH"=="6"  set MSG=%MSG% June %_DAY, %_YEAR
        if "%_MONTH"=="7"  set MSG=%MSG% July %_DAY, %_YEAR
        if "%_MONTH"=="8"  set MSG=%MSG% August %_DAY, %_YEAR
        if "%_MONTH"=="9"  set MSG=%MSG% September %_DAY, %_YEAR
        if "%_MONTH"=="10" set MSG=%MSG% October %_DAY, %_YEAR
        if "%_MONTH"=="11" set MSG=%MSG% November %_DAY, %_YEAR
        if "%_MONTH"=="12" set MSG=%MSG% December %_DAY, %_YEAR


rem Cosmetics: Spacing:
        unset /q ADDITIONAL_JUNK
        set                                LEN=%@LEN[%@stripansi[%MSG]]
        set  PROPOSED_RIGHT_COLUMN=%@EVAL[%LEN + 2]
        set           RIGHT_COLUMN=%DEFAULT_RIGHT_COLUMN%
        iff  %PROPOSED_RIGHT_COLUMN gt %RIGHT_COLUMN% then
                set RIGHT_COLUMN=%PROPOSED_RIGHT_COLUMN%
                set DIFFERENCE=%@EVAL[%PROPOSED_RIGHT_COLUMN - %DEFAULT_RIGHT_COLUMN%]
                if %RIGHT_COLUMN gt %DIFFERENCE% set ADDITIONAL_JUNK=%TIM_EMO_TO_USE%
                if %DIFFERENCE%  gt      2       set ADDITIONAL_JUNK=%ADDITIONAL_JUNK%%TIM_EMO_TO_USE%
                if %DIFFERENCE%  gt      6       set ADDITIONAL_JUNK=%ADDITIONAL_JUNK%%TIM_EMO_TO_USE%
                if %DIFFERENCE%  gt     10       set ADDITIONAL_JUNK=%ADDITIONAL_JUNK%%TIM_EMO_TO_USE%
        endiff
        rem call debug "len=%len, difference=%difference%"

rem Finish assembling date line:
        set MSG=%MSG%%@ANSI_MOVE_TO_COL[%RIGHT_COLUMN%]%CAL_EMO_TO_USE%%ANSI_RESET%


rem Display openining line of clocks + date line:
        call bigecho "%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%ADDITIONAL_JUNK%"
        echo %MSG


rem Start assembling time line:
        set MSG=%TIM_EMO_TO_USE% %faint%The%faint_off% time %faint%is:%faint_off% %@ANSI_FG_RGB[175,220,175]``


rem Determine AM/PM:
        iff %_HOUR lt 12 then
                iff %_HOUR eq 0 then
                    set MSG=%MSG%12:
                elseiff %_HOUR lt 10 then
                    set MSG=%MSG%0%_HOUR:
                else
                    set MSG=%MSG%%_HOUR:
                endiff
        elseiff %_HOUR eq 12 then
                set MSG=%MSG%12:
        elseiff %_HOUR gt 12 then
                set MSG=%MSG%%@eval[%_HOUR-12]:
        else
                call fatal_error "this should never happen"
        endiff


rem Pad minutes with 0 if necessary:
        if %_MINUTE lt 10 set MSG=%MSG%0
        set MSG=%MSG%%_MINUTE


rem Add “a” or “p” for AM/PM, then add the “m.”:
        iff %_HOUR gt 11 then
                set MSG=%MSG% p
        else
                set MSG=%MSG% a
        endiff
        set MSG=%MSG%.m.


rem Create time line to display:
        echo %MSG%%@ANSI_MOVE_TO_COL[%RIGHT_COLUMN%]%TIM_EMO_TO_USE%


rem End with final line of clocks:
        call bigecho "%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%TIM_EMO_TO_USE%%ADDITIONAL_JUNK%"


rem Cleanup:
        :END
        unset /q ADDITIONAL_JUNK
        if defined CURSOR_RESET echos %CURSOR_RESET%


