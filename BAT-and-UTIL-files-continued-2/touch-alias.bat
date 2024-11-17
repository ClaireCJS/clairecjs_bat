@Echo OFF


set TARGET=%1

if   isdir        %1 (goto    :isdir)
if "%CYGWIN%" == "0" (goto :nocygwin)
if "%CYGWIN%" ne ""  (goto   :cygwin)
                      goto :nocygwin



        :isDir
            echo.
            call less_important "is a dir"
            echo on
            rem         /dc or /da or /dw
            *touch /a:d /dw%_isodate  %TARGET%
            @echo off
        goto :end


        :nocygwin
            *touch %*
        goto :end


        :cygwin
            c:\cygwin\bin\touch.exe %*
        goto :end




:END
