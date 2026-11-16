@Echo OFF
@loadbtm on
@on break cancel



rem Set our beta/production status:
        rem PAFPLAYER_STATUS=BETA
        set PAFPLAYER_STATUS=PRODUCTION





rem Set folder name we’ll be using:
        set PROJECT_FOLDER_NAME=PAFPlayer

rem We used to run the script directly, but we started changing to running it with it’s own internal 
rem launcher BAT so that it uses the runtime packages instead of the current machine’s packages, 
rem thus eliminating the Python requirement to new users
        rem RUNTIME_RUNNER=PAFPlayer.py
        set RUNTIME_RUNNER=PAFPlayer.bat

rem Get command line options:
        set PAFPLAYER_CLI_OPTS=%*





rem Validate environment:
        if not isdir UTIL call validate-environment-variable UTIL




rem Run the proper version:
        if "%PAFPLAYER_STATUS%" == "BETA"       c:\codex\clairevironment\bat\%PROJECT_FOLDER_NAME%\%RUNTIME_RUNNER% %PAFPLAYER_CLI_OPTS%
        if "%PAFPLAYER_STATUS%" == "PRODUCTION"                       %UTIL%\%PROJECT_FOLDER_NAME%\%RUNTIME_RUNNER% %PAFPLAYER_CLI_OPTS%




