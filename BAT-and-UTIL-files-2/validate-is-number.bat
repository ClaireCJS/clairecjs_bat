@Echo OFF
 on break cancel

set VALUE=%1



if "%VALUE%" ne "" goto :IsSomething

    SET ERROR=1
        call error "No parameter to validate"
        pause
    goto :END

:IsSomething


if "%@REGEX[\D,%VALUE%]" eq "0" goto :IsNumber

    SET ERROR=1
    call fatal_error "“%italics_on%%VALUE%%italics_on%” is not a number!!"

:IsNumber



:END

