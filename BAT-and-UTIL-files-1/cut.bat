@echo off
 on break cancel
if "%CYGWIN"=="0" goto :nocygwin
if "%CYGWIN" ne ""  goto :cygwin
goto :nocygwin

:nocygwin
c:\util\cut.exe %*
goto :end

:cygwin
c:\cygwin\bin\cut.exe %*
goto :end

:end
