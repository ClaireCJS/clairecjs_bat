@Echo OFF


REM IMAGE_OPENER=start
REM IMAGE_OPENER=call wrapper start
set IMAGE_OPENER=%UTIL2%\IrfanViewPortable\IrfanViewPortable.exe
set IMAGE_OPENER=%UTIL2%\IrfanViewPortable\App\IrfanView\i_view32.exe
set IMAGE_OPENER=%UTIL2%\IrfanViewPortable\App\IrfanView64\i_view64.exe


call validate-environment-variable IMAGE_OPENER





call advice "using image opener of %IMAGE_OPENER% %*"
start %IMAGE_OPENER% %*

