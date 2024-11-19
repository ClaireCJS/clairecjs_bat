@Echo Off
 on break cancel

:REQUIRES: set-ansi.bat (which must have been run prior to this)


rem Just some hex colors I was experimenting with:
        SET HEX_MAGENTA_GOOD=FF00FF
        SET HEX_ORANGE_UNASSUMING=CF5500
        SET HEX_ORANGE_DARK_PUMPKIN=DF5500


rem Reference of permitted cursor shapes:
        rem ANSI_CURSOR_SHAPE_BLOCK_BLINKING=%ANSI_ESCAPE%1 q
        rem ANSI_CURSOR_SHAPE_BLOCK_STEADY=%ANSI_ESCAPE%2 q
        rem ANSI_CURSOR_SHAPE_DEFAULT=%ANSI_ESCAPE%0 q
        rem ANSI_CURSOR_SHAPE_UNDERLINE_BLINKING=%ANSI_ESCAPE%3 q
        rem ANSI_CURSOR_SHAPE_UNDERLINE_STEADY=%ANSI_ESCAPE%4 q
        rem ANSI_CURSOR_SHAPE_VERTICAL_BAR_BLINKING=%ANSI_ESCAPE%5 q
        rem ANSI_CURSOR_SHAPE_VERTICAL_BAR_STEADY=%ANSI_ESCAPE%6 q

rem Set variables to our preferences, wich will be used in this *and* other scripts:
        rem ANSI_PREFERRED_CURSOR_COLOR_HEX=%HEX_MAGENTA_GOOD% was too much like my wife's color
        set ANSI_PREFERRED_CURSOR_COLOR_HEX=%HEX_ORANGE_UNASSUMING%
        set ANSI_PREFERRED_CURSOR_SHAPE=%ANSI_CURSOR_SHAPE_BLOCK_BLINKING%

rem Actually change the cursor to our preferred color & shape, using the function defined in set-ansi.bat:
        set RECREATE_CURSOR=%@SET_CURSOR_COLOR_BY_HEX[%ANSI_PREFERRED_CURSOR_COLOR_HEX]%ANSI_PREFERRED_CURSOR_SHAPE%
                      echos %RECREATE_CURSOR%



