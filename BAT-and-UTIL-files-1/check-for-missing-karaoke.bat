@rem !!!!!!!!!!!!!!!!!!!!!!!!!! CHECK-FOR-MISSING-KARAOKE.BAT !!!!!!!!!!!!!!!!!!!!!!!!!! 
@loadbtm on
@Echo      off
@call bat-init

if "%_PBATCHNAME" == "" cls

rem Usage:
        iff "%1" == "/h" .or. "%1" == "-h" .or. "%1" == "--help" .or. "%1" == "/help" .or. "%1" == "help" .or. "%1" == "?" .or. "%1" == "/?" .or. "%1" == "-?" .or. "%1" == "--?" then
                echo.
                %color_advice%
                echo USAGE: %ansi_color_bright_yellow%%0 %ansi_color_advice%————— checks for missing karaoke in current folder
                echo USAGE: %ansi_color_bright_yellow%%0 /s %ansi_color_advice%—— checks for missing karaoke in current folder RECURSIVELY
                %color_normal%
                goto /i END
        endiff

rem HALT CONDITION:
rem If the folder indicates something we shoudln’t be creating karaoke for, let the user know:
rem (copied from create-srt but with %_CWD\ substitued over %FULL_FILENAME%)
        unset /q cfmk_fail_type
        set chipt_in_foldname=%@REGEX["[\\\[\(][cC][hH][iI][pP][tT][uU][nN][eE][sS]*[\\\]\)]","%_CWD%\"]
        set instr_in_foldname=%@REGEX["[\[\(][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][sS]*[\)\]\\]","%_CWD\"]
        set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*[\\\]\)]","%_CWD\"]
        set iscis_in_foldname=%@REGEX["[\\\[\(][Uu][Nn][Tt][Rr][Aa][Nn][Ss][Cc][Rr][Ii][Bb][Ee][Aa][Bb][Ll][Ee][\\\]\)]","%_CWD\"]
        if "1" == "%instr_in_foldname%" ( set cfmk_fail_type=instrumental     %+ set cfmk_fail_point=dir name)
        if "1" == "%chipt_in_foldname%" ( set cfmk_fail_type=chiptune         %+ set cfmk_fail_point=dir name)
        if "1" == "%sndfx_in_foldname%" ( set cfmk_fail_type=sound effects    %+ set cfmk_fail_point=dir name)
        if "1" == "%iscis_in_foldname%" ( set cfmk_fail_type=untranscribeable %+ set cfmk_fail_point=dir name)
        if "dir name" == "%cfmk_fail_point%" set BAD_AI_TRANSCRIPTION_FOLDER=%_CWP                  %+ rem Set environment flag to signal other processes(but I think this is unused, just an idea)
        rem DEBUG: pause "cmfk_fail_type=%cfmk_fail_type% chipt_in_foldname=%chipt_in_foldname%"
        iff "" != "%cfmk_fail_type%" then
                echo %ansi_color_warning%%no% Sorry! Not checking for missing karaokes here because this %italics_on%%cfmk_fail_point%%italics_off% indicates a %ansi_color_red%%italics_on%%blink_on%%cfmk_fail_type%%blink_off%%italics_off%%ANSI_COLOR_WARNING% folder:%ansi_color_normal% %faint_on%“%_CWP%”%faint_off%%ansi_color_normal%
                set fail=1
                call sleep 1
                goto :END
        endiff

rem Variable definitions ported from our outer environment into this script for portability:
        iff not defined filemask_audio then
                set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        endiff

rem Configuration:
        set DEFAULT_FILELIST_NAME_TO_USE=these.m3u
        set DEFAULT_FILEMASK=%FILEMASK_AUDIO%


rem Validate Enviroment:
        iff  "1" != "%validated_cfmk%" then
                call validate-in-path              check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py  askyn warning insert-before-each-line.py  fast_cat  mp3index delete-bad-ai-transcriptions errorlevel
                call validate-environment-variable filemask_audio   skip_validation_existence
                call validate-environment-variable DEFAULT_FILEMASK skip_validation_existence
                call validate-environment-variable ANSI_COLORS_HAVE_BEEN_SET
                set  validated_cfmk=1
                rem  CHECK-FOR-MISSING-KARAOKE ENVIRONMENT SUCCESSFULLY VALIDATED!!!!!!!!!!!!!!!!
        endiff
        

rem Parameter capture:
        set PARAMS=%*
        set DIR_PARAMS=%PARAMS%
        
rem Parameter processing:
        set RECURSE_CFMK=0
        :Again
        if  "%1" == "/s" set RECURSE_CFMK=1
        iff "%2" != "" then
                shift
                goto /i Again
        endiff                

rem Debug:
        rem echo recurse_cfmk is %RECURSE_CFMK% 

rem Initialization:
        set  FILELIST_TO_USE=%DEFAULT_FILELIST_NAME_TO_USE%
        echo FILELIST_TO_USE is “%FILELIST_TO_USE%” 🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱>nul


rem Parameter checking:
        rem no-parameter case:
                iff "%1" == ""  then
                        rem echo.
                        rem OLDER: ASK: call AskYn   "%italics_on%instead%italics_off% use files here that match: %DEFAULT_FILEMASK% ?" yes 99999
                        rem OLD: NOTIFY:
                        rem call unimportant "No filelist was specified" silent
                        rem call unimportant "Using FILEMASK_AUDIO to find files instead" silent
                        rem dir /b %FILEMASK_TO_USE%  %+ rem this was confusing to see, actually
                        rem NEW: Just say nothing. This is how it's designed, we don't need to warn ourselves anymore.
                        
                        set FILEMASK_TO_USE=%DEFAULT_FILEMASK%
                endiff

        rem Use different filelist name depending on parameters:
                iff "%dir_params%" != "" then
                    rem echo - DEBUG: if "%@REGEX[/s,%dir_params%]" == "1" (set FILELIST_TO_USE=all.m3u) 
                                      if "%@REGEX[/s,%dir_params%]" == "1" (set FILELIST_TO_USE=all.m3u)
                endiff                                      
                iff exist %filemask_audio% then
                        rem dir /b /[!*instrumental*] %DIR_PARAMS% %filemask_audio% >:u8 %FILELIST_TO_USE%
                           (dir /b /[!*instrumental* *chiptune* "*sound effect*"  "*untranscribeable*"] %DIR_PARAMS% %filemask_audio% >:u8 %FILELIST_TO_USE%) >&>nul
                        rem ^^^ There still might be errors here in the event of audio files being present, but 100% of them having "instrumental" in their name. Therefore, let's suppress stderr

                endiff                        


        rem If the filelist is these or all.m3u we need to regenerate them...  (Do we really?)
                if "%filelist_to_use%" == "these.m3u" .or. "%filelist_to_use%" == "all.m3u" (call mp3index)

rem Debug info:
        if %DEBUG gt 0 echo %ANSI_COLOR_DEBUG%- PARAMS: %PARAMS%%newline%%tab%using filelist of = %FILELIST_TO_USE%%newline%%tab%using filemask of = %FILEMASK_TO_USE%%ANSI_COLOR_NORMAL%
        rem echo got here ... does 1 eq %RECURSE_CFMK%?



rem If the filelist doesn't exist...
        iff "1" == "%RECURSE_CFMK%" then
                rem call mp3index/s                         >:u8all.m3u
                call mp3index
                if not exist   all.m3u .or. 0 eq %@FILESIZE[all.m3u]   goto /i END
        else                
                call mp3index
                rem call mp3index                           >:u8these.m3u
                if not exist these.m3u .or. 0 eq %@FILESIZE[these.m3u] goto /i END
        endiff                

rem Kill bad transcriptions first:
        if "0" == "%DELETE_BAD_AI_TRANSCRIPTIONS_FIRST%" goto /i skip_delete_bad
        call delete-bad-ai-transcriptions 3
        :skip_delete_bad
        setdos /x0

rem Check for songs missing sidecar TXT files :
        set last_command=(check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %FILELIST_TO_USE% *.srt;*.lrc createsrtfilewrite %params% |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING KARAOKE %ANSI_RESET% %EMOJI_WARNING% %DASH% ") |:u8 fast_cat
                         (check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %FILELIST_TO_USE% *.srt;*.lrc createsrtfilewrite %params% |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING KARAOKE %ANSI_RESET% %EMOJI_WARNING% %DASH% ") |:u8 fast_cat
        call errorlevel

rem 🧹🧹🧹 While we're here, do some cleanup: 🧹🧹🧹
        iff exist *.json then
                echo rayray|*del /q *.json>&>nul
        endiff
        
        
rem If there was nothing to do, let user know:   
        iff not exist create-the-missing-karaokes-here-temp.bat .and. not exist get-the-missing-lyrics-here-temp.bat then
                set LAST_FOLDER_HAD_NO_KARAOKE_OR_LYRICS_TO_GENERATE=1
                echo.
                iff not exist %FILEMASK_AUDIO% then
                        call success "Nothing here to transcribe!"
                else
                        call success "Nothing left to transcribe!"
                endiff
        else
                set LAST_FOLDER_HAD_NO_KARAOKE_OR_LYRICS_TO_GENERATE=0
        endiff


rem If we passed the “get” parameter, then run the script to get them:
rem echo 💣💣💣💣💣💣       iff %%1"%1" == "get" .or. %%2"%2" == "get" .or. %%3"%3" == "get" t h e n  params=%1$
        iff "%1" == "get" .or. "%2" == "get" .or. "%3" == "get" then 
                iff exist create-the-missing-karaokes-here-temp.bat then
                        call create-the-missing-karaokes-here-temp.bat
                else
                        rem call warning_soft "create-the-missing-karaokes-here-temp.bat does not exist"
                endiff
        endiff


:END
