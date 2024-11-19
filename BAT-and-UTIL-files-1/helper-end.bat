@on break cancel
@Echo off

:DECRIPTION: This is just a generic BAT that we like to call at the end of "helper BATs", which for us, are typically launched in another window/pane
:DECRIPTION:  It responds to the %FAST and %NOPAUSE environment variables, as well as to "FAST" and "NOPAUSE" parameters. They both do the same thing: Skip the pause.


rem Pause if we're instructed to:
        if "%FAST"    ==  "1" goto :nopause
        if  "FAST"    == "%1" goto :nopause
        if "%NOPAUSE" ==  "1" goto :nopause
        if  "NOPAUSE" == "%1" goto :nopause
            pause>nul
            pause>nul
            pause>nul
        :nopause

rem Remove any existing pause instruction, because it's meant to only happen once:
        UNSET /q FAST
        UNSET /q NOPAUSE

rem Exit the window/pane: THIS IS ALL WE *REALLY* WANT TO DO —— The rest is gravy
        exit

