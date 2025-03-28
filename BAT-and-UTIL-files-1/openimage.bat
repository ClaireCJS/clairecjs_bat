@Echo OFF
@on break cancel


rem Configuration:
        REM IMAGE_OPENER=start
        REM IMAGE_OPENER=call wrapper start
        rem IMAGE_OPENER=%UTIL2%\IrfanViewPortable\IrfanViewPortable.exe
        set IMAGE_OPENER=%UTIL2%\IrfanViewPortable\App\IrfanView\i_view32.exe
        rem IMAGE_OPENER=%UTIL2%\IrfanViewPortable\App\IrfanView64\i_view64.exe doesn't handle video as well



rem Capture parameters:
        set PARAM=%*

rem Validate environment (once):
        iff 1 ne %validated_openimage% then
                call validate-environment-variable IMAGE_OPENER "You need to install an image viewer. Suggested: installing IrfanViewPortable to c:\util2\IrfanViewPortable to match the default values"
                set  validated_openimage=1
        endiff

rem Do it:
        rem call advice "using image opener of %IMAGE_OPENER%"
        start %IMAGE_OPENER% %param%

