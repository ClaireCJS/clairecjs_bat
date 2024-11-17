@Echo off

rem Just which version of strings.exe are we currently using?
rem Definitely not the one we used in the 1980s DOS days! 😁

if exist %UTIL%\Sysinternals\strings.exe (goto :sysinternals)
if "%CYGWIN" == "0"                      (goto     :nocygwin)
if "%CYGWIN" ne ""                       (goto       :cygwin)
                                          goto     :nocygwin

    :sysinternals
        %UTIL%\Sysinternals\strings.exe %*
    goto :END


    :nocygwin
        c:\util\strings.exe %*
    goto :end


    :cygwin
        if     exist c:\cygwin\bin\strings.exe (c:\cygwin\bin\strings.exe %*)
        if not exist c:\cygwin\bin\strings.exe (call warning "strings is not currently installed in cygwin" %+ goto :nocygwin)
    goto :end



:END
