@Echo OFF

:DECRIPTOIN: assumes print-message has already been run to define MESSAGE_TYPES_WITHOUT_ALIASES -- that could be better in environm.btm but that makes things less portable

REM Validate that we have a list of message types used in print-message.bat (this var is set in print-message.bat):
        call validate-environment-variables MESSAGE_TYPES ANSI_RESET MESSAGE_TYPES_WITHOUT_ALIASES

REM dump environment to tmp%file —— no need for 'force' parameter because the types don't change except once in a blue moon:
        call dump-environment-to-tmpfile

REM go through each enviroment variable
        rem echo.
        unset /q MESSAGE_TYPES_PRETTY
        for %type in (%MESSAGE_TYPES_WITHOUT_ALIASES%) gosub ProcessEnvVar %type%


goto :END
    :ProcessEnvVar [var]
        set ANSI_VAR_NAME=ANSI_COLOR_%VAR%
        REM echos message_type = %var% %@ANSI_MOVE_TO_COL[30] ansi_env_var_name=%ansi_var_name% %@ANSI_MOVE_TO_COL[74]
        if defined  %[ANSI_VAR_NAME] (
            rem echos  %[%[ANSI_VAR_NAME]]THIS COLOR
            set ZZ=%[%[ANSI_VAR_NAME]]%VAR%
            if defined MESSAGE_TYPES_PRETTY (
                set MESSAGE_TYPES_PRETTY=%MESSAGE_TYPES_PRETTY%%ANSI_RESET%%@ANSI_BG[0,0,0] %ZZ%%ANSI_RESET%%@ANSI_BG[0,0,0]
            ) else (
                set MESSAGE_TYPES_PRETTY=%ZZ%%ANSI_RESET%%@ANSI_BG[0,0,0]
            )
        )
        rem echo %ANSI_RESET%
    return
:END
