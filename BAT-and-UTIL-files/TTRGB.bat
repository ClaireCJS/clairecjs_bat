@Echo OFF

rem Check if it's running already:
        call isRunning ttrgb quiet
        if  %isRunning eq 1 (call warning "TTRGB is already running" %+ goto :END)


rem Validate environment:
        set                                            EXE="%ProgramFiles%\Tt\TT RGB PLUS\TTRGBPlus.exe"
        set                                 DIR=%@PATH[%EXE]
        call validate-environment-variables DIR         EXE  ProgramFiles  

rem Run TTRGB:
        pushd .
                "%DIR%\"
                start %EXE%
                call wait 12 "(waiting for %italics_on%TTRGB%italics_off% to start)"
                activate "TT RGB Plus" tray
        popd


:END

