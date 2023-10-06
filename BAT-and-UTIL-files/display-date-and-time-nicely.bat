@Echo OFF
 echo.


rem redundant, defined elsewhere, redefined here for portability:
        function ANSI_FG_RGB=`%@CHAR[27][38;2;%1;%2;%3m`           
        set ANSI_RESET=%@CHAR[27][0m
        set FAINT_ON=%@CHAR[27][2m
        set FAINT_OFF=%@CHAR[27][22m
        set EMOJI_CALENDAR=%@CHAR[55357]%@CHAR[56517]
        set EMOJI_TEAR_OFF_CALENDAR=%@CHAR[55357]%@CHAR[56518]
        set EMOJI_ONE_OCLOCK=%@CHAR[55357]%@CHAR[56656]
        set EMOJI_TWO_OCLOCK=%@CHAR[55357]%@CHAR[56657]
        set EMOJI_THREE_OCLOCK=%@CHAR[55357]%@CHAR[56658]
        set EMOJI_FOUR_OCLOCK=%@CHAR[55357]%@CHAR[56659]
        set EMOJI_FIVE_OCLOCK=%@CHAR[55357]%@CHAR[56660]
        set EMOJI_SIX_OCLOCK=%@CHAR[55357]%@CHAR[56661]
        set EMOJI_SEVEN_OCLOCK=%@CHAR[55357]%@CHAR[56662]
        set EMOJI_EIGHT_OCLOCK=%@CHAR[55357]%@CHAR[56663]
        set EMOJI_NINE_OCLOCK=%@CHAR[55357]%@CHAR[56664]
        set EMOJI_TEN_OCLOCK=%@CHAR[55357]%@CHAR[56665]
        set EMOJI_ELEVEN_OCLOCK=%@CHAR[55357]%@CHAR[56666]
        set EMOJI_TWELVE_OCLOCK=%@CHAR[55357]%@CHAR[56667]



rem calendar/day emoji
        set                  CAL_EMO_TO_USE=%EMOJI_CALENDAR%
        if %_DAY  == 31 (set CAL_EMO_TO_USE=%EMOJI_TEAR_OFF_CALENDAR%)

rem clock/time emoji
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



set MSG=%CAL_EMO_TO_USE% %faint_on%The%faint_off% date %faint_on%is:%faint_off% %@ANSI_FG_RGB[255,200,200]%_DOW%

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

set MSG=%MSG%%ANSI_RESET%


echo %MSG
set MSG=%TIM_EMO_TO_USE% %faint%The%faint_off% time %faint%is:%faint_off% %@ANSI_FG_RGB[175,220,175]``
iff %_HOUR gt 11 goto :PM
:AM
    iff %_HOUR ne 0 goto :NormalNormal
:WeirdWeird
    set MSG=%MSG%12:
    goto :Minutes
:NormalNormal
    set MSG=%MSG%%_HOUR:
    goto :Minutes
:PM
REM echo [PM]
iff %_HOUR lt 12 set MSG=%MSG%%@eval[%_HOUR-12]:
iff %_HOUR eq 12 set MSG=%MSG%12:
iff %_HOUR gt 12 set MSG=%MSG%%@eval[%_HOUR-12]:

:Minutes
    iff %_MINUTE gt 9 goto :NoZero
:Zero
    set MSG=%MSG%0
:NoZero
    set MSG=%MSG%%_MINUTE


iff %_HOUR gt 11 goto :P
    :A
        set MSG=%MSG% a
        goto :M
    :P
        set MSG=%MSG% p
    :M
        set MSG=%MSG%.m.


echo %MSG%
