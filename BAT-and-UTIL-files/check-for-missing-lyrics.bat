@Echo OFF

rem Validate Enviroment:
        call validate-environment-variable filemask_audio check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py

rem Make filelist to use as input:
        set                           FILELIST=these.m3u
        dir /b %filemask_audio% >:u8 %FILELIST%

rem Check for songs missing sidecar TXT files :
        echo.
        check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py %FILELIST% *.txt getlyricsfilewrite |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING LYRICS %ANSI_RESET% %EMOJI_WARNING% %DASH% "

rem While we're here, do some cleanup:
        del *.json
