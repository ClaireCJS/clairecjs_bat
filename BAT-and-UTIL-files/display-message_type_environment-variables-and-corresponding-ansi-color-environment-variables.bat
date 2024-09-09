@Echo OFF

REM Validate that we have a list of message types used in print-message.bat (this var is set in print-message.bat):
        call validate-environment-variables MESSAGE_TYPES ANSI_RESET 

REM dump environment to tmp%file
        call dump-environment-to-tmpfile.bat force

REM go through each enviroment variable
        echo.
        set MESSAGE_TYPE_GREP_RESULTS=
        for %type in (%MESSAGE_TYPES%) gosub ProcessEnvVar %type%


goto :END
    :ProcessEnvVar [var]
        set ANSI_VAR_NAME=ANSI_COLOR_%VAR%
        echos %@ANSI_MOVE_TO_COL[13]message_type =%ESCAPE_CHARACTER%> %var% %@ANSI_MOVE_TO_COL[45]ansi_env_var_name=%ansi_var_name% %@ANSI_MOVE_TO_COL[1]
        if defined %[ANSI_VAR_NAME] (echos %[%[ANSI_VAR_NAME]]THIS COLOR)
        echo %ANSI_RESET%
    return
:END
