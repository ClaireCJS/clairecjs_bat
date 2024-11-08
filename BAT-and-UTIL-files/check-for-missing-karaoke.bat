@Echo OFF

rem Configuration:
        set DEFAULT_FILELIST_NAME_TO_USE=these.m3u
        set DEFAULT_FILEMASK=%FILEMASK_AUDIO%

rem Validate Enviroment:
        call validate-in-path                check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py  askyn warning insert-before-each-line.py fast_cat 
        call validate-environment-variables filemask_audio DEFAULT_FILELIST_NAME_TO_USE DEFAULT_FILEMASK


rem Parameter capture:
        set PARAMS=%*
        set DIR_PARAMS=%PARAMS%


rem Initialization:
        set FILELIST_TO_USE=%DEFAULT_FILELIST_NAME_TO_USE%

rem Parameter checking:
        rem no-parameter case:
                iff "%1" eq ""  then
                        call warning "Uh oh! No filelist was specified!%" silent
                        rem call AskYn   "%italics_on%instead%italics_off% use files here that match: %DEFAULT_FILEMASK% ?" yes 99999
                        call warning "Using FILEMASK_AUDIO to find files instead" silent
                        set FILEMASK_TO_USE=%DEFAULT_FILEMASK%
                        dir /b %FILEMASK_TO_USE% 

                endiff
        rem Use different filelist name depending on parameters:
                echo - DEBUG: if "%@REGEX[\/[sS],%dir_params%]" eq "1" (set FILELIST_TO_USE=all.m3u) 🐐🐐🐐
                              if "%@REGEX[\/[sS],%dir_params%]" eq "1" (set FILELIST_TO_USE=all.m3u)
                dir /b /[!*instrumental*] %DIR_PARAMS% %filemask_audio% >:u8 %FILELIST_TO_USE%


rem Debug info:
        echo %ANSI_COLOR_DEBUG%- PARAMS: %PARAMS%%newline%%tab%using filelist of = %FILELIST_TO_USE%%newline%%tab%using filemask of = %FILEMASK_TO_USE%%ANSI_COLOR_NORMAL%


rem Check for songs missing sidecar TXT files :
        echo.
        rem fast_cat fixes ANSI rendering errors between TCC/WT:
        check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py %FILELIST_TO_USE% *.srt createsrtfilewrite %* |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING LYRICS %ANSI_RESET% %EMOJI_WARNING% %DASH% " |:u8 fast_cat

rem While we're here, do some cleanup:
        if exist *.json (del *.json)
