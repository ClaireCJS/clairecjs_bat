@Echo off


call validate-in-path alarm advice free frpost cls cat_fast sleep


SET TMPTMP="%@UNIQUE[%TEMP]-%*"


if "%1" eq "" (
    repeat 2 echo.
    call advice "%bold_on%  USAGE:%bold_off% %italics_on%%0 {drive_letter}%italics_off% to monitor free space on that drive"
    call advice "%bold_on%EXAMPLE:%bold_off% %italics_on%%0 C             %italics_off% to monitor free space on  %italics_on%C%italics_off%:  drive"
    repeat 2 echo.
    call alarm  "Must provide a drive letter!"
    goto :END
)

:again
    (free %1: | frpost) >%TMPTMP%
    cls
    cat_fast             %TMPTMP%
    *del /q              %TMPTMP%
    sleep 3
goto :again

:END
