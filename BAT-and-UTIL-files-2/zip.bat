@on break cancel
@Echo OFF

:USAGE: zip <whatever>   - use default zip behavior
:USAGE: zip <foldername> - calls zip-folder.bat


set PARAMS=%*
set PARAM1Q=%1
set PARAM2Q=%2
set PARAM1=%@UNQUOTE[%1]
set PARAM2=%@UNQUOTE[%2]


if not isdir "%PARAM1%" .and. not exist "%PARAM1%" (
    call fatal_error "%0 called with parameter '%PARAM1%' which does not exist "
)


if  isdir           "%PARAM1%" .and. "%PARAM2" eq "" (
    call zip-folder "%PARAM1%"
) else if exist     "%PARAM1%" .and. "%PARAM2" eq "" (
    call zip-file   "%PARAM1%"
) else                                               (    
        *zip         %PARAMS%
)

