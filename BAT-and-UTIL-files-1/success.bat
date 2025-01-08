@Echo OFF
@on break cancel

set MSG=%@UNQUOTE[%*]
if "%1" == "" set MSG=*** Success!!! ***

call print-message success "%MSG%"
goto :END

            :LEGACY
                    call AlarmCharge
                    %COLOR_SUCCESS% %+ echos *** Success!!! ***
                    %COLOR_NORMAL%  %+ echo.

:END
