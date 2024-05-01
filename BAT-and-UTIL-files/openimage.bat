@Echo OFF


REM IMAGE_OPENER=start
REM IMAGE_OPENER=call wrapper start
set IMAGE_OPENER=%UTIL2%\IrfanViewPortable\IrfanViewPortable.exe


call validate-environment-variable IMAGE_OPENER





start %IMAGE_OPENER% %*

