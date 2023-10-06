@echo off

:USAGE: zip <whatever>   - use default zip behavior
:USAGE: zip <foldername> - calls zip-folder.bat


set PARAM1=%@UNQUOTE[%1]
set PARAM2=%@UNQUOTE[%2]


if isdir "%PARAM1%" .and. "%PARAM2" eq "" (
    call zip-folder "%PARAM1%"
) else if exist "%PARAM1%" .and. "%PARAM2" eq "" (
    call zip-file   "%PARAM1%"
) else                                           (    
    *zip         %*       
    )

