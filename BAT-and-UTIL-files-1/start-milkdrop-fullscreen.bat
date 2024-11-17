@Echo OFF

::::: VALIDATE ENVIRONMENT:
        call validate-in-path LaunchKey activate

::::: CHECK IF MILKDROP IS RUNNING:
        rem //Can't do process ID check, must do Window Title check:
        if "%@WINPID[Milkdrop 2]" ne "-1" (goto :Milkdrop_Already_Running)

::::: START MILKDROP IF NOT ALREADY STARTED:
        rem Send Ctrl-Shift-K keypress to Winamp:
        LaunchKey "+^K" "%ProgramFiles\Winamp\winamp.exe"

::::: MAXIMIZE & SWITCH TO MILKDROP (SOMETIMES FULLSCREEN FAILS LATER IF WE DON'T DO THIS):
        :Milkdrop_Already_Running
        activate "Milkdrop 2" MAX

::::: DO THE FULLSCREEN THANG BY SENDING ALT-ENTER TO IT:
        rem Send Alt-Enter keypress to Milkdrop —— but first wait 2 seconds:
        LaunchKey {WAIT=2000}%%{ENTER}

