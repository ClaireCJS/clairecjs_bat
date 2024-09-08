@Echo OFF

if %VALIDATED_DISPLAYMP3TAGS ne 1 (call validate-in-path metamp3)
set VALIDATED_DISPLAYMP3TAGS=1

metamp3 --info %*

