@echo off


set ARGV=%1
set echo=echo 
set doing=Not really ``

if "%2" ne "force" (
    set DRY_RUN=1
    set echo=echo
    set doing=%blink_on%NOT%blink_off% doing: ``
) else (
    set DRY_RUN=0
    set echo=
    set doing=Doing ``
)

gosub echoWarn
for /h /d %temp_directory_to_do_something_in in (*.*) (
    pushd .
    cd %temp_directory_to_do_something_in

    echo.
    set MESSAGE=%doing%'%ARGV%' in Folder: %italics_on%%@randfg_soft[]%_CWP%%italics_off%
    if %DRY_RUN eq 1 (
        REM DEBUG: echo dry run yes %DRY_RUN
        color bright red on black
        echo %ANSI_COLOR_RED%%STAR% %MESSAGE%
    ) else (
        REM DEBUG: echo dry run no %DRY_RUN
        call important %MESSAGE%
        %COLOR_RUN%
    )
    color red on black
    %echo% %ARGV%
    popd
)


rem gosub echoWarn


goto :END
    :echoWarn
        if %DRY_RUN eq 0 (return)
        if %DRY_RUN eq 1 (
            call warning "You must set 2nd argument to 'force' to make this actually happen."
            ECHO.
            echo %ANSI_COLOR_ADVICE%%STAR% EXAMPLE: %0 "call delete-zero-byte-files" force
            pause
        )
        if "%1" eq "" (cancel)
    return
:END


