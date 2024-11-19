@echo off
 on break cancel

 call randcolor

:TOO SLOW: call validate-environment-variable UTIL
:TOO SLOW: if not exist c:\cygwin\bin\wget.exe (goto :nocygwin)

    
if "%CYGWIN" =="0" (goto :nocygwin)
if "%CYGWIN" ne "" (goto   :cygwin)
                    goto :nocygwin



                        :nocygwin
                            %UTIL%\wget.exe %*
                        goto :end

                        :cygwin
                            rem c:\cygwin\bin\wget.exe %*
                            wget.exe %*
                        goto :end



:END
    %COLOR_NORMAL%
