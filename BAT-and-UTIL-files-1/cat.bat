@Echo OFF

if exist c:\cygwin\bin\cat.exe (goto :cygwin)

    :nocygwin
        type %*
    goto :end

    :cygwin
        c:\cygwin\bin\cat.exe %*
    goto :end

:end

REM to fix bug where gnu cat.exes 9.0 changes console input mode so that tab filename completion no longer works
    call fix-tab-completion
