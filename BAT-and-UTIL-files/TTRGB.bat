@Echo OFF

call isRunning ttrgb quiet
if  %isRunning eq 1 (call warning "TTRGB is already running" %+ goto :END)


    set                                 EXE="%ProgramFiles%\Tt\TT RGB PLUS\TTRGBPlus.exe"
    set                                 DIR=%@PATH[%EXE]
    call validate-environment-variables DIR EXE ProgramFiles  

    pushd .
        "%DIR%\"
        start %EXE%
        sleep 12
        activate "TT RGB Plus" tray
    popd


:END

