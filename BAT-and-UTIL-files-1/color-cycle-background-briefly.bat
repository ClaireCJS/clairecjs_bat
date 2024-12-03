@Echo OFF
rem No let's make this cancelable by NOT doing this: on break cancel

rem Output each line of the file with a delay between ... slow-type, basically:
        for /f "usebackq delims=" %%a in ("%bat%\color-cycle-background.ansi") do (
            echos %%a
            delay /m 1
        )

echos %ANSI_RESET%
