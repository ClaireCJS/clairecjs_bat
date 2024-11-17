@Echo OFF

:::::::::: THIS IS NOT MEANT TO BE CALLED DIRECTLY!
    if "%START_DATE_YYYYMMDD%" eq "" (goto :Fail)
    if "%NATURE%"              eq "" (goto :Fail)




::::: REFORMAT DATE FOR THE STUPID MAKEAGE FUNCTION:
    set START_DATE_YYYY=%@SUBSTR[%START_DATE_YYYYMMDD%,0,4]
    set START_DATE_YY=%@SUBSTR[%START_DATE_YYYYMMDD%,2,2]
    set START_DATE_MM=%@SUBSTR[%START_DATE_YYYYMMDD%,4,2]
    set START_DATE_DD=%@SUBSTR[%START_DATE_YYYYMMDD%,6,2]
    set START_DATE_MMDDYY=%START_DATE_MM%/%START_DATE_DD%/%START_DATE_YY%
    set START_DATE_YYYY_MM_DD=%START_DATE_YYYY%/%START_DATE_MM%/%START_DATE_DD%

::::: CALCULATE THE TIME:
    :et TIME=%@EVAL[(%@makeage[%_date] - %@makeage[%START_DATE_MMDDYY])       /1000/100/60/60/24/365.2422/100]
    set TIME=%@EVAL[(%@makeage[%_date] - %@makeage[%START_DATE_YYYY_MM_DD,4]) /1000/100/60/60/24/365.2422/100]

::::: DEBUG STUFF:
    :: echo TEST: START_DATE_YY="%START_DATE_YY%"
    :: echo TEST: START_DATE_YYYY="%START_DATE_YYYY%"
    :: echo TEST: START_DATE_YYYY_MM_DD=%START_DATE_YYYY_MM_DD% 
    :: :option 4=ISO (yyyy-mm-dd) format
    :: echo TEST: eval= @EVAL[(%@makeage[%_date] - %@makeage[%START_DATE_YYYY_MM_DD,4]) /1000/100/60/60/24/365/100]
    :: echo TEST: eval=%@EVAL[(%@makeage[%_date] - %@makeage[%START_DATE_YYYY_MM_DD,4]) /1000/100/60/60/24/365/100]

::::: DISPLAY RESULT:
    set DISPLAY_YRS=%@FORMATN[1.3,%TIME%]
    %COLOR_IMPORTANT_LESS% %+ echo. %+ echo %EMOJI_TEAR_OFF_CALENDAR% %faint_on%%BOLD_ON%Start date: %faint_off%%START_DATE_YYYYMMDD%
    %COLOR_IMPORTANT%      %+ echo. %+ echo %EMOJI_INPUT_NUMBERS% %DISPLAY_YRS%%FAINT_ON% yrs %NATURE%%faint_off%
    %COLOR_NORMAL%

::::: STORE RESULT IN ENVIRONMENT:
    set LAST_CALCULATED_AGE=%TIME%
    set LAST_CALCULATED_AGE_NATURE=%NATURE%
    set LAST_DISPLAY_YRS=%DISPLAY_YRS%
    set LAST_DISPLAY_TEXT=%DISPLAY_YRS%yrs
    set LAST_DISPLAY_NUM=%DISPLAY_YRS%
    set LAST_DISPLAY=%LAST_DISPLAY_TEXT%



goto :END

                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                :FAIL
                    %COLOR_WARNING%
                        echo.
                        echo FATAL ERROR! $0 called without proper environment-variable parameters
                    %COLOR_IMPORTANT%
                        echo.
                        echo Example usage:
                        echo.
                    %COLOR_ADVICE%

                    echo set NATURE=anniversary
                    echo set START_DATE_YYYYMMDD=19920210
                    echo call %0
                goto :END
                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
    unset /q NATURE
    unset /q START_DATE_YYYYMMDD
