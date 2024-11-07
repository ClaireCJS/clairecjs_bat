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
                                                 (set|:u8 grep32 -i "=%PARAM%%$"|:u8 grep32 -i -v real|:u8 grep32 -i HD) |:u8 fast_cat
            goto :END

            :cygwin_YES
                        rem cygwin's grep needed something a bit simpler;
                                                (set|:u8grep -i hd[0-9]*[gt]|:u8grep -i -v real|:u8gr "=%PARAM%"|:u8 strip-ansi)|:u8 grep --color=always -i "=%PARAM%"
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


