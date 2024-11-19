@Echo OFF
 on break cancel

if "%CONTAINER%" ne "" goto :Detected_Already
                       REM we used to set container= but it had some problems with some pop-up situations and I didn't feel like investigating it
                                      set container=unknown
    if "%SESSIONNAME%" eq "Console"  (set container=TCC)
    if defined WT_SESSION            (set container=WindowsTerminal)
    if "%container%"   eq "unknown"  (
        if "%OS%" eq  "7" (set container=TCC)
        if "%OS%" eq "10" (set container=WindowsTerminal)
    )
    call print-if-debug                  "Container is %CONTAINER%"
    if not defined container (call error "container should be defined here in %0")
:Detected_Already
