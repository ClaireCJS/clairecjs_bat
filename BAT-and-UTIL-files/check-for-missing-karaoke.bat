@Echo OFF

rem Validate Enviroment:
        call validate-environment-variable filemask_audio check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py fast_cat

rem Parameter stuff:
        set PARAMS=%*
        set DIR_PARAMS=%PARAMS%

rem Make filelist to use as input:
        set FILELIST=these.m3u
        if "%@REGEX[\/s,%dir_params%]" eq "1" (set FILELIST=all.m3u)
        dir /b /[!*instrumental*] %DIR_PARAMS% %filemask_audio% >:u8 %FILELIST%

rem Check for songs missing sidecar TXT files :
        echo.
        rem fast_cat fixes ANSI rendering errors between TCC/WT:
        check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py %FILELIST% *.srt createsrtfilewrite %* |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING LYRICS %ANSI_RESET% %EMOJI_WARNING% %DASH% " |:u8 fast_cat

rem While we're here, do some cleanup:
        if exist *.json (del *.json)
