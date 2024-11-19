@echo on
@on break cancel

::::: MUST BE MANUALLY CONFIGURED HERE, EACH TIME WE MAKE A NEW SET OF GRAPHING SCRIPTS:
    set WHAT_WE_ARE_TRACKING=something

::::: PROCESS ARGUMENTS:
    echo ************************** [%%1=%2,%%2=%2]
    if "%1" ne "" (set TRACKING_VALUE_TEMP=%1)
    if "%2" ne "" (set TRACKING_VALUE_TEMP=%2)
    echo ************************** TRACKING_VALUE_TEMP is "%TRACKING_VALUE_TEMP%" %+ %COLOR_NORMAL%


::::: SETUP:
    call "plot-%WHAT_WE_ARE_TRACKING%-graph---plot-graph" DEFINE_CONSTANTS_ONLY
    call validate-environment-variables USERNAME TRACKING_FILE 
    call yyyymmddhhmm

::::: COLLECT VALUE IF WE DON'T ALREADY HAVE IT:    
    if "%TRACKING_VALUE_TEMP" ne "" (goto :AlreadyHaveValue)
        querybox /d /l3 "Just got new %WHAT_WE_ARE_TRACKING% data!" Enter your new %WHAT_WE_ARE_TRACKING%:  %%TRACKING_VALUE_TEMP
    :AlreadyHaveValue


::::: ADD DATA TO TRACKING FILE, THEN DISPLAY IT TO SHOW USER THAT IT WAS INDEED ADDED:
    echo %OUR_NAME%,%YYYYMMDDHHMM,%TRACKING_VALUE_TEMP% >>"%TRACKING_FILE%"
    gr   %OUR_NAME%                                       "%TRACKING_FILE%"


:END
    unset /q OUR_FILE
    unset /q TRACKING_VALUE_TEMP
