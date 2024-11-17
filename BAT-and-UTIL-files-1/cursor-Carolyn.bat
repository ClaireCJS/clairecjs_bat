@Echo OFF

:REQUIRES: set-ansi.bat (which must have been run prior to this)

rem Reference of permitted cursor shapes:
        rem ANSI_CURSOR_SHAPE_BLOCK_BLINKING=%ANSI_ESCAPE%1 q
        rem ANSI_CURSOR_SHAPE_BLOCK_STEADY=%ANSI_ESCAPE%2 q
        rem ANSI_CURSOR_SHAPE_DEFAULT=%ANSI_ESCAPE%0 q
        rem ANSI_CURSOR_SHAPE_UNDERLINE_BLINKING=%ANSI_ESCAPE%3 q
        rem ANSI_CURSOR_SHAPE_UNDERLINE_STEADY=%ANSI_ESCAPE%4 q
        rem ANSI_CURSOR_SHAPE_VERTICAL_BAR_BLINKING=%ANSI_ESCAPE%5 q
        rem ANSI_CURSOR_SHAPE_VERTICAL_BAR_STEADY=%ANSI_ESCAPE%6 q

rem Set variables to our preferences, wich will be used in this *and* other scripts:
        set ANSI_PREFERRED_CURSOR_SHAPE=%ANSI_CURSOR_SHAPE_BLOCK_STEADY%
        set ANSI_PREFERRED_CURSOR_COLOR_HEX=8000DF

rem Actually change the cursor to our preferred color & shape, using the function defined in set-ansi.bat:
        set RECREATE_CURSOR=%ANSI_PREFERRED_CURSOR_SHAPE%%@SET_CURSOR_COLOR_BY_HEX[%ANSI_PREFERRED_CURSOR_COLOR_HEX%]
                      echos %RECREATE_CURSOR%


rem i need this hex defined before we set the prompt

