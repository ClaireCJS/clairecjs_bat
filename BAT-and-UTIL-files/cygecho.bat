@Echo OFF

set CYGECHO=c:\cygwin\bin\echo.exe

if %VALIDATED_CYGECHO ne 1 (
    call validate-environment-variable CYGECHO
    set VALIDATED_CYGECHO=1
)


%CYGECHO% %*


