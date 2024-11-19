@echo off
 on break cancel
:pause
	if "%CYGWIN" == "0" goto :nocygwin
	if "%CYGWIN" ne ""  goto   :cygwin
goto :nocygwin

:nocygwin
	(c:\util\diff.exe %*)
goto :end

:cygwin
:original:
:c:\cygwin\bin\diff.exe %*
:
:temp
c:\cygwin\bin\diff.exe --binary %*
:temp verbose:
:echo  c:\cygwin\bin\diff.exe --binary		%*
:c:\cygwin\bin\diff.exe --binary		%*
:

goto :end

:end
