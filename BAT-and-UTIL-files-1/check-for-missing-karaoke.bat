@loadbtm on
@rem !!!!!!!!!!!!!!!!!!!!!!!!!! CHECK-FOR-MISSING-KARAOKE.BAT !!!!!!!!!!!!!!!!!!!!!!!!!! 
@Echo      off
ON BREAK goto /i cmfk_onbreak










rem ===== CONFIG: EXECUTION: ==========================================================================================================================

set LOCKFILE_EXPIRATION_TIME=604800  %+ rem How old should the lockfile be to where we just ignore it? In seconds. We’re going to go with one week, which is 60 sec * 60 min * 24 hrs * 7 days = 604,800 seconds
set ONLY_RUN_ONCE_PER_FOLDER=1       %+ rem Use lockfiles to prevent two instances of this from running in the same folder simultaneously. There may be situations where you want to turn this off, like if you want to dedicate multilpe tabs to transcribing one folder.

rem ===== CONFIG: DEBUG: ==============================================================================================================================

set    DEBUG_CFMK_LOCKFILE=0         %+ rem whether to echo to screen: certain information about the per-folder-lockfile–processing to the screen
set DEBUG_AUTOFAIL_FOLDERS=0         %+ rem whether to echo to screen: the results of our probe to see whether the current folder is valid or not

rem ===================================================================================================================================================











rem Usage:
        iff "%1" == "/h" .or. "%1" == "-h" .or. "%1" == "--help" .or. "%1" == "/help" .or. "%1" == "help" .or. "%1" == "?" .or. "%1" == "/?" .or. "%1" == "-?" .or. "%1" == "--?" then
                echo.
                %color_advice%
                        echo USAGE: %ansi_color_bright_yellow%%0 %ansi_color_advice%————— checks for missing karaoke in current folder
                        echo USAGE: %ansi_color_bright_yellow%%0 /s %ansi_color_advice%—— checks for missing karaoke in current folder RECURSIVELY
                        echo USAGE: %ansi_color_bright_yellow%%0 /f %ansi_color_advice%—— checks for missing karaoke in current folder, ignoring lockfiles, in case you want to run multilpe instances in one folder
                %color_normal%
                goto /i END
        endiff





rem Opening cosmetics:
        if "%_PBATCHNAME" == "" cls

rem HALT CONDITIONS:
        rem HALT ❶: If the folder indicates something we shouldn’t be creating karaoke for, let the user know:
        rem (copied from create-srt but with %_CWD\ substitued over %FULL_FILENAME%)
                rem Reset our failure flag(s):
                        unset /q cfmk_fail_type

                rem Check to see if certain halt patterns are in our filenames:
                        set chipt_in_foldname=%@REGEX["[\\\[\(][cC][hH][iI][pP][tT][uU][nN][eE][sS]*[\\\]\)]","%_CWD%\"]
                        set instr_in_foldname=%@REGEX["[\[\(][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][sS]*[\)\]\\]","%_CWD\"]
                        set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*[\\\]\)]","%_CWD\"]                                    %+ rem OLD
                        set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*","%_CWD\"]                                            %+ rem NEW: to commodate folder names like “sound effects & ambient sound”
                        set iscis_in_foldname=%@REGEX["[\\\[\(][Uu][Nn][Tt][Rr][Aa][Nn][Ss][Cc][Rr][Ii][Bb][Ee]*[Aa][Bb][Ll][Ee][\\\]\)]","%_CWD\"]

                rem If certain halt patterns ARE in our filename, gather our failure type:
                        if "1" == "%instr_in_foldname%" ( set cfmk_fail_type=instrumental     %+ set cfmk_fail_point=dir name)
                        if "1" == "%chipt_in_foldname%" ( set cfmk_fail_type=chiptune         %+ set cfmk_fail_point=dir name)
                        if "1" == "%sndfx_in_foldname%" ( set cfmk_fail_type=sound effects    %+ set cfmk_fail_point=dir name)
                        if "1" == "%iscis_in_foldname%" ( set cfmk_fail_type=untranscribeable %+ set cfmk_fail_point=dir name)

                rem Signal our failure to any other processes watching this environment variable:
                        if "dir name" == "%cfmk_fail_point%" set BAD_AI_TRANSCRIPTION_FOLDER=%_CWP                  

                rem DEBUG: 
                        if "1" == "%DEBUG_AUTOFAIL_FOLDERS%" pause "cmfk_fail_type=“%cfmk_fail_type%” chipt_in_foldname=“%chipt_in_foldname%” sndfx_in_foldname=“%sndfx_in_foldname%”" 

                rem Let user know if we halted based on one of our halt conditions:
                        iff "" != "%cfmk_fail_type%" then
                                echo %ansi_color_warning%%no% Sorry! Not checking for missing karaokes here because this %italics_on%%cfmk_fail_point%%italics_off% indicates a %ansi_color_red%%italics_on%%blink_on%%cfmk_fail_type%%blink_off%%italics_off%%ANSI_COLOR_WARNING% folder:%ansi_color_normal% %faint_on%“%_CWP%”%faint_off%%ansi_color_normal%
                                set  fail=1
                                call sleep 1
                                goto /i END
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
        :Again
        set     CFMK_GET=0
        set   CFMK_FORCE=0
        set RECURSE_CFMK=0
        if "%1" == "get"    (shift %+ set CFMK_GET=1                )
        if "%1" == "/s"     (shift %+ set RECURSE_CFMK=1            )
        if "%1" == "/f"     (shift %+ set ONLY_RUN_ONCE_PER_FOLDER=0)
        if "%1" == "force"  (shift %+ set CFMK_FORCE=1)
        if "%1" != ""       (echo * ERROR: check-for-missing-karaoke.bat still need to process command tail value of, but doesn’t know how: %1$ %+ goto /i Again)
        rem DEBUG pause "After cmd tail proc, CFMK_FORCE=“%CFMK_FORCE%”"


rem Debug:
        rem echo recurse_cfmk is %RECURSE_CFMK% 





rem Initialization:
        set  FILELIST_TO_USE=%DEFAULT_FILELIST_NAME_TO_USE%
        echo FILELIST_TO_USE is “%FILELIST_TO_USE%” 🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱🐱>nul


rem Parameter checking:
        rem no-parameter case:
                iff "%1" == ""  then
                        set FILEMASK_TO_USE=%DEFAULT_FILEMASK%
                endiff

        rem Use different filelist name depending on parameters:
                iff "%dir_params%" != "" then
                        if "%@REGEX[/s,%dir_params%]" == "1" (set FILELIST_TO_USE=all.m3u)
                endiff                                      
                iff exist %filemask_audio% then
                        (dir /b /[!*instrumental* *chiptune* "*sound effect*"  "*untranscribable*" "*untranscribeable*"] %DIR_PARAMS% %filemask_audio% >:u8 %FILELIST_TO_USE%) >&>nul
                        rem ^^^ There still might be errors here in the event of audio files not being present, but 100% of them having "instrumental" in their name. Therefore, let's suppress stderr
                endiff                        

        rem If the filelist is these or all.m3u we need to regenerate them...  (Do we really?)
                if "%filelist_to_use%" == "these.m3u" .or. "%filelist_to_use%" == "all.m3u" (call mp3index)

rem Debug info:
        if %DEBUG gt 0 echo %ANSI_COLOR_DEBUG%- PARAMS: %PARAMS%%newline%%tab%using filelist of = %FILELIST_TO_USE%%newline%%tab%using filemask of = %FILEMASK_TO_USE%%ANSI_COLOR_NORMAL%


rem HALT ❷: If the folder is already being worked in ... Then we don’t want to work in the same folder twice at once.
rem             Even though it is inconsequential due to the lockfile functionality in create-srt, it gets messy from a 
rem             multi-tab operational standpoint if you have done something like set a OVERRIDE_VAD_THRESHOLD or a 
rem             OVERRIDE_LANGUAGE that you really intended to effect the folder you’re working in.... Then a 2ⁿᵈ tab
rem             you are operating might go into that folder and operate WITHOUT the flags you set for your 1ˢᵗ tab.
rem             So we have decided to only have one of these working in a folder at a time.
rem          This may be rergetted someday, if we want to use 20 tabs to conquer a folder with 100s of files in it,
rem             this would thwart us. So we will make it configutable
        iff "1" == "%ONLY_RUN_ONCE_PER_FOLDER%" then
                gosub lockfile_folderlevel_initialize_lockfile_values 
                gosub lockfile_folderlevel_check_lockfile
                gosub lockfile_folderlevel_create_lockfile 
        endiff


rem If the filelist doesn't exist...
        call mp3index
        iff "1" == "%RECURSE_CFMK%" then
                if not exist   all.m3u .or. 0 eq %@FILESIZE[all.m3u]   goto /i END
        else                
                if not exist these.m3u .or. 0 eq %@FILESIZE[these.m3u] goto /i END
        endiff                

rem Kill bad transcriptions first:
        if "0" == "%DELETE_BAD_AI_TRANSCRIPTIONS_FIRST%" goto /i skip_delete_bad
        call delete-bad-ai-transcriptions 3
        :skip_delete_bad
        setdos /x0

rem Check for songs missing sidecar TXT files :
        set last_check_for_missing_karaoke_command=(check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %FILELIST_TO_USE% *.srt;*.lrc createsrtfilewrite %params% |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING KARAOKE %ANSI_RESET% %EMOJI_WARNING% %DASH% ") `|:u8` fast_cat
        set                           last_command=(check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %FILELIST_TO_USE% *.srt;*.lrc createsrtfilewrite %params% |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING KARAOKE %ANSI_RESET% %EMOJI_WARNING% %DASH% ") `|:u8` fast_cat
                                                   (check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %FILELIST_TO_USE% *.srt;*.lrc createsrtfilewrite %params% |:u8 insert-before-each-line.py "%EMOJI_WARNING% %ANSI_COLOR_ALARM% MISSING KARAOKE %ANSI_RESET% %EMOJI_WARNING% %DASH% ")  |:u8  fast_cat
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
        rem pause "hmm"

rem If we passed the “get” parameter, then run the script to get them:
rem echo 💣💣💣💣💣💣       iff %%1"%1" == "get" .or. %%2"%2" == "get" .or. %%3"%3" == "get" t h e n  params=%1$
        iff "%CFMK_GET%" == "1" .or. "%1" == "get" .or. "%2" == "get" .or. "%3" == "get" then 
                iff exist create-the-missing-karaokes-here-temp.bat then
                        call create-the-missing-karaokes-here-temp.bat
                else
                        rem call warning_soft "create-the-missing-karaokes-here-temp.bat does not exist"
                endiff
        endiff


:cmfk_onbreak
rem pause "we’re done already?!"       
gosub lockfile_folderlevel_delete_lockfile

goto :END

rem ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
        :lockfile_folderlevel_initialize_lockfile_values [opt]
                if %DEBUG_CFMK_LOCKFILE% gt 0 call debug "Initializing folder level lockfile"
                set KARAOKE_FOLDER_LOCKFILE_FILENAME=.CurrentlyDoingTranscriptionsHere
        return
        :lockfile_folderlevel_check_lockfile [opt]
                rem Return if no lockfile exists:                
                        if %DEBUG_CFMK_LOCKFILE% gt 0 call debug "Checking folder level lockfile"
                        iff not exist "%KARAOKE_FOLDER_LOCKFILE_FILENAME%" then
                                return
                        endiff

                rem If the lockfile exists, read its values:
                        echo %ANSI_COLOR_WARNING_soft%%EMOJI_WARNING% Folder-level lockfile detected! %ansi_color_warning_soft_fg%Already doing work in %italics_on%%lq%%faint_on%%[_CWD]%faint_off%%rq%%italics_off%! %EMOJI_WARNING% %ANSI_COLOR_NORMAL%        
                        gosub lockfile_folderlevel_read_values

                rem If the lockfile is older than our configured expiration, then delete it automatically:
                        iff "1" == "%lockfile_folderlevel_expired%" then
                                gosub lockfile_folderlevel_delete_lockfile
                                return
                        endiff

                rem If the lockfile still exists and is valid, let user know about “force” option——unless that option is already being used:
                rem Otherwise, set our answer timeout to a low value with “yes” so that the lockfile is automatically deleted in “force” mode:
                        rem TODO hard-coded timeout values here
                        iff "1" != "%cfmk_force%" then
                                echo %ANSI_COLOR_ADVICE%%star2% Use ‘force’ option to continue anyway %ansi_color_normal%
                                set ANSWER_TIMEOUT=1200 %+ rem TODO fix hardcoded val
                                set ANSWER_DEFAULT=no
                        else
                                set ANSWER_TIMEOUT=5
                                set ANSWER_DEFAULT=yes
                        endiff

                rem Ask if they want to delete the lockfile, using parameters that may have been modified by the “force” option:
                        unset /q ANSWER
                        call AskYN "Delete lockfile & proceed in this folder anyway" %ANSWER_DEFAULT% %ANSWER_TIMEOUT%

                rem If the user answered “Yes” to our deletion question (which is not asked in “force” mode), then delete it:
                rem Otherwise, let the user know that we are aborting execution because a lockfile exists and we are already working in this folder
                        iff "Y" == "%ANSWER%" .or. "1" == "%cfmk_force%"  then
                                gosub lockfile_folderlevel_delete_lockfile
                        else
                                echo %ansi_color_warning_soft%%EMOJI_STOP_SIGN% Aborting because lockfile indicates that we are already working in this folder! %ansi_color_normal%
                                rem call divider
                                repeat 8 echo.
                                quit
                                goto /i :END
                        endiff
        return
        :lockfile_folderlevel_read_values [opt]
                        set raw1=%@if[exist %KARAOKE_FOLDER_LOCKFILE_FILENAME%,%@LINE[%KARAOKE_FOLDER_LOCKFILE_FILENAME%,1],NONE]
                        set raw2=%@if[exist %KARAOKE_FOLDER_LOCKFILE_FILENAME%,%@LINE[%KARAOKE_FOLDER_LOCKFILE_FILENAME%,3],NONE]
                        set lockfile_seconds_age=%@EVAL[%_DATETIME - %raw1%]
                        set   uptime_seconds=%@EVAL[%_WINTICKS/1000]
                        if "1" == "%DEBUG_CFMK_LOCKFILE%" echo %ansi_color_debug%- DEBUG: lockfile_folderlevel_read_values - pid=“%raw2%”,datetime=“%raw1%” - created %@COOL[%lockfile_seconds_age%] %ansi_color_debug%seconds ago!
                        rem If the lockfile has reached our expiration time, or is older than our last reboot, then it’s expired:
                                set lockfile_folderlevel_expired=0
                                iff  %lockfile_seconds_age% gt %LOCKFILE_EXPIRATION_TIME% then
                                        echo * Lockfile is past our age threshhold...
                                        set lockfile_folderlevel_expired=1
                                endiff
                                iff %lockfile_seconds_age% gt %uptime_seconds% then
                                        echo %ansi_color_removal%* Lockfile is before last reboot time...Deleting%ansi_color_normal%
                                        set lockfile_folderlevel_expired=1
                                endiff
                        iff "%raw1" == "NONE" unset folder_lockfile_dir
                        iff "%raw2" == "NONE" unset folder_lockfile_pid
        return %folder_lockfile_pid%
        :lockfile_folderlevel_create_lockfile [opt]
                if %DEBUG_CFMK_LOCKFILE% gt 0 call debug "Creating folder level lockfile"
                echo ％_DATETIME: >%KARAOKE_FOLDER_LOCKFILE_FILENAME%
                echo %_DATETIME  >>%KARAOKE_FOLDER_LOCKFILE_FILENAME%
                echo ％_PID:     >>%KARAOKE_FOLDER_LOCKFILE_FILENAME%
                echo %_PID       >>%KARAOKE_FOLDER_LOCKFILE_FILENAME%
                attrib  +r         %KARAOKE_FOLDER_LOCKFILE_FILENAME% >&nul
        return
        :lockfile_folderlevel_delete_lockfile [opt]
                :delete_it
                iff not exist "%KARAOKE_FOLDER_LOCKFILE_FILENAME%" then
                        if %DEBUG_CFMK_LOCKFILE% gt 0 .and. "1" == "%ONLY_RUN_ONCE_PER_FOLDER%" call debug "No lockfile to delete"
                        return
                endiff
                if %DEBUG_CFMK_LOCKFILE% gt 0 call debug "Deleting folder level lockfile"
                iff exist "%KARAOKE_FOLDER_LOCKFILE_FILENAME%" then
                        rem echo %ansi_color_removal%%emoji_axe% Deleting lock file: “%italics_on%%faint_on%%KARAOKE_FOLDER_LOCKFILE_FILENAME%%faint_off%%italics_off%”"%ansi_color_normal%
                        attrib -r          "%KARAOKE_FOLDER_LOCKFILE_FILENAME%" >&nul
                        *del /q /Ns /z /a: "%KARAOKE_FOLDER_LOCKFILE_FILENAME%" >&nul
                endiff
                iff exist "%KARAOKE_FOLDER_LOCKFILE_FILENAME%" then
                        call error "Why does the lockfile of “%KARAOKE_FOLDER_LOCKFILE_FILENAME%” still exist?"
                        goto /i delete_it
                endiff
                
        return
rem ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════



:END
        :Cleanup
                iff "1" == "%ONLY_RUN_ONCE_PER_FOLDER%" then
                        gosub lockfile_folderlevel_delete_lockfile
                        unset /q ONLY_RUN_ONCE_PER_FOLDER
                endiff

        


