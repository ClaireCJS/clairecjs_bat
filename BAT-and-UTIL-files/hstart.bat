@Echo off

call validate-environment-variables OSBIT UTIL

goto :%OSBIT





:32
    %UTIL\hstart %*
goto :end




:default
:64
    %UTIL\hstart64 %*
goto :end




:end
