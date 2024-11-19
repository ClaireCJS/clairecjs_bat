@Echo OFF
@on break cancel

rem Configure defaults:
        set                OUR_TAB_WIDTH_TO_USE=%DEFAULT_TAB_STOP_WIDTH%
        if "%1" ne "" (set OUR_TAB_WIDTH_TO_USE=%1)
        set                   NUM_TABS_TO_REGEN=100
        if "%2" ne "" (set    NUM_TABS_TO_REGEN=%2)

rem Validate environment, but only once:
        if %validated_reset_tab_stops ne 1 .or. "%3" eq "validate" (
            call validate-env-vars  ANSI_TABSTOP_SET_COL OUR_TAB_WIDTH_TO_USE NUM_TABS_TO_REGEN ANSI_POSITION_SAVE ANSI_POSITION_RESTORE ANSI_TABSTOP_CLR_COL ANSI_TABSTOP_SET_COL STAR BLINK_ON BLINK_OFF ANSI_COLOR_SUCCESS PARTY_POPPER DEFAULT_TAB_STOP_WIDTH ANSI_TABSTOP_RESET
            call validate-functions ANSI_MOVE_UP ANSI_MOVE_TO_COL
            set  validated_reset_tab_stops=1
        )

rem One reset method exists, but it's hardcoded(?) at a tab stop of 8, so we'll do that for a quickfix first, before it gets complicated:
        echos ANSI_TABSTOP_RESET

rem (Cosmetic Voodoo)
        set                   XX=2
        repeat               %XX% echo.
        echos %@ANSI_MOVE_UP[%XX]

rem Let us know what we're doing:
        echo %ANSI_POSITION_SAVE%%STAR% %blink_on%%ansi_color_important%Regenerating tab stops...

rem Q: Traverse how many columns? A: maximum of either NUM_TABS*WIDTH or how many columns 
        set CHARS_TO_OUTPUT=%@EVAL[%NUM_TABS_TO_REGEN * %OUR_TAB_WIDTH_TO_USE]
        if %CHARS_TO_OUTPUT gt %_COLUMNS (set CHARS_TO_OUTPUT=%_COLUMNS)

rem Loop through each column and set it's tab-stop status on or off, tracking how many we do:
        set NUM_REGENERATED=0
        do xx = 1 to %CHARS_TO_OUTPUT% by 1 (
            echos %@ANSI_MOVE_TO_COL[%xx]
            if "%@EVAL[%xx mod %OUR_TAB_WIDTH_TO_USE]" != "1" (echos %ANSI_TABSTOP_CLR_COL%)
            if "%@EVAL[%xx mod %OUR_TAB_WIDTH_TO_USE]" == "1" (echos %ANSI_TABSTOP_SET_COL% 
                                             set NUM_REGENERATED=%@EVAL[%NUM_REGENERATED+1])
        )        

rem (Cosmetic Voodoo)
        echo.
        echos %ANSI_POSITION_RESTORE%%ANSI_MOVE_UP0%
        echos %ANSI_COLOR_SUCCESS%%PARTY_POPPER% DONE!%ANSI_CLEAR_TO_EOL%
        echos %@ANSI_MOVE_TO_COL[1]%ANSI_CLEAR_TO_EOL%                    %+ rem This line kinda negates the last one by erasing it... 😂

rem Display our handiwork:
        set SILENT=0
        if "%1" eq "silent" .or. "%2" eq "silent" .or. "%3" eq "silent" .or. "%4" eq "silent" (set SILENT=1)
        if %SILENT ne 1 (
            call display-tab-stops %@EVAL[%NUM_REGENERATED%-1]
            rem We do NUM_REGENERATED-1 because displaying 2 digits can wrap to the next line
        )

