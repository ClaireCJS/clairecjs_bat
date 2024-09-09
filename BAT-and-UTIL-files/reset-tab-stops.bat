@Echo OFF

rem Configure defaults:
        set NUM_TABS_TO_REGEN=100
        set OUR_TAB_WIDTH_TO_USE=4
        if "%1" ne "" (set OUR_TAB_WIDTH_TO_USE=%1)

rem Validate environment, but only once:
        if %validated_reset_tab_stops ne 1 (
            call validate-env-vars  ANSI_TABSTOP_SET_COL OUR_TAB_WIDTH_TO_USE NUM_TABS_TO_REGEN ANSI_POSITION_SAVE ANSI_POSITION_RESTORE
            call validate-functions ANSI_MOVE_TO_COL
            set  validated_reset_tab_stops=1
        )

rem Reset the tabs:
        echo %ANSI_POSITION_SAVE%
        set CHARS_TO_OUTPUT=%@EVAL[%NUM_TABS_TO_REGEN * %OUR_TAB_WIDTH_TO_USE]
        do xx = 1 to %CHARS_TO_OUTPUT% by 1 (
            rem echos %@ANSI_MOVE_TO_COL[%@EVAL[%xx*%OUR_TAB_WIDTH_TO_USE+1]]
            rem echos %ANSI_TABSTOP_SET_COL%
            echos %@ANSI_MOVE_TO_COL[%xx]
            if "%@EVAL[%xx mod %column_width]" == "1" (echos %ANSI_TABSTOP_SET_COL%)
            if "%@EVAL[%xx mod %column_width]" != "1" (echos %ANSI_TABSTOP_CLR_COL%)
        )
        echo.
        echos %ANSI_POSITION_RESTORE%

rem Display our handiwork:
        call display-tab-stops %NUM_TABS_TO_REGEN%

