@echo off

:USAGE: echo-rainbow Message to be in rainbow
:USAGE: echo-rainbow test
:USAGE: echo-rainbow generate 'message to set to RAINBOW_TEXT'



rem *** Are we running in test mode?
        if "%*"=="test" (
            gosub :generateTestString
        ) else (
            set inputStr=%*
        )


rem *** Are we running in generate mode?
        set GENERATE_MODE=0
        if "%1"=="generate" (
            set RAINBOW_TEXT=
            set GENERATE_MODE=1
            set inputStr=%2$
        )

rem *** Get length of string, and use it to calculate the step size between hues
        set strLength=%@len[%inputStr%]
        set MAX_HUE=1530
        set colorStep=%@EVAL[%MAX_HUE/%strLength]
        REM @echo strlength is '%strLength'%wide%

rem Iterate over each character and interpolate color
        for /l %N in (0,1,%strLength%) gosub printCharWithColor %n%


goto :eof


    :printCharWithColor [%n]
        set charPosition=%%N

        set hue=%@FLOOR[%@EVAL[(%charposition/%strLength)*%MAX_HUE]]
        REM echo hue is %hue

        set /a redComponent=0
        set /a greenComponent=0
        set /a blueComponent=0

        if %hue% lss 256 (
            set /a redComponent=255
            set /a greenComponent=%hue%
        ) else (
            if %hue% lss 512 (
                set /a redComponent=511-%hue%
                set /a greenComponent=255
            ) else (
                if %hue% lss 768 (
                    set /a greenComponent=255
                    set /a blueComponent=%hue%-512
                ) else (
                    if %hue% lss 1024 (
                        set /a greenComponent=1023-%hue%
                        set /a blueComponent=255
                    ) else (
                        if %hue% lss 1280 (
                            set /a redComponent=%hue%-1024
                            set /a blueComponent=255
                        ) else (
                            set /a redComponent=255
                            set /a blueComponent=1535-%hue%
                        )
                    )
                )
            )
        )

        :next_1
        set singleChar=%@INSTR[%charPosition%,1,%inputStr%]``
        if "%singleChar%" eq "" (set singleChar= ``)
        REM echo singlechar is '%singleChar'

        set   redComponent=%@FLOOR[%redComponent]
        set greenComponent=%@FLOOR[%greenComponent]
        set  blueComponent=%@FLOOR[%blueComponent]

        rem echo %singleChar% @ANSI_FG_RGB[%redComponent%,%greenComponent%,%blueComponent%]%singleChar%``
        rem echo %blink%%singleChar%%blink_off%  hue=%hue% ... %@ANSI_FG_RGB[%redComponent%,%greenComponent%,%blueComponent%]%singleChar%``

        if 1 ne %GENERATE_MODE (
                                     echos %@ANSI_FG_RGB[%redComponent%,%greenComponent%,%blueComponent%]%singleChar%``
        ) else (
            set RAINBOW_TEXT=%RAINBOW_TEXT%%@ANSI_FG_RGB[%redComponent%,%greenComponent%,%blueComponent%]%singleChar%``
        )
            


    return


    :generateTestString
        rem Generate a test string of length 1024
        rem The string consists of four-digit repetitions from 0000 to 1023
        set inputStr=
        for /l %%N in (0,1,1023) do (
            set /a number=%%N
            if %number% lss 1000 (set number=0%number%)
            if %number% lss 100  (set number=00%number%)
            if %number% lss 10   (set number=000%number%)
            set inputStr=%inputStr%%number%
        )
    return


:eof

rem Optional: Reset ansi back (this env var is defined in set-colors.bat)
        if 1 ne %GENERATE_MODE (
            echos %ANSI_RESET%``
        ) else (
            set RAINBOW_TEXT=%RAINBOW_TEXT%%ANSI_RESET%``
        )

