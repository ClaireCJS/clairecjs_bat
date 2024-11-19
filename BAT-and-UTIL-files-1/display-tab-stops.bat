@on break cancel
@Echo OFF

rem Display 100, or however many we ask:
                       set NUM_TO_DISPLAY=100
        if "%1" ne "" (set NUM_TO_DISPLAY=%1)

rem Validate environment:
        call validate-env-vars NUM_TO_DISPLAY BOLD_ON BOLD_OFF

rem Do it —— seting bold on and off at the end to make it so the line doesn't technically end in a tab, and thus renders correctly:
        do xx = 1 to %NUM_TO_DISPLAY% by 1 (
            echos %xx%%@CHAR[9]%BOLD_ON%%BOLD_OFF%
        )