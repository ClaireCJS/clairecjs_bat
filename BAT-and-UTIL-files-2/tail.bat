@echo off
@on break cancel

if "%CYGWIN" == "0"  goto :nocygwin
if "%CYGWIN" ne  ""  goto   :cygwin

goto :nocygwin

        :nocygwin
                *tail /n%@STRIP[-,%1]
        goto :end

        :cygwin
                c:\cygwin\bin\tail.exe %*
        goto :end

:end
