@echo off
if "%CYGWIN"=="0" goto :nocygwin
if "%CYGWIN" ne ""  goto :cygwin
goto :nocygwin

:nocygwin
c:\util\uniq.exe %*
goto :end

:cygwin
c:\cygwin\bin\uniq.exe %*
goto :end

:end
