@Echo OFF

rem USAGE CHECK:
        if "%1"=="" goto :oops

rem PARAMETER CAPTURE:
        set PARAM=%@LEFT[1,%1]

rem ENVIRONMENT VALIDATION:
        call validate-in-path fast_cat grep gr set


rem CYGWIN BRANCHING:
        if "%CYGWIN%" eq "1" goto :cygwin_YES
        if "%CYGWIN%" ne ""  goto :cygwin_YES
            :cygwin_NO
                        call validate-in-path grep32
                        rem DEBUG: echo cygwin no "=%PARAM%%$"
                        rem grep32.exe can handle this:
                                                 (set|grep32 -i "=%PARAM%%$"|grep32 -i -v real|grep32 -i HD)
                        rem WHICHDRIVE=%@EXECSTR[(set|grep32 -i "=%PARAM%%$"|grep32 -i -v real|grep32 -i HD)]
            goto :END

            :cygwin_YES
                        rem cygwin's grep needed something a bit simpler;
                                                 set|grep -i hd[0-9]*[gt]|grep -i -v real|gr "=%PARAM%"|call fast_cat
                        rem WHICHDRIVE=%@EXECSTR[set|grep -i hd[0-9]*[gt]|grep -i -v real|gr "=%PARAM%"]
            goto :END




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :END

    :oops
        echo.
        call divider
        %color_advice%
        echo %blink_on%whichdrive.bat%blink_off%
        
        echo must give a drive letter as an argument, i.e. %ansi_color_bright_yellow%whichdrive c%ansi_color_yellow%%ansi_reset%
        call divider
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END


