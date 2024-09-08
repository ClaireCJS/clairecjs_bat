@Echo OFF 

unset /q FIRST_FILE_FOUND            %+ REM   do not leave results left over from previous searches!

set EXTENSION=%1
if %@FILES[%EXTENSION%] gt 0 goto :Found_YES
                             goto :Found_NO

    :Found_YES
        set FIRST_FILE_FOUND=%@EXECSTR[ffind /k /b %EXTENSION% | head -1] 
        %color_success% %+ echos * FIRST_FILE_FOUND=%FIRST_FILE_FOUND%
        %color_normal%  %+ echo.
    goto :END

    :Found_NO
        %color_alarm%  %+ echos * No matches for %EXTENSION%
        %color_normal% %+ echo.
    goto :END


:END
