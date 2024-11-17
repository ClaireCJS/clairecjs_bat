@Echo OFF

REM validate environment
        call validate-in-path magick.exe

REM validate parameters
        set                                IMAGE=%@UNQUOTE[%1]
        call validate-environment-variable IMAGE

REM get dimensions and set them to environment variables
        set dimensions=%@EXECSTR[magick.exe identify -format "%%%%wx%%%%h" "%IMAGE%"]
        set      width=%@EXECSTR[magick.exe identify -format "%%%%w"       "%IMAGE%"]
        set     height=%@EXECSTR[magick.exe identify -format       "%%%%h" "%IMAGE%"]



