@on break cancel
@Echo OFF

set OUR_LOGGING_LEVEL=none


REM locate windows terminal directory and its own json file (but we don't edit it, we just validate it)
        call detect-with-which WT
        set WT=%RESULT%
        set WTDIR=%@PATH[%WT%]
        call logging " WT     is '%WT%'    "
        call logging " WTDIR is: '%WTDIR%' "
        %WTDIR%\
        set DEFAULTS_JSON=defaults.json
        call validate-environment-variables DEFAULTS_JSON EDITOR


rem locate settings.json config file:
        set SETTINGS_JSON_FOLDER=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState
        %SETTINGS_JSON_FOLDER%\
        set SETTINGS_JSON=settings.json
        call validate-environment-variables SETTINGS_JSON_FOLDER SETTINGS_JSON

rem EDIT our config file
        %COLOR_RUN%
        copy /md %SETTINGS_JSON% c:\backups\%MACHINENAME\windows_terminal-settings_file\%SETTINGS_JSON%.bak.%_DATETIME
        %EDITOR% %SETTINGS_JSON%




