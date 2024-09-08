@echo off
if "%CYGWIN"=="0" goto :nocygwin
if "%CYGWIN" ne ""  goto :cygwin
goto :nocygwin

:nocygwin
    %UTIL%\head.exe %*
goto :end

:cygwin
    c:\cygwin\bin\head.exe %*
goto :end

:end
