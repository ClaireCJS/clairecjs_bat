:::: 20151014 - decided it's annoying when it goes to a new window and you DON'T want that. And when you DO, you can just drag it out.
:::: 2008-20151013: @call chrome --new-window %*

:::: 202002 temp fix when chrome sucked
    set CHROME_SUCKS_RIGHT_NOW=0
    :if "%machinename%" eq "THAILOG" (goto :Firefox)

:: Massage 2nd parameter:
    set TWO=%2
    if "%2" eq "CHROME" .or. "%2" eq "IE" (unset /q TWO)
    set ARGS=%1 %TWO% %3 %4 %5 %6 %7 %8 %9 
    set LAST_HTML_VIEWER_ARGS=%ARGS

:: Let 2nd parameter choose browser:
    if "%2" eq "CHROME" goto :Chrome
    if "%2" eq "IE"     goto :IE

:: Default browser:
                        goto :Chrome              %+ REM //Default behavior
        :Chrome
                set LAST_HTML_VIEWER_COMMAND=call chrome %ARGS%
                call chrome  %ARGS% %+ goto :END
        :Firefox
                set LAST_HTML_VIEWER_COMMAND=call firefox %ARGS%
                call firefox %ARGS% %+ goto :END
        :IE
                set LAST_HTML_VIEWER_COMMAND=call ie ht%ARGS%
                call ie      %ARGS% %+ goto :END

:END
