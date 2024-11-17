@echo off
if "%CYGWIN"=="0" goto :nocygwin
if "%CYGWIN" ne ""  goto :cygwin
goto :nocygwin

:nocygwin
c:\util\du.exe %*
goto :end

:cygwin
c:\cygwin\bin\du.exe %*
goto :end

:end
