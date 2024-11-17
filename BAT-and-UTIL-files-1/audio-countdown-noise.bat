@Echo OFF

::::: CHECK USAGE:
    if "%1" eq "" .or. "%2" eq "" (gosub :Usage %+ goto :END)

::::: PARAMETERS:
    set ITEM_NUMBER=%1
    set TOTAL_ITEMS=%2
    set OVERRIDE_IN=%3
    set INTERVAL=2       %+ if "%OVERRIDE_IN%" ne "" set INTERVAL=%OVERRIDE_IN%    %+ REM //Allow overriding default note length
    

::::: DETERMINE BEEP FREQUENCY:
    SET NOTES=%BAT%\note-frequencies.dat %+ call validate-environment-variable NOTES
    SET BEEP_NOTES_TOTAL=%@LINES[%NOTES%]
    SET BEEP_RANGE_ITEM=%@EVAL[BEEP_NOTES_TOTAL / TOTAL_ITEMS]
    SET DONE_ITEMS_RANGE=%@EVAL[BEEP_RANGE_ITEM * ITEM_NUMBER]
    SET NOTE_LINENUM_TO_USE=%@EVAL[BEEP_NOTES_TOTAL-DONE_ITEMS_RANGE]
    SET FREQ_TO_USE=%@LINE[%NOTES%,%NOTE_LINENUM_TO_USE%]

::::: DEBUG:
    if %DEBUG% gt 0 goto :Debug
                    goto :Normal
        :Debug
            %COLOR_DEBUG%
                echo.
                echo *    BEEP_NOTES_TOTAL=%BEEP_NOTES_TOTAL%
                echo *         TOTAL ITEMS=%TOTAL_ITEMS%
                echo *     BEEP_RANGE_ITEM=%BEEP_RANGE_ITEM%
                echo *          DONE ITEMS=%ITEM_NUMBER%
                echo *    DONE_ITEMS_RANGE=%DONE_ITEMS_RANGE%
                echo * NOTE_LINENUM_TO_USE=%NOTE_LINENUM_TO_USE%
            %COLOR_SUCCESS%
                echo *      FREQ_TO_USE=%FREQ_TO_USE%
            %COLOR_NORMAL%
        :Normal

::::: DO THE BEEP (BEEP CAN ONLY TAKE INTEGER FREQUENCIES; TRUNCATE CALCULATED FREQUENCY):
    beep %@CEILING[%FREQ_TO_USE%] %INTERVAL%


goto :END
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Usage
            %COLOR_WARNING%
                echo.
                echo   USAGE:   %0 [itemNumber] [totalItems] [optional interval_override]
                echo.  EXAMPLE: %0 10 100   --- indicate the countdown if we are on item 10 out of 100. About 10% through
                echo.
                echo   This does an audio countdown, so we can listen to our progress.
                echo.
                echo.
            %COLOR_NORMAL%
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END

