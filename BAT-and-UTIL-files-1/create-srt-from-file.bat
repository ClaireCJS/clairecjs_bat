@loadbtm on
@rem echo %@colorful[🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗 CREATE-SRT-FROM-FILE 🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗] CWP=%_CWP
@Echo off                                                 %+ @rem @set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=1
@setdos /x0
@on break cancel                                          %+ @rem echo **** create-srt-from-file.bat called **** 🌭🌭🌭 
@on break goto :csff_onbreak
@if not defined Default_command_Separator_Character set Default_command_Separator_Character=`^`

rem TODO: MAYBE: figure out where to place the :go_here_for_encoding_retries label                                                            
rem TODO: MAYBE: concurrency: per-directory locking is implemented for certain scripts, but this one doesn’t perform any of it’s own [and that’s probably overkill]
rem TODO: MAYBE: afterregen anyway, do we need to ask about ecc2fasdfasf.bat?



REM CONFIG: OUTPUT FILE WIDTH:
        set SUBTITLE_OUTPUT_WITH=30                                                                    %+ rem is 25 for dvds, set to 20 for 72% of the project, trying 30 as of 2025/09/24


REM CONFIG: LOGFILES: 
        iff not defined LOGS then                                                                      %+ rem copy this line to get-lyrics-for-file as well
                mkdir c:\logs                                                                          %+ rem copy this line to get-lyrics-for-file as well
                set logs=c:\logs                                                                       %+ rem copy this line to get-lyrics-for-file as well
                if not isdir %logs% mkdir %logs%                                                       %+ rem copy this line to get-lyrics-for-file as well
        endiff                                                                                         %+ rem copy this line to get-lyrics-for-file as well
        set              AUDIOFILE_TRANSCRIPTION_LOG_FILE=%LOGS%\audiofile-transcription.log           %+ rem copy this line to get-lyrics-for-file as well
        set AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE=%LOGS%\audiofile-transcription-prompts.log   %+ rem copy this line to get-lyrics-for-file as well


REM CONFIG: 2025: 2ⁿᵈ half:
        set DEBUG_TRACE_CSFF=0                                                                         %+ rem Whether we want to echo our “we are here” debug traces
        set DEBUG_KARAOKE_APPROVAL=0                                                                   %+ rem Whether to let us know where calls to approving the karaoke file are made
        set DEBUG_ECHO_CALLS_TO_GETLYRICS=0                                                            %+ rem Whether to echo to the screen any calls to the get-lyrics functionality
        set LOCKFILE_MESSAGE_ROWS_TO_CLEAR=10                                                          %+ rem cosmetic: How many rows to clear out (scroll text up these many rows) to make space for lockfile messages to appear on the same part of the screen with more consistency

REM CONFIG: 2025: 1ˢᵗ half:
        @set temporarily_disable_status_bar=0
        set DEFAULT_LANGUAGE=en                                                                        %+ rem Default language. MAKE SURE TO SET/OVERRIDE TO “None” IF YOU DON’T WANT ONE! WhisperAI is actually pretty good at knowing which language something is, anyway
        set DEBUG_LOCKFILE=0                                                                           %+ rem Whether to show lockfile-related debugging info
        set DEFAULT_VAD_THRESHOLD=0.075                                                                %+ rem Whatever threshold we by default —— we may be asked to lower it if we choose to delete subtitles because they didn’t pick up most of the vocals
        set DEFAULT_VAD_THRESHOLD=0.07                                                                 %+ rem Whatever threshold we by default —— we may be asked to lower it if we choose to delete subtitles because they didn’t pick up most of the vocals
        set DEFAULT_VAD_THRESHOLD=0.05                                                                 %+ rem Whatever threshold we by default —— we may be asked to lower it if we choose to delete subtitles because they didn’t pick up most of the vocals
        set DEFAULT_VAD_THRESHOLD=0.03                                                                 %+ rem Whatever threshold we by default —— we may be asked to lower it if we choose to delete subtitles because they didn’t pick up most of the vocals. And increasingly, we make this lower over time because our auto-hallucation-removal removes is the primary bad side-effect from setting this value too low.
        set DEFAULT_VAD_THRESHOLD=0.01                                                                 %+ rem 2025/09/12 adjustment
        set DEFAULT_VAD_THRESHOLD=0                                                                    %+ rem 2025/09/24 adjustment but I think this may be unnecessary for most music genres


REM CONFIG: 2024: 
        set INSIST_ON_HAVING_ARTIST=0                                                                  %+ rem Set to 1 to ALWAYS ask for an artist, even if one can’t be found. For me personally, I found this to be too naggy.
        gosub set_TRANSCRIBER_VALID_EXTENSIONS_AND_LOCK_FILE_NAME                                      %+ rem Done as subroutine so it can be called by get-lyrics in case it needs it too
        set DEFAULT_PLAYER_COMMAND=vlc.exe                                                             %+ rem UPDATE THIS IN GET-LYRICS TOO! ——> program we use to play audio files, i.e. VLCplayer, MPC, etc.
        set DEFAULT_PLAYER_COMMAND=call preview-audio-file                                             %+ rem Command to run to play files with a media player
        set LOG_PROMPTS_USED=1                                                                         %+ rem 1=save prompt used to create SRT into sidecar ..log file
        set MAXIMUM_PROMPT_SIZE=3000                                                                   %+ rem The most TXT we will use to prime our transcription.  Since faster-whisper-xxx only supports max_tokens of 224, we only need 250 words or so. But will pad a bit extra. We just don’t want to go over the command-line-length-limit!
        set DEBUG_SHOW_LYRIC_STATUS=0                                                                  %+ rem shows lyriclessness/lyric status if we “gosub debug_show_lyric_status”
        set ANNOUNCE_IF_SIDECAR_FILES_EXIST=1                                                          %+ rem 1=very cosmetically polished display of whether each file/sidecar file exists (mp3/srt/lrc/txt/json/srt2)

rem CONFIG: 2024: WAIT TIMES:                                                                      
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=120                                                   %+ rem wait time for “are these lyrics good?”-type questions
        set AI_GENERATION_ANYWAY_WAIT_TIME=45                                                          %+ rem wait time for “no lyrics, gen with AI anyway”-type questions
        set AI_GENERATION_ANYWAY_WAIT_TIME_FOR_LYRICLESSNESS_APPROVED_FILES=5                          %+ rem wait time for “no lyrics, gen with AI anyway”-type questions *IF WE HAVE APPROVED LYRICLESSNESS STATUS* for the song
        set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=25                                        %+ rem wait time for “we already have karaoke, regen anyway?”-type questions
        set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=250                                       %+ rem wait time for “we already have karaoke, regen anyway?”-type questions
        set PROMPT_CONSIDERATION_TIME=20                                                               %+ rem wait time for “does this AI command look sane”-type questions
        SET PROCEED_WITH_AI_CONSIDERATION_TIME=40                                                      %+ rem wait time for “Proceed with this AI generation?”-type questions
        SET PROCEED_WITH_AI_CONSIDERATION_TIME=30                                                      %+ rem wait time for “Proceed with this AI generation?”-type questions
        set PROMPT_EDIT_CONSIDERATION_TIME=20                                                          %+ rem wait time for “do you want to edit the AI prompt”-type questions
        set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=0                                         %+ rem wait time for “hey lyrics not found!”-type notifications/questions. Set to 0 to not pause at all.
        set WHISPERTIMESYNC_QUERY_WAIT_TIME=300
        set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=120                                                  %+ rem wait time for “edit it now that we’ve made it?”-type questions ... Have decided it should probably last longer than the average song
        set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=1200                                                 %+ rem wait time for “edit it now that we’ve made it?”-type questions ... Have decided it should probably last longer than the average song
        set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=600                                                  %+ rem wait time for “edit it now that we’ve made it?”-type questions ... Have decided it should probably last longer than the average song
        set EDIT_KARAOKE_AFTER_FORCE_REGEN_WAIT_TIME=12                                                %+ rem wait time for “edit it now that we’ve made it?”-type questions when we are in force-regen mode
        set KARAOKE_APPROVAL_WAIT_TIME=60                                                              %+ rem wait time for “Approve/edit karaoke file” prompt after creating karaoke
        set AI_GENERATION_ANYWAY_DEFAULT_ANSWER=no                                                     %+ rem default answer for “Generate AI anyway?”-type questions


REM CONFIG: 2023:
        set SKIP_SEPARATION=1                                                                          %+ rem 1=disables the 2023 process of separating vocals out, a feature that is now built in to Faster-Whisper-XXL, 0=run old code that probably doesn’t work anymore
        SET SKIP_TXTFILE_PROMPTING=0                                                                   %+ rem 0=use lyric file to prompt AI, 1=go in blind
        rem set TRANSCRIBER_TO_USE=call whisper-faster.bat 
        rem SET SKIP_TXTFILE_PROMPTING=0  





REM Setting valid extensions and lockfile name:
        rem ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
        goto :set_TRANSCRIBER_VALID_EXTENSIONS_AND_LOCK_FILE_NAME_done
        :set_TRANSCRIBER_VALID_EXTENSIONS_AND_LOCK_FILE_NAME
                set TRANSCRIBER_TO_USE=Faster-Whisper-XXL.exe                                               %+ rem Command to generate/transcribe [with AI]
                set TRANSCRIBER_PDNAME=faster-whisper-xxl.exe                                               %+ rem probably the same as as %TRANSCRIBER_TO_USE%, but technically         it’s whatever string can go into %@PID[] that returns a nonzero result if we are running a transcriber
                set TRANSCRIBER_VALID_EXTENSIONS=*.wav;*.flac;*.mp3;*.mp4;*.mpweg;*.mpga;*.m4a;*.wav;*.webm %+ rem valid extensions that our transcriber can transscribe
                set search=%@SEARCH[%TRANSCRIBER_TO_USE%]
                rem If you don’t add the machinename to the lockfile, then running on multiple machines is not possible 
                rem because one will lock the other. Therefore, the lockfile filename must also include the machinename
                rem For similar reasoning, this one should NOT include the process name in the filename
                rem (but we’ll put it in the contents of the file later, of course, along with start time):
                        set TRANSCRIBER_LOCK_FILE=%@UNQUOTE[%@path[%search%]%@NAME[%TRANSCRIBER_TO_USE%]].%MACHINENAME%.lock
                        rem echo %ANSI_COLOR_DEBUG%- TRANSCRIBER_LOCK_FILE is “%TRANSCRIBER_LOCK_FILE%”     %faint_on%(search=“%search%”)%faint_off%
        return
        :set_TRANSCRIBER_VALID_EXTENSIONS_AND_LOCK_FILE_NAME_done
        rem ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


rem Set filemask to match audio files:
        iff not defined filemask_audio then
                set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        endiff

REM validate environment [once]:
        call status-bar unlock
        if not defined UnicodeOutputDefault (set UnicodeOutputDefault=no)
        iff "1" != "%VALIDATED_CREATE_LRC_FF%" then
                rem Default values to help portability:
                        if not defined MACHINENAME .and. "" != "%USERDOMAIN%"      set MACHINENAME=%USERDOMAIN%
                        if not defined ESCAPE                                      set                                            ESCAPE=%@CHAR[27]
                        if not defined ANSI_ESCAPE                                 set                                       ANSI_ESCAPE=%ESCAPE%[
                        if not defined ANSI_CURSOR_CHANGE_TO_DEFAULT               set        ANSI_CURSOR_CHANGE_TO_DEFAULT=%ANSI_ESCAPE%0 q
                        if not defined ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING        set ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING=%ANSI_ESCAPE%1 q
                        if not defined ANSI_CURSOR_CHANGE_TO_BLOCK_STEADY          set ANSI_CURSOR_CHANGE_TO_BLOCK_STEADY=%ANSI_ESCAPE%2 q
                        if not defined ANSI_CURSOR_CHANGE_TO_UNDERLINE_BLINKING    set ANSI_CURSOR_CHANGE_TO_UNDERLINE_BLINKING=%ansi_escape%3 q
                        if not defined ANSI_CURSOR_CHANGE_TO_UNDERLINE_STEADY      set ANSI_CURSOR_CHANGE_TO_UNDERLINE_STEADY=%ansi_escape%4 q
                        if not defined ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING set ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING=%ansi_escape%5 q
                        if not defined ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_STEADY   set ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_STEADY=%ansi_escape%6 q
                        if not defined ANSI_COLOR_BLUE                             set ANSI_COLOR_BLUE=%@CHAR[27][34m
                        if not defined ANSI_COLOR_BRIGHT_YELLOW                    set ANSI_COLOR_BRIGHT_YELLOW=%@CHfR[27][93m
                        if not defined ANSI_COLOR_ORANGE                           set ANSI_COLOR_ORANGE=%@CHAR[27][38;2;235;107;0m
                        rem TODO BLINK_ON, BLINK_OFF ITALICS_ON ITALICS_OFF, QUOTE, etc
                rem Perform the actual validations:
                        @call validate-in-path              %TRANSCRIBER_TO_USE% get-lyrics.bat  debug.bat  lyricy.exe  copy-move-post  paste.exe  divider  less_important  insert-before-each-line  bigecho  deprecate  errorlevel  grep  isRunning fast_cat  top-message  top-banner  unlock-top  status-bar.bat footer.bat unlock-bot deprecate.bat  add-ADS-tag-to-file.bat remove-ADS-tag-from-file.bat display-ADS-tag-from-file.bat display-ADS-tag-from-file.bat review-subtitles.bat  error.bat print-message.bat  get-lyrics-for-file.btm delete-bad-ai-transcriptions.bat subtitle-postprocessor.pl lyric-postprocessor.pl success.bat alarm.bat  WhisperTimeSync.bat WhisperTimeSync-helper.bat restart-winamp.bat appdata.bat winamp.bat display-horizontal-divider.bat
                        @if not defined TRANSCRIBER_PDNAME  @call validate-environment-variable  TRANSCRIBER_PDNAME  skip_validation_existence
                        @if not defined FILEMASK_AUDIO        @call validate-environment-variable  FILEMASK_AUDIO      skip_validation_existence
                        @call validate-environment-variables  ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET UnicodeOutputDefault machinename 
                        @call validate-is-function            ansi_randfg_soft randfg_soft ANSI_CURSOR_CHANGE_COLOR_WORD                
                        @call validate-plugin                 StripANSI
                        @call checkeditor
                        @set VALIDATED_CREATE_LRC_FF=1
        endiff

                        



















rem ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
rem ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
rem ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
rem ══════════════════════════════════════════════════════════════════════════════════    BEGIN    ════════════════════════════════════════════════════════════════════════════════════════════════
rem ══════════════════════════════════════════════════════════════════════════════════    BEGIN    ════════════════════════════════════════════════════════════════════════════════════════════════
rem ══════════════════════════════════════════════════════════════════════════════════    BEGIN    ════════════════════════════════════════════════════════════════════════════════════════════════
rem ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
rem ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
rem ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════



rem Start our processing of command line parameters with giving USAGE if no command line parameterse are given:
        iff "%1" == "" then 
                gosub usage
                goto /i The_Very_END
        endiff

rem Pre-Cleanup:
        unset /q JUST_APPROVED_LYRICLESSNESS goto_forcing_ai_generation ABANDONED_SEARCH LYRICLESSNESS_STATUS FAILURE_ADS_RESULT LYRIC_APPROVAL LYRICS_APPROVAL LYRICLESSNESS_APPROVAL  MAYBE_SRT_1 MAYBE_SRT_2 WAITING_ON_LOCKFILE_ROW WAITING_ON_LOCKFILE_COL WAITING_FOR_COMPL_ROW WAITING_FOR_COMPL_COL LYRIC_STATUS our_lyrics* tmppromptfile file_title file_song    
REM values set from parameters:
        *setdos /x-4
        set SONGFILE=%@UNQUOTE["%1"]
        set SONGBASE=%@UNQUOTE["%@NAME["%SONGFILE%"]"]`` %+ rem this might not work anymore 🐮
        set SONGDIR=%@UNQUOTE["%@PATH["%@UNQUOTE["%@FULL["%SONGFILE%"]"]"]"]
        setdos /x0

        set pushd_performed_in_create_srt=0
        iff "%_CWD\" != "%SONGDIR%" then
                pushd "%SONGDIR%"
                set pushd_performed_in_create_srt=1
        endiff

        set OUTPUT_DIR=%@Unquote[%@ReReplace[\\$,,%SONGDIR%]]

        rem DEBUG: echo SONGDIR is “%SONGDIR%” , cwd=“%_CWD” , SONGBASE=“%SONGBASE%”, songfile=“%SONGFILE%” %+ *pause

        *setdos /x-4
        setdos /x0
        set LRC_FILE=%SONGDIR%%SONGBASE%.lrc
        set SRT_FILE=%SONGDIR%%SONGBASE%.srt
        set TXT_FILE=%SONGDIR%%SONGBASE%.txt
        set JSN_FILE=%SONGDIR%%SONGBASE%.json
        if "%@EXT[%2]" == "txt" (
                set POTENTIAL_LYRIC_FILE=%@UNQUOTE[%2]
        ) else (                
                set POTENTIAL_LYRIC_FILE=%@UNQUOTE[%TXT_FILE%]
        )
        rem VOC_FILE=%SONGDIR%%SONGBASE%.vocals.wav
        rem LRCFILE2=%SONGDIR%%SONGBASE%.vocals.lrc


rem BRANCH CONDITIONS: Only postprocess files, or only make the LRC, if we’ve been told to just do that part:
        if  "%1" == "last" (goto /i actually_make_the_lrc) %+ rem to repeat the last regen
        iff "%1" ==  "postprocess_lrc_srt_files" then
                gosub postprocess_lrc_srt_files
                goto /i EOF
        endiff


REM Pre-run announce:
        gosub divider
        call  bigecho "%STAR% Creating karaoke for %left_quotes%%@ansi_rgb[170,170,244]%italics_on%%songfile%%italics_off%%ansi_color_normal%”"

REM Pre-run header:
        rem got 2 in a row so removed this 2024/12/11: gosub divider
        echos %ansi_color_unimportant%
        timer /5 on >nul                     %+ rem Let’s time the overall process
        unset /q LYRIC_ATTEMPT_MADE
        unset /q OKAY_THAT_WE_HAVE_SRT_ALREADY
        unset /q ANSWER
        if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav)
        if exist     *vad_original*.srt (*del /q     *vad_original*.srt)
        
REM Cosmetics:
        rem Remove any leftover banners from previous runs, then
                rem Hurts actually: echos %@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;36r%@CHAR[27]8%@CHAR[27][u               

        rem Fix cursor color, and any custom rgb recolorings of the default character color:
                echos %CURSOR_RESET%%@CHAR[27]]10;rgb:c0/c0/c0%@CHAR[27]\%@CHAR[27]]11;rgb:00/00/00%@CHAR[27]\




REM Set flags and default values:

        rem Flags:
                set CLEANUP=0 
                set FAST_MODE=0 
                set FORCE_REGEN=0 
                set SOLELY_BY_AI=0
                set been_here_1339=0
                set AUTO_LYRIC_APPROVAL=0
                set ALREADY_HAND_EDITED=0
                set PROMPT_ANALYSIS_ONLY=0
                set CHIPTUNE_ENCOUNTERED=0
                set LAUNCHING_AI_DISPLAYED=0
                set LOCKFILE_MENTIONED_ALREADY=0
                set JUST_RENAMED_TO_INSTRUMENTAL=0
                set ALREADY_ASKED_TO_DELETE_LOCKEFILE=0
                set DELETE_BAD_AI_TRANSCRIPTIONS_FIRST=1                                                       %+ rem Whether we run delete-bad-ai-transcriptions in folders ... This used to be configurable, but now the system only runs the cleaner every 72 hours at most, so it doesn’t represent enough of a time-slow down to be considered a configurable option anymore. Better to always keep it on.
                set SONG_PROBED_VIA_CALL_FROM_CREATE_SRT=0                                                     %+ rem Also gets set later but put here as a formality so this list is more thorough
                set LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE=0
                set LOCKFILE_NOT_FOR_THIS_PROCESS_MENTIONED=0

        rem Default values that can be overridden by environment variables:
                set  OUR_LANGUAGE=%DEFAULT_LANGUAGE%
                set VAD_THRESHOLD=%DEFAULT_VAD_THRESHOLD%
                if "" !=      "%USE_LANGUAGE%"       set  OUR_LANGUAGE=%USE_LANGUAGE%                          %+ rem deprecated legacy option——now renamed as “%%”——that we’ve removed from the documentation but are leaving for backward compatibility
                if "" != "%OVERRIDE_LANGUAGE%"       set  OUR_LANGUAGE=%OVERRIDE_LANGUAGE%
                if "" != "%OVERRIDE_VAD_THRESHOLD%"  set VAD_THRESHOLD=%OVERRIDE_VAD_THRESHOLD%

                unset /q karaoke_status

        rem pause "our language is %OUR_LANGUAGE"


        rem Set if we approving lyrics automatically
                iff "%CONSIDER_ALL_LYRICS_APPROVED%" == "1" then
                        set AUTO_LYRIC_APPROVAL=1
                        rem This is deprecated/testing only and we don’t want it to persist:
                        unset /q CONSIDER_ALL_LYRICS_APPROVED   
                endiff                


rem Process command line parameters:        
        :process_for_mode_variants
        set TMP_PARAM_1=%1
        echos %ANSI_COLOR_MAGENTA%
        iff "%@UNQUOTE["%TMP_PARAM_1%"]" != "" then
                set special_parameters_possibly_present=1
        else
                set special_parameters_possibly_present=0
        endiff
        iff "1" == "%special_parameters_possibly_present%" then
                set special=%TMP_PARAM_1%
                rem echo checking[ee] special=“%special%” ... %%1=“%1” %+ pause
                if "%special%" == "ai" .or. "1" == "%FORCE_AI_ENCODE_FROM_LYRIC_GET%" (set SOLELY_BY_AI=1)
                if "%special%" == "cleanup"            (set  CLEANUP=1            )
                if "%special%" == "force"              (set  FORCE_REGEN=1          %+ set LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE=1)
                if "%special%" == "lyriclessness"      (set  NEVERMIND_THIS_ONE=42) %+ rem Protection from invalid invocation where this gets snuck in as the 2ⁿᵈ argument. Our way to deal with it is to ignore it...for reasons
                if "%special%" == "force-regen"        (set  FORCE_REGEN=1        )
                if "%special%" == "redo"               (set  FORCE_REGEN=1        )
                if "%special%" == "ala"                (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==  "la"                (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==     "LyricApprove"   (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==     "LyricApproved"  (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==     "LyricApproval"  (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==     "LyricsApprove"  (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==     "LyricsApproved" (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" ==     "LyricsApproval" (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyricsApproval" (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyricApproval"  (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyricsApproved" (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyricApproved"  (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyricsApprove"  (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyricApprove"   (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyrics"         (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "AutoLyric"          (set  AUTO_LYRIC_APPROVAL=1)
                if "%special%" == "prompts"            (set PROMPT_ANALYSIS_ONLY=1)
                if "%special%" == "PromptAnalysis"     (set PROMPT_ANALYSIS_ONLY=1)
                shift 
                rem  after “shift”,  %1$ is now the remaining arguments (if any)
                rem echo %reverse_on%after “shift”, %%1$ is now: %1$%reverse_off% >nul
                goto /i process_for_mode_variants
        endiff    


        rem echo AUTO_LYRIC_APPROVAL is %AUTO_LYRIC_APPROVAL%  %+ pause
        
        if "1" == "%CLEANUP%" (goto /i just_do_the_cleanup)

        set MAKING_KARAOKE=1

              
        rem todo: consider going back to the top of this section 2 or 3 times for easier simultaneous option stacking but then you gotta think about what all the combinations really mean

                          
 rem Adjust wait times if we are in automatic mode. Also, automatic lyric approval means we’re streamilined and should auto-fast it as well:
        iff "1" == "%AUTO_LYRIC_APPROVAL%" .or. "1" == "%FAST_MODE%" then
                set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=3                 %+ rem wait time for "are these lyrics good?"-type questions
                set AI_GENERATION_ANYWAY_WAIT_TIME=3                       %+ rem wait time for "no lyrics, gen with AI anyway"-type questions
                set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=3     %+ rem wait time for "we already have karaoke, regen anyway?"-type questions
                set PROMPT_CONSIDERATION_TIME=4                            %+ rem wait time for "does this AI command look sane"-type questions
                set PROMPT_EDIT_CONSIDERATION_TIME=3                       %+ rem wait time for "do you want to edit the AI prompt"-type questions
                set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=2     %+ rem wait time for "hey lyrics not found!"-type notifications/questions
                set WHISPERTIMESYNC_QUERY_WAIT_TIME=9
                set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=3                %+ rem wait time for "edit it now that we’ve made it?"-type questions ... Have decided it should probably last longer than the average song
                SET PROCEED_WITH_AI_CONSIDERATION_TIME=6                   %+ rem wait time for "Proceed with this AI generation?"-type questions
        endiff

        iff "1" == "%FORCE_REGEN%" then
                set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=10
        endiff

        iff "1" == "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" then                     
                set AI_GENERATION_ANYWAY_WAIT_TIME=0                       %+ rem wait time for "no lyrics, gen with AI anyway"-type questions
                set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=0                %+ rem wait time for "edit it now that we’ve made it?"-type questions ... Have decided it should probably last longer than the average song
                set KARAOKE_APPROVAL_WAIT_TIME=0
                set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=0                 %+ rem wait time for "are these lyrics good?"-type questions
                SET PROCEED_WITH_AI_CONSIDERATION_TIME=0                   %+ rem wait time for "Proceed with this AI generation?"-type questions
                set PROMPT_CONSIDERATION_TIME=0                            %+ rem wait time for "does this AI command look sane"-type questions
                set PROMPT_EDIT_CONSIDERATION_TIME=0                       %+ rem wait time for "do you want to edit the AI prompt"-type questions
                set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=0     %+ rem wait time for "we already have karaoke, regen anyway?"-type questions
                set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=0     %+ rem wait time for "hey lyrics not found!"-type notifications/questions
                set WHISPERTIMESYNC_QUERY_WAIT_TIME=0
        endiff                                              


REM Determine our expected input and output files:
        unset /q INPUT_FILE
        set INPUT_FILE=%SONGFILE%
        rem EXPECTED_OUTPUT_FILE=%LRC_FILE%   %+ rem //This was for the 2023 version
        SET EXPECTED_OUTPUT_FILE=%SRT_FILE%



rem Make sure it’s a transcribeable filename:
        rem echo α 100
        :regenerate_karaoke
        gosub validate_transcribeable_filename "%INPUT_FILE%" "transcribing"
        if "%_?" == "666" .or. "%retval%" == "666" .or. "1" == "%goto_end%" (
                rem echo %EMOJI_STOP_SIGN% Aborting...
                goto /i The_Very_Very_END
        )
        goto skip_sub_414
                                :validate_transcribeable_filename [input_file verb]
                                        rem Debug:
                                                rem echo %ansi_color_debug%- DEBUG: called validate_transcribeable_filename [input_file=%input_file% verb=%verb%]%ansi_color_normal%

                                        rem Failure flag:
                                                set fail=0

                                        rem Make our filename checks:                                                                           //NOTE: A redundant check occurs later but shoudl no longer happen, and looks like this: if "%@REGEX[instrumental,%INPUT_FILE%]" == "1" (@call warning "Sorry, nothing to transcribe because this appears to be an instrumental: %INPUT_FILE%" silent %+ goto :END)
                                                set chipt_in_filename=%@REGEX["\[[cC][hH][iI][pP][tT][uU][nN][eE][sS]*\]",%INPUT_FILE%]
                                                set chipt_in_foldname=%@REGEX["[\\\[\(][cC][hH][iI][pP][tT][uU][nN][eE][sS]*[\\\]\)]",%@FULL["%INPUT_FILE%"]]
                                                set instr_in_filename=%@REGEX["[^\-][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][\)\]]",%INPUT_FILE%]
                                                set instr_in_foldname=%@REGEX["[\[\(\\][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][sS]*[\)\]\\]",%@FULL["%INPUT_FILE%"]]
                                                set sndfx_in_filename=%@REGEX["[\[\(][sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*[\)\]]",%INPUT_FILE%]
                                                set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*[\\\]\)]",%@FULL["%INPUT_FILE%"]]              %+ rem OLD
                                                set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*",%@FULL["%INPUT_FILE%"]]                      %+ rem NEW: to accomodate folder names like “sound effects & ambient sound”
                                                set iscis_in_filename=%@REGEX["\[[Uu][Nn][Tt][Rr][Aa][Nn][Ss][Cc][Rr][Ii][Bb][Ee][Aa][Bb][Ll][Ee]*\]",%INPUT_FILE%]
                                                set iscis_in_foldname=%@REGEX["[\\\[\(][Uu][Nn][Tt][Rr][Aa][Nn][Ss][Cc][Rr][Ii][Bb][Ee][Aa][Bb][Ll][Ee]*[\\\)\]]",%@FULL["%INPUT_FILE%"]]

                                        rem These definitely happen in this order for the reason of error message precedence:
                                                unset /q fail_type fail_point
                                                if "1" == "%instr_in_filename%" ( set fail_type=instrumental     %+ set fail_point=filename) 
                                                if "1" == "%chipt_in_filename%" ( set fail_type=chiptune         %+ set fail_point=filename)
                                                if "1" == "%sndfx_in_filename%" ( set fail_type=sound effects    %+ set fail_point=filename)
                                                if "1" == "%iscis_in_filename%" ( set fail_type=untranscribeable %+ set fail_point=filename)
                                                if "1" == "%instr_in_foldname%" ( set fail_type=instrumental     %+ set fail_point=dir name)
                                                if "1" == "%chipt_in_foldname%" ( set fail_type=chiptune         %+ set fail_point=dir name)
                                                if "1" == "%sndfx_in_foldname%" ( set fail_type=sound effects    %+ set fail_point=dir name)
                                                if "1" == "%iscis_in_foldname%" ( set fail_type=untranscribeable %+ set fail_point=dir name)

                                        rem Debug stuffs:
                                                goto :debug_406_no
                                                goto :debug_406_yes
                                                     :debug_406_yes
                                                        echo chipt_in_foldname == “%chipt_in_foldname%”
                                                        echo instr_in_filename == “%instr_in_filename%”
                                                        echo sndfx_in_filename == “%sndfx_in_filename%”
                                                        echo iscis_in_filename == “%iscis_in_filename%”
                                                        echo chipt_in_filename == “%chipt_in_filename%”
                                                        echo instr_in_foldname == “%instr_in_foldname%”
                                                        echo sndfx_in_foldname == “%sndfx_in_foldname%”
                                                        echo iscis_in_foldname == “%iscis_in_foldname%”
                                                        echo fail_type         == “%fail_type%”
                                                        echo fail_point        == “%fail_point%”
                                                :debug_406_no

                                        rem Set environment flag to signal other processes, but I think this is unused, just an idea:
                                                if "dir name" == "%fail_point%" set BAD_AI_TRANSCRIPTION_FOLDER=%_CWP                                                                                

                                        rem Notify of error and quit if applicable:
                                                if "" == "%fail_type%" goto :we_are_fine_403 %+ rem else:
                                                        unset /q strN
                                                        if "%fail_type%" == "instrumental" set strN=n
                                                        call bigecho "%ansi_color_warning%%star2%%star2%%star2%%star2%%star2% %fail_type%!!!%star2%%star2%%star2%%star2%%star2%%ansi_color_normal%"
                                                        echo %ansi_color_warning%%no% Sorry! Not %italics_on%%verb%%italics_off% because this %italics_on%%fail_point%%italics_off% indicates a%strN% %ansi_resetNOLETSNOTDOTHAT%%ansi_color_red%%italics_on%%blink_on%%fail_type%%blink_off%%italics_off%%ANSI_COLOR_WARNING% file:%ansi_color_normal% %faint_on%“%@UNQUOTE["%INPUT_FILE%"]”%faint_off%%ansi_color_normal%
                                                        set fail=1
                                                        call sleep 1
                                                :we_are_fine_403

                                        rem Return success/fail:
                                                if "1" == "%fail%" (return 666)
                                                if "1" != "%fail%" (return 777)
                                return

                
        :skip_sub_414


rem Do subtitles exist?
        rem pause "do subtitles exist"
        iff exist "%EXPECTED_OUTPUT_FILE%" .and. "1" !=  "%FORCE_REGEN%" then
                rem echo exp output file exists!
                rem echo %big_Top%%ansi_color_warning_soft%%star2%%star2% Karaoke already exists!%ansi_color_normal%
                rem echo %big_bot%%ansi_color_warning_soft%%star2%%star2% Karaoke already exists!%ansi_color_normal%
                echo %big_top%%ansi_color_warning_soft%%star2% Karaoke already exists!%ansi_color_normal%
                echo %big_bot%%ansi_color_warning_soft%%star2% Karaoke already exists!%ansi_color_normal%
                gosub divider
                rem set goto_end=1
                goto /i END
        else
                rem echo exp output file does not exist! 
                rem echo goto_end == "%goto_end%" 
        endiff
        if "1" == "%goto_end%" goto /i END
        REM echo if exist "%POTENTIAL_LYRIC_FILE%" 
        iff exist "%POTENTIAL_LYRIC_FILE%" then
                rem gosub refresh_lyric_status "%POTENTIAL_LYRIC_FILE%"
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: POTENTIAL_LYRIC_FILE file exists! - %lq%%POTENTIAL_LYRIC_FILE%%rq%%ANSI_COLOR_NORMAL% (status=%lq%%LYRIC_STATUS%%rq%)
        else
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: POTENTIAL_LYRIC_FILE file does not exist! - %lq%%POTENTIAL_LYRIC_FILE%%rq%%ANSI_COLOR_NORMAL%
        endiff

               
rem If the file has been marked as failed previously, abort (unless in force mode):
        rem echo α 200
        unset /q failure_ads_result
        set  failure_ads_result=%@EXECSTR[type "%@UNQUOTE["%INPUT_FILE%"]:karaoke_failed"  >>&>nul] 
        rem pause "failure_ads_result is %lq%%failure_ads_result%%rq%"
        REM echo failure_ads_result is “%failure_ads_result%”, force_regen=“%force_regen%”
        iff "True" == "%failure_ads_result%" .and. "1" != "%FORCE_REGEN%" .and. "1" != "%PROMPT_ANALYSIS_ONLY%" then
                gosub divider
                @call bigecho "%ansi_color_warning%%star2%%star2%%star2%%star2%%star2% Already failed!!! %star2%%star2%%star2%%star2%%star2%%ansi_color_normal%"
                @call warning "Sorry, this file has failed in transcription, and won’t be tried again without the “force” parameter being used" silent 
                @call warning "     %INPUT_FILE%     ``"
                gosub divider
                unset /q answer
                :ask_about_instrumental_480
                call AskYN "Rename it as “[untranscribeable]” to prevent this prompt from coming up again [TODO OPTIONS]" no 20 IQPS I:no_but_mark_it_instrumental_instead,Q:enQueue_in_winamp,P:play_it,S:no_instead_mark_mark_as_sound_effect %+ rem TODO remove hard-coded wait time
                        gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                        gosub check_for_answer_of_P "%@UNQUOTE["%INPUT_FILE%"]"
                        gosub check_for_answer_of_Q "%@UNQUOTE["%INPUT_FILE%"]"
                        gosub check_for_answer_of_S "%@UNQUOTE["%INPUT_FILE%"]"
                        if  "P" == "%ANSWER%" .or. "Q" == "%ANSWER%" .or. "S" == "%ANSWER%" goto /i ask_about_instrumental_480
                        iff "Y" == "%ANSWER%" then
                                unset /q answer
        echo                    gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental "%@UNQUOTE["%INPUT_FILE"]" "untranscribeable" GOAT %+ pause
                                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental "%@UNQUOTE["%INPUT_FILE"]" "untranscribeable"
                                
                                goto /i END
                        endiff
                goto /i END
        endiff

REM Values fetched from input file:
        :initial_probing
        rem echo solely_by_ai is %solely_by_ai% %+ pause
        rem echo α 300
        iff "1" == "%SOLELY_BY_AI%" .and. "1" != "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" then
                set PROMPT_CONSIDERATION_TIME=3
                set PROMPT_EDIT_CONSIDERATION_TIME=3
        endiff
        set SONG_PROBED_VIA_CALL_FROM_CREATE_SRT=0
        if      exist "%SONGFILE%"  echos %ansi_color_success%%STAR2% songfile exists!
        iff not exist "%SONGFILE%" then
                rem pause "let’s see if the songfile not existing is why the step craps out - create-srt-from-file #511"
                echos %ansi_color_alarm%%STAR2% songfile “%SONGFILE%” does NOT exist!  Aborting!
                goto /i END
        endiff
        iff "1" != "%SOLELY_BY_AI%" then                                
                echo %faint_on% ... Probing!%faint_off%                                                          %+ rem echo %ansi_color_unimportant%🐐 %@cool[calling %lq%get-lyrics-for-file "%SONGFILE%" SetVarsOnly%rq%] [22111] - CALLING %@colorful_string[━━━━━━━━━━━━━━━━(to probe the file)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] CWP=%_CWP                
                rem 2025/07/17: separating force_regen into separaet flags for karaoke/lyric process, so we shouldn’t just pass it on like this anymore:
                rem call get-lyrics-for-file "%SONGFILE%" SetVarsOnly %@IF["1" == "%FORCE_REGEN%",force,]        %+ rem probes the song file and sets FILE_ARTIST / FILE_TITLE / etc %+ rem echo %ansi_color_unimportant%🐐 return: %@cool[get-lyrics-for-file] [22111] - RETURNED %@colorful_string[━━━━━━━━━━━━━━━(after file probing)━━━━━━━━━━━━━━ CWP=%_CWP] 
                call get-lyrics-for-file "%SONGFILE%" SetVarsOnly                                                %+ rem probes the song file and sets FILE_ARTIST / FILE_TITLE / etc %+ rem echo %ansi_color_unimportant%🐐 return: %@cool[get-lyrics-for-file] [22111] - RETURNED %@colorful_string[━━━━━━━━━━━━━━━(after file probing)━━━━━━━━━━━━━━ CWP=%_CWP] 
                set SONG_PROBED_VIA_CALL_FROM_CREATE_SRT=1                                                       %+ rem Set the fact that is has been probed
                set last_file_probed=%SONGFILE%                                                                  %+ rem prevents get-lyrics from probing twice
                if "%_CWD\" != "%SONGDIR%" (*cd "%SONGDIR%")
        else
                set SONG_PROBED_VIA_CALL_FROM_CREATE_SRT=0
                unset /q FILE_TITLE
                echo.
        endiff

        REM Determine the base text used for our window title:
                set BASE_TITLE_TEXT=%FILE_ARTIST - %FILE_TITLE% 



REM Chiptune stuff:
        rem call debug "CHIPTUNE_ENCOUNTERED is “%CHIPTUNE_ENCOUNTERED%”"
        if "1" == "%CHIPTUNE_ENCOUNTERED%" goto /i END



REM Lyric file stuffs:
        rem echo α 400
        set sidecar_was_present_from_the_start=0
        iff not exist "%POTENTIAL_LYRIC_FILE%" then
                rem echo %star% Lyrics don’t exist ... %faint_on%[PROMPT_ANALYSIS_ONLY=%PROMPT_ANALYSIS_ONLY%]...so if we are in prompt analysis mode we should actually goto /i END!!%faint_off%
                if "1" == "%PROMPT_ANALYSIS_ONLY%" (pause %+ goto /i END)
        endiff
        if not exist "%POTENTIAL_LYRIC_FILE%" goto /i end_of_potential_lyric_file_initial_processing
                set TXT_FILE=%@UNQUOTE["%POTENTIAL_LYRIC_FILE%"]
                echos %STAR%%ANSI_COLOR_IMPORTANT% Checking lyrics at %faint_on%%italics_on%%lq%%TXT_FILE%%rq%%italics_off%%faint_off%...%ansi_color_normal%
                gosub refresh_lyric_status "%TXT_FILE%"
                iff "%LYRIC_STATUS%" == "APPROVED" then
                        echo %ansi_color_bright_green%...%italics_on%and they are %blink_on%approved%blink_off%!%italics_off%%ansi_color_normal%
                        set sidecar_was_present_from_the_start=1
                        set LYRIC_FILE=%TXT_FILE%
                        goto /i AI_generation
                else
                        echo %ansi_color_bright_red%...but the lyrics are not approved!%ansi_color_normal%
                        goto /i AI_generation
                endiff
        :end_of_potential_lyric_file_initial_processing

rem If we are doing it *SOLELY* by AI, skip some of our lyric logic:
        rem this doesn’t really do anything, it’s the next thing: i f "1" != "%SOLELY_BY_AI%" go to : solely_by_ai_jump 1

REM display debug info:
        :Retry_Point
        :solely_by_ai_jump1
        rem echo α 500
        if %DEBUG gt 0 echo %ansi_color_debug%- DEBUG: (8)%NEWLINE%    SONGFILE=“%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%”:%NEWLINE%    SONGFILE=“%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%”:%NEWLINE%%TAB%%TAB%%FAINT_ON%SONGBASE=“%ITALICS_ON%%SONGBASE%%ITALICS_OFF%”%NEWLINE%%TAB%%TAB%LRC_FILE=“%ITALICS_ON%%LRC_FILE%%ITALICS_OFF%”, %NEWLINE%%TAB%%TAB%TXT_FILE=“%ITALICS_ON%%TXT_FILE%%ITALICS_OFF%”%FAINT_OFF%%ansi_color_normal%
        gosub divider
        iff "1" == "%ANNOUNCE_IF_SIDECAR_FILES_EXIST%" then
                                       gosub say_if_exists SONGFILE
                                       gosub say_if_exists SRT_FILE
                                       gosub say_if_exists LRC_FILE
                                       gosub say_if_exists TXT_FILE
                                       gosub say_if_exists JSN_FILE
                if defined MAYBE_SRT_1 gosub say_if_exists MAYBE_SRT_1
                if defined MAYBE_SRT_2 gosub say_if_exists MAYBE_SRT_2
        endiff

rem If a txt file exists and it is approved, and a subtitle does not exist, jump straight to ai
        rem echos [refresh_lyric_status]
        rem echo α 600
        if "%LYRIC_STATUS%" == "" gosub refresh_lyric_status
        rem echos [/refresh_lyric_status]
        rem echo Trace %ansi_color_orange%lyric_status is "%LYRIC_STATUS%"%ansi_color_normal% %@cool[{olaf}]


REM Earlier, we retrieved the values for MAYBE_SRT_[1|2] via probing the songfile via the shared probe code in get-lyrics-for-file.btm
REM Now, let’s check these values:
        if not exist "%@UNQUOTE[%MAYBE_SRT_1%]" .and. not exist "%@UNQUOTE[%MAYBE_SRT_2%]" goto :endiff_610
                if exist "%@UNQUOTE[%MAYBE_SRT_2%]" set found_subtitle_file=%@UNQUOTE["%MAYBE_SRT_2%"]
                if exist "%@UNQUOTE[%MAYBE_SRT_1%]" set found_subtitle_file=%@UNQUOTE["%MAYBE_SRT_1%"]
                gosub divider
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%   
                call bigecho      "%ansi_color_warning_soft%%star2% Already have the karaoke!%ansi_reset%"
                call warning_soft "Pre-existing transcription found in lyric repository at: “%emphasis%%italics_on%%found_subtitle_file%%deemphasis%%italics_off%”" silent
                iff exist "%found_subtitle_file%" then
                        call review-file -wh -ins "%found_subtitle_file%"
                else
                        call warning "found subtitle file of “%found_subtitle_file%” doesn’t exist"
                endiff
                call warning_soft "Pre-existing transcription found in lyric repository at: “%emphasis%%italics_on%%found_subtitle_file%%deemphasis%%italics_off%”" silent
                echo %STAR% %ANSI_COLOR_ADVICE%Copy this file %italics_on%from our local repo%italics_off% into this folder, as a sidecar file for %@NAME[%SONGFILE%]%ansi_color_normal%
                rem You’d think the answer would be yes, but actually, every live version of a song does NOT want the LRC/SRT for the studio version instead!
                rem Sadly, these must be rejected unless explicitly accepted...
                unset /q ANSWER
                call askYN        "Copy repository version to local folder as sidecar file" no %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "Y" == "%answer%" then
                        set target_old=%@path[%@full[%songfile%]]%@name[%SONGFILE%].%@ext[%found_subtitle_file%]``
                        set target=%@path["%@UNQUOTE["%@full["%songfile%"]"]"]%@name["%SONGFILE%"].%@ext[%found_subtitle_file%]``
                        echo target_old = %target_old% >nul
                        echo target     = %target%     >nul
                        set srt_file=%target%
                        *copy /q "%found_subtitle_file%" "%target%" >&>nul
                        if not exist "%target%" (call error "target of %left_quote%%target%%right_quote% should exist now, in %left_apostrophe%%italics_on%create-srt-from-file%italics_off%%right_apostrophe% line 320ish" %+ call warning "...not sure if we want to abort right now or not..." )                                
                        iff exist "%target%" then
                                call review-file -wh "%target%" 
                        else
                                call warning "target file to review does not exist: “%target%”"
                        endiff
                        rem echo  displayaudiofilename 06
                        gosub DisplayAudioFileName
                        unset /q ANSWER
                        call  AskYN "Do these still look acceptible [%ansi_color_bright_green%H%ansi_color_prompt%=hand-edit,%ansi_color_bright_green%I%ansi_color_prompt%=Instrumental(%ansi_color_bright_green%X%ansi_color_prompt%=All)]" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME% HIX H:Yes_but_hand-_edit_them,I:Rename_as_instrumental,X:rename_all_the_files_as_instrumentals %+ rem borrowed wait time

                        iff "%ANSWER%" == "I" then
                                gosub rename_audio_file_as_instrumental
                        endiff
                        iff "%ANSWER%" == "N" then
                                call disapprove-subtitle-file "%target%"
                                unset /q ANSWER
                                call askYN "³Delete file “%target%”" yes %PROCEED_WITH_AI_CONSIDERATION_TIME% %+ rem borrowed wait time
                                iff "%ANSWER%" == "Y" then
                                        del /q "%target%" >nul
                                        goto /i retry_after_lrc_copy
                                endiff                                        
                                title %red_x% %SRT_FILE% %blink_on%NOT%blink_off% retrieved successfully! %red_x%             
                        endiff                                
                        iff "%ANSWER%" == "Y" .or. "%ANSWER%" == "H" then
                                iff "%ANSWER%" == "H" then
                                        %EDITOR% "%target%"
                                        echos Remember that leaving the file blank signals that you changedy our mind and coulnd’t find lyrics
                                        echos %emoji_pause% Hit any key when done editing... 
                                        set ALREADY_HAND_EDITED=1
                                        *pause>nul
                                endiff
                                call approve-subtitle-file "%target%"
                                call success "“%italics_on%%SRT_FILE%%italics_off%” retrieved successfully!"
                                title %CHECK% %SRT_FILE% retrieved successfully! %check%             
                        endiff                                
                        rem set goto_END=1
                        goto /i END
                endiff
        :endiff_610
        if "%goto_end%" == "1" gosub divider
        if "%goto_end%" == "1" goto /i END
        :retry_after_lrc_copy

REM if our input MP3/FLAC/audio file doesn’t exist, we have problems:
        rem echo α 700
        if not exist "%INPUT_FILE%" call validate-environment-variable INPUT_FILE
        rem iff "%FORCE_REGEN%" == "1" .or. "%SOLELY_BY_AI%" == "1" then
        rem         rem Skip validation because we’re doing things automatically
        rem else
                rem TODO: refactor this internally for speedup
                call validate-file-extension "%INPUT_FILE%" %FILEMASK_AUDIO%
        rem endiff
        rem echo α 750
        rem echo α 760
        rem echo α 770
REM If our input file is lyricless and we’ve approved its lyriclessness, then we’ve decided to transcribe without a lyrics file
        rem echo α 780
        rem call get-lyriclessness-status "%INPUT_FILE%"
        rem echo α 800
        rem echo y set LYRICLESSNESS_STATUS=%%@EXECSTR[type {lt}"%@unquote["%INPUT_FILE%"]:lyriclessness" {gt}&{gt}nul]``
        set LYRICLESSNESS_STATUS=%@EXECSTR[type <"%@unquote["%INPUT_FILE%"]:lyriclessness" >&>nul]``
        rem echo y HEY ARE WE HERE WHAT HAPPENED
        rem echo α 805
        rem echo 🐐3 LYRICLESSNESS_STATUS=“%LYRICLESSNESS_STATUS%” ... 
        rem echo α 806        
        iff "%LYRICLESSNESS_STATUS%" == "APPROVED" .and. "%LYRIC_STATUS%" != "APPROVED" then  %+ rem NOTE: sometimes we can download and approve lyrics after a songfile is set to lyriclessness, so in that situation, defer to the approved lyrics!
                rem echo α 807.5                                                                                                        
                call success "%italics_on%Lyric%underline_on%less%underline_off%ness%italics_off% already approved! Using AI only!" big
                set SOLELY_BY_AI=1
                if defined EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME .and. "0" != "%EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME%" set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=10       %+ rem 🐮 hard-coded value warning
                set goto_forcing_ai_generation=1
        else                
                rem echo α 807.6
                set goto_forcing_ai_generation=0
        endiff
        rem echo α 809
        if "1" == "%goto_forcing_ai_generation%" goto /i forcing_ai_generation
        rem echo α 809.1


REM if we already have a SRT file, we have a problem unless we’re forcing a re-creation of it:
        rem echo α 809.2
        iff exist "%SRT_FILE%" .and. "%OKAY_THAT_WE_HAVE_SRT_ALREADY%" != "1" .and. "%SOLELY_BY_AI%" != "1" then
                rem echo α 809.2.3
                iff exist "%TXT_FILE%" .and. %@FILESIZE["%TXT_FILE%"] gt 0 then
                        rem @gosub divider
                        rem call bigecho %STAR% %ANSI_COLOR_IMPORTANT_LESS%Review the lyrics:%ANSI_RESET%
                        rem @echos %ANSI_COLOR_BRIGHT_YELLOW%
                        rem (type "%TXT_FILE%" |:u8 unique-lines -A -L)|:u8 print-with-columns -wh
                        call review-file -wh "%TXT_FILE%" "Review the lyrics"
                        iff %@FILESIZE["%TXT_FILE%"] lt 5 then
                                echo         %ANSI_COLOR_WARNING%Hmm. Nothing there.%ANSI_RESET%
                        endiff
                        @gosub divider
                endiff
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%   
                call bigecho %ansi_color_warning% %emoji_warning% Already have this karaoke! %emoji_warning% %ansi_color_normal%
                call warning "We already have a file created: %emphasis%%srt_file%%deemphasis%"
                call review-subtitles "%srt_file%"
                gosub divider


                iff "%SOLELY_BY_AI" == "1" then
                        @call advice "Automatically answer the next prompt as Yes by adding the parameter “force-regen” or “redo”"
                        iff exist "%TXT_FILE%" then
                                rem echo displayaudiofilename 08
                                gosub DisplayAudioFileName

                                set answer_to_use=no
                                if "1" == "%FORCE_REGEN%" set answer_to_use=yes
                                unset /q ANSWER
                                @call AskYn "%conceal_on%5%conceal_off%Do the above lyrics look acceptable" %answer_to_use% %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME
                                iff "%answer%" == "Y" then
                                        rem Proceed with process
                                        set LYRICS_ACCEPTABLE=1
                                else
                                        ren /q "%TXT_FILE%" "%@NAME[%TXT_FILE%].txt.lyr.%_datetime.bak" >nul
                                        @call less_important "Okay, let’s try fetching new lyrics"
                                        goto /i Refetch_Lyrics
                                endiff
                        endiff
                endiff
                :automatic_skip_for_ai_parameter
                rem FORCE_REGEN is %FORCE_REGEN %+ pause
                iff "1" != "%FORCE_REGEN%" then
                        unset /q ANSWER
                        @call askYN "%conceal_on%22%conceal_off%Regenerate it anyway? %faint_on%[“no” will mark karaoke as %italics%approved%italics_off%]%faint_off%" no %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME%
                endiff
                set GOTO_END=0
                set GOTO_FORCE_AI_GEN=0
                
                iff "%ANSWER%" == "Y" .or. "1" == "%FORCE_REGEN%" then
                        iff exist "%SRT_FILE%" then
                                ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak" >nul
                        endiff
                        set OKAY_THAT_WE_HAVE_SRT_ALREADY=1

                        rem show lyrics again and delete them
                        iff exist "%txt_file%" then
                                if %@FILESIZE["%TXT_FILE%"] gt 0 call review-file -wh -stL  "%TXT_FILE%" "Existing Lyrics"
                                @call askYN "Delete the lyrics (backup is kept)" no %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME%
                                iff "Y" == "%ANSWER%" then
                                        iff exist "%txt_file%" then
                                                if %@FILESIZE["%TXT_FILE%"] gt 0 call review-file -wh -stL  "%TXT_FILE%" "Existing Lyrics"
                                                rem echos %ansi_color_removal%%emoji_axe%  `` 
                                                rem *del /p /Ns "%txt_file%"
                                                ren /q "%TXT_FILE%" "%TXT_FILE%.deleted-during-forcemode-prompt.%_datetime.bak" >nul
                                        endiff
                                        rem just do this no matter what, actually: if not exist "%txt_file%" set LYRIC_STATUS=NOT_APPROVED
                                        set LYRIC_STATUS=NOT_APPROVED
                                endiff
                        endiff
                
                        set  DEFAULT_ANSWER_FOR_THIS=no
                        if exist "%TXT_FILE%" call get-lyric-status "%TXT_FILE%"
                        if "1" == "%AUTO_LYRIC_APPROVAL%" .or. "%LYRIC_STATUS%" == "APPROVED" (set DEFAULT_ANSWER_FOR_THIS=no)

                        unset /q ANSWER
                        @call AskYN "Get new lyrics" %DEFAULT_ANSWER_FOR_THIS% %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME% %+ rem todo make unique wait time for this
                        iff "%ANSWER%" == "Y" .and. "1" !=  "%AUTO_LYRIC_APPROVAL%" then
                                echo %ansi_color_unimportant%🐐 calling get-lyrics-for-file [2]
                                unset /q LYRIC_STATUS
                                set LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE=0
                                call get-lyrics-for-file "%songfile%"
                                if "%_CWD\" != "%SONGDIR%" *cd "%SONGDIR%"
                                set last_file_probed=%SONGFILE%                               %+ rem prevents get-lyrics from probing twice
                                if "1" == "%GOTO_END_AFTER_GET_LYRICS_CALLED%" goto /i :END
                        endiff                                
                        if "1" == "%AUTO_LYRIC_APPROVAL%" set LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE=1
                        echo Used to do this here: set GOTO_FORCE_AI_GEN=1 🌵
                        if "1" == "%abort_karaoke_kreation%"           goto /i :END
                        if "1" == "%GOTO_END_AFTER_GET_LYRICS_CALLED%" goto /i :END
                        
                else
                        @call warning_soft "Not generating anything, then!"
                        if exist "%SRT_FILE%" call approve-subtitles "%SRT_FILE%"
                        rem set GoTo_END=1
                        goto /i END
                endiff
                if "1" == "%abort_karaoke_kreation%"           goto /i :END
                if "1" == "%GOTO_FORCE_AI_GEN%" set goto_Force_AI_Generation=1
                if "1" == "%GOTO_END_AFTER_GET_LYRICS_CALLED%" goto /i :END
                if "1" == "%GOTO_END%"                         goto /i :END
        endiff
        rem echo α 809.3
        iff "1" == "%goto_Force_AI_Generation%" then 
                rem echo α 809.3.2
                unset /q goto_Force_AI_Generation=1
                goto /i Force_AI_Generation
        endiff
        rem echo α 900





REM If "%SOLELY_BY_AI%" == "1", we nuke the LRC/SRT file and go straight to AI-generating, and we only use the TEXT
REM file if it is pre-approved or we are set in AutoLyricsApproval mode:
        :forcing_ai_generation
        rem echo α 1000.0
        iff "1" == "%SOLELY_BY_AI%" .and. "1" != "%AUTO_LYRIC_APPROVAL%" then
                rem echo α 1000.0.1
                @call important_less "Forcing AI generation..."
                iff exist "%LRC_FILE%" .or. exist "%SRT_FILE%"  then
                        iff "1" == "%FORCE_REGEN%" then
                                if exist "%LRC_FILE%" (ren /q "%LRC_FILE%" "%@NAME[%LRC_FILE%].lrc.%_datetime.bak")
                                if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
                        endiff
                else 
                        if "%AUTO_LYRIC_APPROVAL%" != "1" (set SKIP_TXTFILE_PROMPTING=1)
                        goto /i AI_generation
                endiff
        endiff
        rem echo α 1000.1

REM If we say "force", skip the already-exists check and contiune
        rem Orch "1" == "%AUTO_LYRIC_APPROVAL%"
        rem echo α 1100
        iff "1" == "%FORCE_REGEN%" then
                if exist "%LRC_FILE%" (ren /q "%LRC_FILE%" "%@NAME[%LRC_FILE%].lrc.%_datetime_.bak")
                rem do not do this, we’re just skipping the check, that’s all:
                rem if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
                rem no need to goto /i :attempt_to_download_LRC because that’s what’s next anyway
        else
                REM At this point, we are NOT in force mode, so:
                REM At this point, if an LRC file already exists, we shouldn’t bother generating anything...
                REM Except wait! LRCget can get incorrect LRC files, so barring approval, we shoudln’t just trust the ones we see automatically.
                REM They still need approval for us to be considered ready-to-encode.
                REM In part, because thousands of files were marked as in a state of lyriclessness/unfindeable lyrics without their sidecar LRCs being deleted as they shoudl have been
                REM But still, automatic-LRC-getting means the LRC could be wrong, so we should NOT just assume it’s approved.
                REM However, this would cause us to overwrite a possibly-good LRC file. One possibly even hand-edited.
                REM And taht would be very destructive. So we must updated our “business logic” to consider existing LRCs as needing approval before being overwritten.
                        rem if exist %LRC_FILE% (@call error   "Sorry, but %bold%LRC%bold_off% file “%italics%%LRC_FILE%%italics_off%” %underline%already%underline_off% exists!" %+ call cancelll)
                            iff exist "%LRC_FILE%" then
                                     @call warning "Sorry, but %italics_on%LRC%italics_off% file “%italics%%LRC_FILE%%italics_off%” %underline%already%underline_off% exists!%" silent 
                                     @call review-file -wh  "%LRC_FILE%"
                                     @unset /q ANSWER
                                     @call AskYN   "Mark LRC file as %italics_on%approved%italics_off%" no %EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME%
                                     @if "%ANSWER%" == "Y" call approve-subtitles "@UNQUOTE[%LRC_FILE%]"
                                     goto /i END
                            endiff

        endiff



:attempt_to_download_LRC 
:attempt_to_download_LRC_with_lyricy
        REM FAILED: Let’s NOT try downloading a LRC with lyricy first because it gets mismatches whenever none exists, which is almost always:
               rem call get-lrc-with-lyricy "%CURRENT_SONG_FILE%"
               rem if exist %LRC_FILE% (@call success "Looks like %italics_on%lyricy%italics_off% found an LRC for us!" %+ goto /i END)




REM If it’s an instrumental, don’t bother:
        rem echo α 1200
        if "%@REGEX[instrumental,%INPUT_FILE%]" == "1" (@call warning "Sorry, nothing to transcribe because this appears to be an instrumental: %INPUT_FILE%" silent %+ goto /i END)
        rem echo α 1200.1





REM In terms of automation, as of 10/28/2024 we are only comfortable with FULLY automatic (i.e. going through a whole playlist) generation
REM in the event that a txt file also exists.  To enforce this, we will only generate with a "force" parameter if the txt file does not exist.
        :check_for_txtfile
        rem echo α 1400
        if "1" == "%SOLELY_BY_AI%" goto /i we_decided_to_never_check_for_txtfile
   
        rem not exist "%TXT_FILE%" .and.  1  !=  %FORCE_REGEN%  .and.  1  ==  %LYRIC_ATTEMPT_MADE   then
        rem not exist "%TXT_FILE%" .and.  1  !=  %FORCE_REGEN%                                      then
        iff not exist "%TXT_FILE%" .and. "1" != "%FORCE_REGEN%" .and. "1" == "%LYRIC_ATTEMPT_MADE%" then
                
                :Generate_AI_Anyway_question        
                        rem echo α 1450
                        rem Refetch lyriclessness status:
                                rem echo ➕ lyriclessness status before refresh: “%LYRICLESSNESS_STATUS%”
                                if "" == "%LYRICLESSNESS_STATUS%" gosub  refresh_lyriclessness_status
                                rem echo ➕ lyriclessness status  after refresh: “%LYRICLESSNESS_STATUS%”
        
                        rem If we are approved for lyriclessness, we’ve already decided we don’t want lyrics, so
                        rem reduce the AI_GENERATION_ANYWAY_WAIT_TIME prompt time
                                rem "1" == "%JUST_APPROVED_LYRICLESSNESS%" then
                                rem echo ⏺ iff "1" == "%JUST_APPROVED_LYRICLESSNESS%"[JUST_APPROVED_LYRICLESSNESS] .or. LYRICLESSNESS_STATUS(“%LYRICLESSNESS_STATUS%”) == "APPROVED" 
                                iff "1" == "%JUST_APPROVED_LYRICLESSNESS%" .or. "%LYRICLESSNESS_STATUS%" == "APPROVED" then
                                        set AI_GENERATION_ANYWAY_WAIT_TIME=%AI_GENERATION_ANYWAY_WAIT_TIME_FOR_LYRICLESSNESS_APPROVED_FILES%
                                        set AI_GENERATION_ANYWAY_DEFAULT_ANSWER=yes
                                else
                                        set AI_GENERATION_ANYWAY_DEFAULT_ANSWER=no
                                endiff
                                rem echo ⏺ AI_GENERATION_ANYWAY_DEFAULT_ANSWER=“%AI_GENERATION_ANYWAY_DEFAULT_ANSWER%”

                        rem ASK THE ACTUAL QUESTOIN:
                                rem gosub debug_show_lyric_status
                                unset /q ANSWER
                                @call askYN "Generate AI anyway (%ansi_color_bright_green%I%ansi_color_prompt%=instrumental[%ansi_color_bright_green%X%ansi_color_prompt%=All],%ansi_color_bright_green%L%ansi_color_prompt%=Lyrics Unfindable)" %AI_GENERATION_ANYWAY_DEFAULT_ANSWER% %AI_GENERATION_ANYWAY_WAIT_TIME% ILX I:Mark_it_as_an_instrumental_track,L:Mark_lyricless,X:mark_all_as_instrumental_tracks

                        rem DEAL WITH THE ANSWERS:
                                if "%ANSWER%" == "Y" (goto /i Force_AI_Generation)
                                iff "L" == "%ANSWER%" then                        
                                        set JUST_APPROVED_LYRICLESSNESS=1
                                        set AI_GENERATION_ANYWAY_DEFAULT_ANSWER=yes
                                        set AI_GENERATION_ANYWAY_WAIT_TIME=5
                                        rem NO! This is infinite-loop-ish: goto /i :Generate_AI_Anyway_question
                                        rem Instead go to creating it now, since we marked it as lyricless
                                endiff
                                gosub check_for_answer_of_L "%@UNQUOTE["%INPUT_FILE%"]"
                                gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                                if "L" == "%ANSWER%" goto /i Force_AI_Generation

                        rem If we are still here, then:
                                iff "1" != "%ABANDONED_SEARCH%" .or. "%LYRICLESSNESS_STATUS%" == "APPROVED" then
                                        @echo %ANSI_COLOR_WARNING% %EMOJI_WARNING% Failed to generate %emphasis%%SRT_FILE% %deemphasis%%ansi_color_warning%                %emoji_warning% %ansi_color_normal%
                                        @echo %ANSI_COLOR_WARNING% %EMOJI_WARNING% because the lyrics %emphasis%%TXT_FILE% %deemphasis%%ansi_color_warning% do not exist!! %emoji_warning% %ansi_color_normal%
                                        rem @call advice  "Use “ai” option to go straight to AI generation"
                                endiff
                goto /i END
        else
                rem echo α 1475
                rem This seems inapplicable now (2024/12/11): @echo %ansi_color_warning_soft%%star% Not yet generating %emphasis%%SRT_FILE%%deemphasis%%ansi_color_warning_soft% because %emphasis%%TXT_FILE%%deemphasis%%ansi_color_warning_soft% does not exist!%ansi_color_normal%
                rem Let’s save this for our usage response: @echo %ansi_color_advice%`---->` Use “%italics_on%force%italics_off%” option to override.
                rem Let’s save this for our usage response: @echo %ansi_color_advice%`---->` Try to get the lyrics first. SRT-generation is most accurate if we also have a TXT file of lyrics!
                rem Don’t need this (2025/01/04) because get-lyrics-for-file calls its own divider: gosub divider
                iff %WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST gt 0 then
                    call pause-for-x-seconds %WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST%
                endiff

        endiff

        rem echo α 1500.0.0 ━━ "LYRICLESSNESS_STATUS" == "%LYRICLESSNESS_STATUS%" 
        if "%LYRICLESSNESS_STATUS%" == "APPROVED" goto /i do_not_refetch_lyrics
        rem echo α 1500.0.1
        rem echo α 1500.0.2 - how can this show up but not the next one?
        :Refetch_Lyrics
        rem echo α 1500.1.0 - helloooooooooooo???
        iff not exist "%TXT_FILE%" .and. "1" != "%FORCE_REGEN%" .and. "1" == "%LYRIC_ATTEMPT_MADE%" then
                rem echo α 1500.1.1
                rem this is just the same “iff” condition copied from the block above
                rem believe it or not, this is for code readability reasons :) :) :)
        else
                rem echo α 1500.1.2
                rem echo * Refetch_Lyrics[2A]: LYRIC_STATUS=“%LYRIC_STATUS%”, LYRICLESSNESS_STATUS=“%LYRICLESSNESS_STATUS%”
                if "%LYRIC_STATUS%" == "" gosub  refresh_lyric_status
                rem echo * Refetch_Lyrics[2B]: LYRIC_STATUS=“%LYRIC_STATUS%”, LYRICLESSNESS_STATUS=“%LYRICLESSNESS_STATUS%”
                if "%LYRICLESSNESS_STATUS%" == "" gosub  refresh_lyriclessness_status
                rem echo * Refetch_Lyrics[2Z]: LYRIC_STATUS=“%LYRIC_STATUS%”, LYRICLESSNESS_STATUS=“%LYRICLESSNESS_STATUS%”
                rem echo %ansi_color_normal%🐐 calling: %@cool[calling get-lyrics-for-file] [333A]
                call get-lyrics-for-file "%SONGFILE%" 
                if "1" == "%abort_karaoke_kreation%"       goto /i :end
                if "1" == "%JUST_RENAMED_TO_INSTRUMENTAL%" set GOTO_END_AFTER_GET_LYRICS_CALLED=1
                rem echo %ansi_color_normal%🐐 return: %@cool[calling get-lyrics-for-file] [333Z] [GOTO_END_AFTER_GET_LYRICS_CALLED=%GOTO_END_AFTER_GET_LYRICS_CALLED%]
                if "%_CWD\" != "%SOnGDIR%" pushd "%SONGDIR%"
                set LYRIC_ATTEMPT_MADE=1
                if "1" == "%GOTO_END_AFTER_GET_LYRICS_CALLED%" goto /i :END
                goto /i :We_Have_A_Text_File_Now
        endiff
        rem echo α 1500.1.98 - helloooooooooooo???
        rem if "1" == "%GOTO_END_AFTER_GET_LYRICS_CALLED%" set goto_end=1
        rem echo α 1500.1.99 - helloooooooooooo???
        if "1" == "%GOTO_END_AFTER_GET_LYRICS_CALLED%" goto /i END
        :We_Have_A_Text_File_Now
        rem echo α 1500.10.1 - hello???!?!?


rem GOAT hope this is the right place for this label:
:go_here_for_encoding_retries


rem Mandatory review of lyrics 
        :mandatory_review_of_lyrics
        rem echo α 1500.20.1 ━━ mandatory_review_of_lyrics
        iff exist "%TXT_FILE%" .and. %@FILESIZE["%TXT_FILE%"] gt 0 then
                rem Deprecating this section which is redundant because it’s done in get-lyrics:
                        iff 0 == 1 then
                                                        call review-file -wh -st  "%TXT_FILE%" "Review the lyrics now"
                                                        @gosub divider
                                                        gosub DisplayAudioFileName
                                                        unset /q ANSWER
                                                        @call AskYn "[REDUNDANT?] Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                                                        iff "%ANSWER%" == "N" then
                                                                %color_removal%
                                                                ren  /q "%TXT_FILE%" "%TXT_FILE%.%_datetime.bak"
                                                                %color_normal%
                                                                @call warning "Aborting because you don’t find the lyrics acceptable"
                                                                @call advice  "To skip lyrics and transcribe using only AI: %blink_on%%0 “%$ ai”%blink_off%"
                                                                unset /q ANSWER
                                                                @call AskYn   "Go ahead and use AI anyway" no %AI_GENERATION_ANYWAY_WAIT_TIME%
                                                                if "%answer%" == "Y" goto /i :Force_AI_Generation
                                                                goto /i :END
                                                        endiff
                        endiff
        else
                rem This may be a bad way to deal with the situation:
                goto /i :check_for_txtfile
        endiff


:regen_ai_prompt
:do_not_refetch_lyrics
:we_decided_to_never_check_for_txtfile
:Force_AI_Generation
:AI_generation

rem DEBUG:
        echo ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇  %@rainbow[AI generation: go!] ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ 
        rem >nul



rem Only include the “--language” part of the prompt if %OUR_LANGUAGE% is set, and not set/overrided to “None”:
        iff "%OUR_LANGUAGE%" != "None" .and. "%OUR_LANGUAGE%" != "" then
                set LANGUAGE_PART_OF_PROMPT=--language=%OUR_LANGUAGE%
        else
                unset /q LANGUAGE_PART_OF_PROMPT
        endiff
        if "1" == "%DEBUG_TRACE_CSFF%" pause "did we get here 993"

REM if a text file of the lyrics exists, we need to engineer our AI transcription prompt with it to get better results
        :reassemble_prompt
        rem 2023 version: set CLI_OPS=
        rem Not adding txt to output_format in case there were hand-edited lyrics that we don’t want to overwrite already there
        rem CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words True  --beep_off --check_files --sentence --standard       --max_line_width 99 --ff_mdx_kim2 --verbose True
        rem CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words True  --beep_off --check_files --sentence --standard       --max_line_width 25 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files                             --max_line_width 30 --ff_mdx_kim2 --verbose True
        rem CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files --vad_max_speech_duration 6 --max_line_width 30 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files                             --max_line_width 30 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_threshold 0.35 --max_segment_length isn’t even an option! 5
        :et CLI_OPS=--vad_filter false --model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_filter False   --max_segment_length isn’t even an option! 5
        rem some tests with Destroy Boys - Word Salad & i threw glass at my... were done with 9 & 10
        rem 9:
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_filter False   
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --vad_filter False   -vad_threshold 0.35 --verbose True
        rem CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  -vad_threshold 0.35 --vad_max_speech_duration_s 5   --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 200
        rem 10v1: is better than 9 in one case, same in another
        rem CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_max_speech_duration_s 5   --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 201
        rem 11v2: worse than 9 or 10 definitely doesn’t pick up on as many lyrics as prompt v9 prompt
        rem CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_max_speech_duration_s 5   --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 202 --vad_threshold 0.35
        rem 9v3: making vad_filter false requires taking out other vad-related args or it errors out
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --verbose True
        rem 9v4: seeing if --sentence still works with 9v3 ... may have to remove verbose?
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True
        rem 9v5:  let’s experiment with maxlinecount=1
        :et CLI_OPS=--model large-v2 --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True %PARAM_2% %3$
        rem THE IDEA GARBAGE CAN: 9v5:
        rem Possible improvements, but in practice missed like 2/3rds of X-Ray Spex - Oh Bondage, Up yours! (blooper live version from 2-cd set) whereas vad_filter=false did not
        rem --vad_max_speech_duration_s 5:     [default= ♾] Limits the maximum length of a speech segment to 5 seconds, forcing breaks if a segment runs too long.
        rem --vad_min_speech_duration_ms 500:  [default=250] Ensures that speech segments are at least 500ms long before considering a split.
        rem --vad_min_silence_duration_ms 300: [default=100] Splits subtitles at smaller pauses (300ms).
        rem --vad_speech_pad_ms 200:           [default= 30] Ensures a 200ms buffer around detected speech to avoid clipping.
        rem 9v6:  changing to use equals between some args
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True 
        rem Alas, completely disabling VAD filter results in major major major hallucinations during silence... Let’s try turning it on again, sigh.
        rem 10v2: gave "unrecognized arguments: --vad_filter_threshold=0.2" oops it should be vad_threshold not vad_filter_threshold plus we had accidentally left vad_filter=False
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.2   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v3:                                                                                                                                                                                                                                                                                                      
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.2   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v4:  lowering vad_threshold from 0.2 to 0.1 because of metal & punk with fast/hard vocals. May increase hallucations tho                                                                                                                                                                                 
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 11:  adding --best_of 5  and --vad_alt_method=pyannote_v3 & removed --ff_mdx_kim2 but this clearly gave worse lyrics, terrible ones, with Wet Leg – Girlfriend                                                                                                                                             
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                                   --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --vad_alt_method=pyannote_v3 
        rem 12:  going back to original --ff_mdx_kim2 vocal separation but keeping the best_of 5 ... Looks great?                                                                                                                                                                                                      
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --vad_alt_method=pyannote_v3 
        rem 12v2:  reordering                                                                                                                                                                                                                                                                                          
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5
        rem 13: adding --max_comma_cent 70                                                                                                                                                                                                                                                                             
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70
        rem 14: adding -hst 2 via Purview’s advice to stop the thing where one subtitle gets stuck on for a whollleeee solooooo — it is short for --hallucination_silence_threshold  ... But it absolutely 100% does not solve that problem and gives output that causes concern for discarded lyrics. Have added logging the whisper output [and not just prompt] to the logfile to help track this...
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70               -hst 2 
        rem 15: adding --max_gap 3.0 — Purfview said there is a --max_gap option -- default is 3.0 but i’m getting gaps way larger than that so I don’t think it’s being enforced so i’m going to explicitly add it                                                                                                     
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 3.0 -hst 2 
        rem 16b: adding --max_gap 3.0 — Purfview said there is a --max_gap option -- default is 3.0 but i’m getting gaps way larger than that so I don’t think it’s being enforced so i’m going to explicitly add it                                                                                                    
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 3.0 
        rem 17: try shortening max_gap ———————— FINALLY VERY VERY GOOD RESULTS!!!! ————————                                                                                                                                                                                                                             
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 17b: dropping %PARAM_2% business ━━ 🌟 🌟 🌟 🌟 🌟 🌟 This prompt ran for 5,000+ songs!!!!!! 🌟 🌟 🌟 🌟 🌟 🌟                                                                                                                                                                                               
        set CLI_OPS=--model=large-v2           %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 18: But then we hit Gwar: Bloody Pit Of Horror Pt 2, that had very low-talking words, and WhisperAI could *NOT* get it right. It just couldn’t.  Not until the vad threshold was lowered...                                                                                                                     
        rem 18: 202501xx: lowering --vad_filter Threshold for the 1ˢᵗ time since v10
        set CLI_OPS=--model=large-v2           %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.05  --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 19v1: 20250219: raising --vad_filter Threshold back up to halfway between what we had for a long time, and what we recently lowered it to. There’s some wonkyness sometimes and we’re just not sure if it may be caused by this. Mostly going on gut feeling from observing it churn and churn and churn.
        set CLI_OPS=--model=large-v2           %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20                     --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=%VAD_THRESHOLD% --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 19v2: 20250601: changing language to be conditional on language set to “None” or not. Still considered Prompt Version 19 because it doesn’t actually change the prompt,j ust how it’s generated
        set CLI_OPS=--model=large-v2           %3$ %LANGUAGE_PART_OF_PROMPT% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width %SUBTITLE_OUTPUT_WITH% --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=%%VAD_THRESHOLD%% --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
                
        set PROMPT_VERSION=19              %+ rem used in log files

        rem proposed: Purfview said there is a --max_gap option -- default is 3.0 ... But i haven’t needed to use it

        rem --nullify_non_speech 
        rem     Avoiding Hallucinations: Sometimes, background noise or soft sounds may cause WhisperAI to “hallucinate” words. --nullify_non_speech helps eliminate this by focusing transcription on clearer speech.
        rem --vad_dump 
        rem     Enabling --vad_dump might reveal how changes to vad_window_size_samples affect VAD output and help approximate the default behavior based on responsiveness.                               
        rem --vad_alt_method 
        rem     Different music separation engines: [--vad_alt_method {silero_v3,silero_v4,pyannote_v3,pyannote_onnx_v3,auditok,webrtc}]
        rem --max_new_tokens
        rem     Purpose: This option limits the maximum number of tokens that WhisperAI generates per segment.
        rem     How it Works: WhisperAI’s model produces text in tokens (small chunks of words or sounds), and --max_new_tokens restricts the number of tokens generated for each detected segment. When the token limit is reached, transcription stops for that segment and moves on to the next.
        rem     When to Use It:
        rem     Control Segment Length: If you’re transcribing long audio files, especially ones with background noise, this option prevents overly long transcriptions for a single detected speech segment, helping keep segments manageable and aligned with the audio.
        rem     Reduce Noise-Induced Errors: In noisy environments, background sounds may stretch a transcription segment unnecessarily. --max_new_tokens allows you to limit the impact of background noise by truncating overly long sections.
        rem     Improve Processing Speed: Setting a lower max_new_tokens value can reduce the time spent on ambiguous or prolonged segments. This is useful if you’re prioritizing speed and only need shorter, precise snippets of audio transcribed.
        rem --vad_window_size_samples VAD_WINDOW_SIZE_SAMPLES
        rem     A typical starting point for vad_window_size_samples is 10 ms to 30 ms of audio data, which would correspond to sample counts based on the audio’s sampling rate (for example, 441 samples for 10 ms at a 44.1 kHz sample rate). You could try values within this range to see how they affect detection sensitivity and stability.
        rem --vad_threshold
        rem         Lower the VAD threshold to 0.35 or 0.3 to capture more detail. [I had to go to 0.1 for most songs in a punk/metal/industrial collection, settled on 0.075, but have gone to even 0.05 after that]
        rem --vad_filter_off
        rem         Disable VAD filtering with --vad_filter_off to ensure the whole audio is processed without aggressively skipping sections.
        rem --max_comma_cent 70
        rem         Roughly, break the subtitle at a comma... I think 70 is if it’s 70% through the line but i’m probably wrong
        rem NOTE: We also have --batch_recursive - {automatically sets --output_dir} but you can’t prompt each file with individual lyrics that way

        if "1" == "%DEBUG_TRACE_CSFF%"    pause "did we get here 1088"
        if "1" == "%AUTO_LYRIC_APPROVAL%" goto /i use_text
        if not exist %TXT_FILE% .or. "1" == "%SKIP_TXTFILE_PROMPTING%" .or. ("1" == "%SOLELY_BY_AI%" .and. "1" != "%AUTO_LYRIC_APPROVAL%") goto /i endiff_no_text_1017
                :use_text

                if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1904"
                rem the text file %TXT_FILE% does in fact exist!
                        rem 2023 method: set CLI_OPS=%CLI_OPS% --initial_prompt "Transcribe this audio, keeping in mind that I am providing you with an existing transcription, which may or may not have errors, as well as header and footer junk that is not in the audio you are transcribing. Lines that say “downloaded from” should definitely be ignored. So take this transcription lightly, but do consider it. The contents of the transcription will have each line separated by “ / ”.   Here it is: ``
                        rem set CLI_OPS=%CLI_OPS% --initial_prompt "Transcribe this audio, keeping in mind that I am providing you with an existing transcription, which may or may not have errors, as well as header and footer junk that is not in the audio you are transcribing. Lines th at say “downloaded from” should definitely be ignored. So take this transcription lightly, but do consider it. The contents of the transcription will have each line separated by “ / ”.   Here it is: ``
                        rem 2024: have learned prompt is limited to 224 tokens and should really just be a transcription
                        rem set WHISPER_PROMPT=--initial_prompt "
                        rem @Echo OFF
                        rem DO line IN @%TXT_FILE (
                        rem         set WHISPER_PROMPT=%WHISPER_PROMPT% %@REPLACE[%QUOTE%,',%line]
                        rem         REM @echo %faint%adding line to prompt: %italics%%line%%italics_off%%faint_off%
                        rem )

                rem Set our temp file using UNIQUEx instead of UNIQUE because UNIQUE uses the Windows API which bugs out at >100,000-file temp folders:
                        set tmppromptfile=%TEMP%\%_DATETIME.%KNOWN_NAME%.%_PID.%@NAME[%@UNIQUEx[%TEMP%\]]

                rem Smush the lyrics into a single line (no line breaks) set of unique lines ... unique-lines.pl is actually our lyric postprocessor
                        rem the oldest proof of concept:
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type  "%@UNQUOTE[%TXT_FILE]"   | uniq | paste.exe -sd " " -]]
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type  "%@UNQUOTE[%TXT_FILE]"   | awk "!seen[$0]++" | paste.exe -sd " " -]]
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type  "%@UNQUOTE[%TXT_FILE]"   | awk "!seen[$0]++" ]] .... This was getting unruly, wrote a perl script that like “uniq”, but more for this specific situation
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE["%TXT_FILE%"]" |:u8 unique-lines.pl -1 -L]] 
                                rem OUR_LYRICS_TRUNCATED=%@LEFT[%MAXIMUM_PROMPT_SIZE%,%OUR_LYRICS%]
                                rem OUR_LYRICS_2=%@LEFT[%MAXIMUM_PROMPT_SIZE%,%@EXECSTR[type "%@UNQUOTE["%TXT_FILE%"]" |:u8 lyric-postprocessor.pl -A -1 -L]]                               

                        rem The older way: piping the lyrics into the postprocessor: very problematic with special characters:
                                rem    rem Essentially make it so there is no command separator character. CHAR[1] should NOT come up in any lyrics
                                rem    rem The problem with *setdos /x-5 is it also disables piping so it made this into a multi-step process, but that’s okay.
                                rem    rem The problem with *setdos /x-1 is that it makes “*Echo” and commands prefixed with “*” invalid
                                rem    rem nevermind! *setdos /c%@CHAR[1] 
                                rem    rem But wait! This isn’t setting separator to  %@ASCII[1], but to “%”! oops!
                                rem    (type "%@UNQUOTE["%TXT_FILE%"]" |:u8 lyric-postprocessor.pl -A -1 -L) >%tmppromptfile%
                                rem    setdos /x0


                        rem Failed idea: Convert file to UTF-8 so that our perl postprocesser can open it properly... Excpet iconv itself fails which is a bummer, so we can’t do this
                                rem call set-tmp-file raw-lyrics-run-thru-iconv                             %+ rem \__Create output filename 
                                rem set  lyr_utf8=%tmpfile%.txt                                             %+ rem /  Create output filename 
                                rem iconv-perl-2009.exe -t UTF-8 "%@UNQUOTE["%TXT_FILE%"]"  >:u8%lyr_utf8%  %+ rem Convert to UTF-8
                                rem call errorlevel                                                         %+ rem Catch any errors
                                rem if not exist %lyr_utf8% call validate-environment-variable lyr_utf8     %+ rem Double-check that we did it
                                rem lyric-postprocessor.pl -A -1 -L "%@UNQUOTE["%lyr_utf8%"]" >:u8 %tmppromptfile%

                        rem The newer way: Letting the lyric postprocess open up the file directly to bypass limitations of command-line’s text piping:
                                lyric-postprocessor.pl -A -1 -L "%@UNQUOTE["%TXT_FILE%"]" >:u8 %tmppromptfile%
                                call errorlevel "You %italics_on%may%italics_off% need to %italics_on%manually%italics_off% re-save the file in %underline_on%UTF-8%underline_off% format" %+ rem The worst possible thing, and you really can’t overestimate how hard it is to prevent this from *EVER* happening, when dealing with world-sourced input files made by people with different editors in different countries with different languages and character sets and encodings and *waves hands* ... all ✨that✨


                if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1141"


                rem Safely ingest postprocessed lyrics into environment variable:
                        *setdos /x-25
                        rem 2025/06/07: Adding 6 to the setdos options to turn off redirection...
                        *setdos /x-256 
                        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1146"
                        set OUR_LYRICS_3a=%@EXECSTR[type %tmppromptfile%]
                        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1148"
                        set FINAL_LYRICS=%@unquote["%@LEFT[%MAXIMUM_PROMPT_SIZE%,"%our_lyrics_3a"]"]
                        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1150"
                        setdos /x0
                        rem echo our_lyrics_1=“%OUR_LYRICS_TRUNCATED%”
                        rem echo our_lyrics_2=“%our_lyrics_2%”
                        rem echo FINAL_LYRICS=“%FINAL_LYRICS%”
                        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1152"

                rem Add the lyrics to our existing whisper prompt:
                        *setdos /x-5
                        set WHISPER_PROMPT=--initial_prompt "%FINAL_LYRICS%"
                        setdos /x0
                        rem @echo %ANSI_COLOR_DEBUG%Whisper_prompt is:%newline%%tab%%tab%%faint_on%%WHISPER_PROMPT%%faint_off%%ANSI_COLOR_NORMAL%
                        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1159"

                rem Leave a hint to future-self, because we definitely do "env whisper" to look into the environment to find the whisper prompt last-used, for when we want to do minor tweaks... And remembering --batch_recursive is hard 😂
                        set WHISPER_PROMPT_ADVICE_NOTE_TO_SELF______________________________=*********** FOR RECURSIVE: do %%whisper_prompt%% but instead of the filename do --batch_recursive *.mp3

                rem Preface our whisper prompt with our hard-coded default command line options from above:
                        *setdos /x-5
                        set CLI_OPS=%CLI_OPS% %WHISPER_PROMPT%
                        setdos /x0
                        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1168"

                setdos /x0
        if "1" == "%DEBUG_TRACE_CSFF%" pause "we are here: 1168"
        :endiff_no_text_1017
        :No_Text
        rem if "1" == "%goto_end%" goto /i END
     if "1" == "%come_back_to_1386%" (unset /q come_back_to_1386 %+ goto /i come_back_to_1386)



rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////
REM        REM demucs vocals out (or not——we don’t do this in 2024):
REM                                        if "%SKIP_SEPARATION%" == "1" (goto /i Vocal_Separation_Skipped)
REM                                        if exist %VOC_FILE% (
REM                                            @call warning "Vocal file “%italics%%VOC_FILE%%italics_off%” %underline%already%underline_off% exists! Using it..."
REM                                            goto /i Vocal_Separation_Done
REM                                        )
REM                                    REM do it
REM                                        :Vocal_Separation
REM                                        @call unimportant "Checking[ff] to see if demuexe.exe music-vocal separator is in the path ... For me, this is in anaconda3\scripts as part of Python" %+ call validate-in-path demucs.exe
REM                                        REM mdx_extra model is way slower but in tneory slightly more accurate to use default, just set model= -- lack of parameter will use default Demucs 3 (Model B) may be best (9.92) which apparently mdx_extra is model b whereas mdx_extra_q is model b quantized faster but less accurate. but it’s fast enough already!
REM                                            set MODEL_OPT= %+  set MODEL_OPT=-n mdx_extra 
REM                                        REM actually demux the vocals out here
REM                                            %color_run% %+ demucs.exe --filename "%_CWD\%VOC_FILE%" %MODEL_OPT% --verbose --device cuda --float32 --clip-mode rescale   "%SONGFILE%" %+ @Echo OFF
REM                                            CALL errorlevel "Something went wrong with demucs.exe"
REM                                    REM validate if the vocal file was created, and remove demucs cruft           
REM                                        call validate-environment-variable VOC_FILE "demucs separation did not produce the expected file of “%VOC_FILE%”"
REM                                        :Vocal_Separation_Done
REM                                            set INPUT_FILE=%VOC_FILE% %+  SET EXPECTED_OUTPUT_FILE=%LRCFILE2% %+ if "%2" != "keep" .and. isdir separated (rd /s /q separated)
REM        :Vocal_Separation_Skipped
rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////



REM Use this tool to kill bad AI transcriptions / bad LRCget downloads — with the “3” option to pre-answer the first question for what mode type, type 3 = review and ask before deleting
        iff   "1" == "%FORCE_REGEN%" then
                call delete-bad-ai-transcriptions 3 force
        else
                iff "1" == "%DELETE_BAD_AI_TRANSCRIPTIONS_FIRST%" then
                        call delete-bad-ai-transcriptions 3 
                endiff
        endiff


REM does our input file exist?
        if not exist "%@UNQUOTE[%INPUT_FILE%]" call validate-environment-variable  INPUT_FILE

REM Assemble the full command-line to transcribe the file:
        *setdos /x-5
        set LAST_WHISPER_COMMAND=%TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%"    
        setdos /x0


REM Log the prompt we generated for analysis:
        echo. >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
        echo. >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
        echo. >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
        echo. >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
        echo %emoji_ear%%emoji_microphone% %_datetime ━━━━━━ %INPUT_FILE% ━━━━━━ PROMPT: %LAST_WHISPER_COMMAND%               >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
        echo. >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
        echo %newline%%newline%%emoji_ear%%emoji_microphone% %_datetime ━━━━━━ %INPUT_FILE% ━━━━━━ LYRICS: %FINAL_LYRICS%     >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"


REM If we are ONLY gathering prompts for analysis, abort now:
        if "1" != "%PROMPT_ANALYSIS_ONLY%" goto /i no_analysis_aborting        
                echo %ansi_color_warning_less%%star% Only gathering prompts right now, so we are done, actually.%ansi_color_normal%
                iff "" != "%LAST_WHISPER_COMMAND%" then
                        echo %ansi_color_less_important%%star% Prompt used would be: %faint_on%%LAST_WHISPER_COMMAND%%faint_off%%ansi_color_normal%
                endiff
                rem *pause>nul
                rem gosub divider                
                goto /i END
        :no_analysis_aborting



REM Backup any existing SRT file, and ask if we are sure we want to generate AI right now:
        :backup any existing one
        if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
        
        :actually_make_the_lrc
        gosub divider
        @echos %STAR% %ANSI_COLOR_WARNING_SOFT%%emphasis%%blink_on%About to%deemphasis%: %blink_off%
        *setdos /x-5
        set LAST_WHISPER_COMMAND_FOR_DISPLAY_TMP=%LAST_WHISPER_COMMAND%
        rem LAST_WHISPER_COMMAND_FOR_DISPLAY=%@ReReplace[initial_prompt ,initial_prompt%ansi_color_orange% ,"%LAST_WHISPER_COMMAND_FOR_DISPLAY_TMP%"]

        rem LAST_WHISPER_COMMAND_FOR_DISPLAY=%@ReReplace["(initial_prompt..)([^\\]*)","\1%ansi_color_orange%\2%ansi_color_bright_yellow%","%LAST_WHISPER_COMMAND_FOR_DISPLAY_TMP%"]
        set LAST_WHISPER_COMMAND_FOR_DISPLAY=%@ReReplace[(initial_prompt..)([^\\]*),\1%ansi_color_orange%\2%ansi_color_bright_yellow%,"%LAST_WHISPER_COMMAND_FOR_DISPLAY_TMP%"]

        set LAST_WHISPER_COMMAND_FOR_DISPLAY=%@ReReplace[^\%escape_character%q,,%last_whisper_command_for_display%]
        set LAST_WHISPER_COMMAND_FOR_DISPLAY=%@ReReplace[\%escape_character%q$,,%last_whisper_command_for_display%]
                rem ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Can do the matching of non-quote characters better 
        rem if you do it like this, but it requires the escape caharacter, which introduces potential incompatibility:
                rem *setdos /e!
                rem echo %@rereplace[[^\!q],x,"How is "your" quest going?"]
        @echo %LAST_WHISPER_COMMAND_FOR_DISPLAY%%ansi_color_reset% 
        setdos /x0
        unset /q answer
        gosub debug_show_lyric_status

        :determine_dynamic_prompt_options
                unset /q ADDITIONAL_OPTIONS_TEXT
                unset /q ADDITIONAL_OPTIONS_LETTERS
                unset /q ADDITIONAL_OPTIONS_MEANINGS
                                                                                                                        
                iff "%LYRICLESSNESS_STATUS%" != "APPROVED" then
                        set ADDITIONAL_OPTIONS_TEXT= [%ansi_color_bright_green%P%ansi_color_prompt%=Play,%ansi_color_bright_green%L%ansi_color_prompt%=mark lyricless%underline_on%ness%underline_off%,%ansi_color_bright_green%I%ansi_color_prompt%=Instr,%ansi_color_bright_green%K%ansi_color_prompt%=skip,%ansi_color_bright_green%G%ansi_color_prompt%=get lyrics,%ansi_color_bright_green%U%ansi_color_prompt%=mark as Untranscribeable/failed]
                        set ADDITIONAL_OPTIONS_LETTERS=EGIKLPSU
                        set ADDITIONAL_OPTIONS_MEANINGS=G:re-probe,L:Mark_as_lyricless!,Q:enQueue_in_winamp,P:play_the_file,I:mark_as_instrumental,U:mark_as_untranscribeable,S:mark_as_sound_effect,K:skip,E:edit_lyrics
                else
                        set ADDITIONAL_OPTIONS_TEXT= [%ansi_color_bright_green%P%ansi_color_prompt%=Play,%ansi_color_bright_green%I%ansi_color_prompt%=instr,%ansi_color_bright_green%K%ansi_color_prompt%=skip,%ansi_color_bright_green%G%ansi_color_prompt%=get lyrics,%ansi_color_bright_green%U%ansi_color_prompt%=mark as %ansi_color_bright_green%U%ansi_color_prompt%ntranscribeable/failed,%ansi_color_bright_green%E%ansi_color_prompt%dit lyr]
                        set ADDITIONAL_OPTIONS_LETTERS=EGIKPSU
                        set ADDITIONAL_OPTIONS_MEANINGS=G:re-probe,Q:enQueue_in_winamp,P:preview_the_file,I:mark_as_instrumental,U:mark_as_untranscribeable,S:mark_as_sound_effect,K:skip
                endiff
        :determine_dynamic_prompt_options_end


rem Ask if we should proceed:
        if "%LYRIC_STATUS%" == "APPROVED" .and. "1" != "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" set PROCEED_WITH_AI_CONSIDERATION_TIME=9
        :proceed_prompt
        unset /q answer
        @call AskYn "Do the transcription%ADDITIONAL_OPTIONS_TEXT%" yes %PROCEED_WITH_AI_CONSIDERATION_TIME% %ADDITIONAL_OPTIONS_LETTERS% %ADDITIONAL_OPTIONS_MEANINGS%
                set STORED_ANSWER=%ANSWER%                                                                                     %+ rem echo stored_answer is “%stored_answer” %+ pause %+ echo 0n
                rem “E”:
                        iff "%STORED_ANSWER%" == "E" then
                                if not exist "%TXT_FILE%" call warning "%italics_on%TXT_FILE%italics_off% of “%faint_on%%TXT_FILE%%faint_off%” does not exist!"
                                if     exist "%TXT_FILE%" %EDITOR% "%TXT_FILE%"
                                goto /i :go_here_after_last_minute_lyric_edit
                        endiff
                rem “K”:
                        if  "%STORED_ANSWER%" == "K" goto /i END
                rem “G”:
                        gosub check_for_answer_of_G "%INPUT_FILE%"
                        if  "%STORED_ANSWER%" == "G" goto /i initial_probing
                rem “I”:
                        iff "%STORED_ANSWER%" == "I" then
                                gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                                @call warning "Aborting because you marked it as an instrumental..."
                                gosub divider
                                goto /i END
                        endiff
                        unset /q answer
                rem “K”:
                        iff "%STORED_ANSWER%" == "K" then
                                @call warning "Skipping..."
                                gosub divider
                                goto /i END
                        endiff
                        unset /q answer
                rem “L”:
                        iff "%STORED_ANSWER%" == "L" then 
                                set answer=%STORED_ANSWER%
                                gosub check_for_answer_of_L "%INPUT_FILE%" no_end
                                goto /i regen_ai_prompt
                        endiff                
                rem “Y”/“N”:
                        rem "%STORED_ANSWER%" == "Y" goto /i  edit_ai_prompt
                        if  "%STORED_ANSWER%" == "Y" echo just continue on! >nul
                        iff "%STORED_ANSWER%" == "N" then
                                @call warning "Aborting because you changed your mind..."
                                rem sleep 1
                                gosub divider
                                goto /i END
                        endiff
                rem “P”/“Q”/“S”: 1274
                        unset /q answer
                        set answer=%STORED_ANSWER%
                        if  "%STORED_ANSWER%" == "P" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%INPUT_FILE%"
                        if  "%STORED_ANSWER%" == "Q" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_Q "%INPUT_FILE%"
                        if  "%STORED_ANSWER%" == "S" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_S "%INPUT_FILE%"
                        if  "%STORED_ANSWER%" == "P" .or. "%STORED_ANSWER%" == "Q" .or. "%STORED_ANSWER%" == "S" goto /i  proceed_prompt
                rem “U”: 1305
                        unset /q answer
                        set answer=%STORED_ANSWER%
                        if  "%STORED_ANSWER%" == "U" (gosub mark_as_untranscribeable "%INPUT_FILE%" %+ goto /i END_OF_GET_LYRICS)


REM quick chance to edit prompt:
        :edit_ai_prompt
        unset /q ANSWER
        @call AskYn "Edit the AI prompt first" no %PROMPT_EDIT_CONSIDERATION_TIME%
        rem “Y” answer:
                iff "%answer%" == "Y" then
                        rem Get new VAD threshold:
                                gosub            VAD_threshold_advice
                                call  eset-alias VAD_threshold        quick

                        rem Regenerate our prompt:
                                rem OLD: 
                                rem NEW:
                                set come_back_to_1386=1
                                goto /i reassemble_prompt
                                :come_back_to_1386
                                call  eset-alias LAST_WHISPER_COMMAND quick
                endiff


REM Updated Concurrency Check: wait on lock file
        on break cancel
        :concurrency_checks
        :lockfile_again
        unset /q lockfile_pid
        if %DEBUG_LOCKFILE% gt 0 echo  🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐TOP OF CONCURRENCY CHECKS!!!!🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐
        gosub lockfile_wait_on_transcriber_lock_file 
        gosub lockfile_read_lockfile_values
        set   lockfile_retval=%_
        if %DEBUG_LOCKFILE% gt 0 echo  🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐 Returned from lockfile_wait_on_transcriber_lock_file!!! lockfile_pid=“%lockfile_pid%” lockfile_filename=“%lockfile_filename” 🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐🐐
        rem if isfile "%TRANSCRIBER_LOCK_FILE%" goto :passed_concurrency_check
        rem echo  lockfile_retval is “%lockfile_retval%”
        iff "666" == "%lockfile_retval%" then
                echos {{delaying .3-6.66 seconds}} 
                delay /m %@RANDOM[30,666] 
                goto /i lockfile_again
        endiff
        iff "%lockfile_pid%" != "%_pid" then
                iff "1" == "%LOCKFILE_NOT_FOR_THIS_PROCESS_MENTIONED%" then
                        echos %NO% %@randfg_soft[]Lockfile is not for this process...%@ANSI_MOVE_TO_COL[0]
                        set LOCKFILE_NOT_FOR_THIS_PROCESS_MENTIONED=1
                        sleep 1
                else
                        gosub clear_rows_for_lockfile_messages %LOCKFILE_MESSAGE_ROWS_TO_CLEAR%                             %+ rem equivalent to: repeat 8 echo. %+ echo %@ANSI_MOVE_TO_ROW[%@EVAL[%_ROWS-9]]
                        iff exist %TRANSCRIBER_LOCK_FILE% then
                                set lockfile_initially_detected=1
                                call warning_soft "Lockfile detected..."
                                type %TRANSCRIBER_LOCK_FILE%
                                set my_question=Delete the lockfile
                                set my_wait_time=45
                                unset /q ANSWER
                        endiff
                        iff not exist %TRANSCRIBER_LOCK_FILE% then
                                if "1" == "%lockfile_initially_detected%" call warning_soft "But now it’s gone, so something must have %italics_on%just%italics_off% finished..."
                        else
                                call AskYN "%my_question" no %my_wait_time%
                                if "Y" == "%ANSWER%" gosub lockfile_delete_transcriber_lock_file
                        endiff
                        unset /q lockfile_initially_detected                                            %+ rem this flag only briefly used
                endiff
        endiff
        if %DEBUG_LOCKFILE% gt 0 echos [DBLF:we got through the first check]




REM Original Concurrency Check: Check if the encoder is already running in the process list. Don’t run more than 1 at once.
        rem slower call isRunning %TRANSCRIBER_PRNAME% silent
        rem slower if "%isRunning" != "1" (goto /i no_concurrency_issues)
        rem faster:
        rem echo %ANSI_COLOR_DEBUG%- DEBUG: (4) iff @PID[TRANSCRIBER_PDNAME=%TRANSCRIBER_PDNAME%] "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then %ANSI_COLOR_NORMAL%
        set CONCURRENCY_WAS_TRIGGERED=0       
        echos %@ansi_move_to_col[0]%ansi_save_position% 
        iff "%@PID[%TRANSCRIBER_PDNAME%]" == "0" then
                goto /i no_concurrency_issues
        else 
                if %DEBUG_LOCKFILE% gt 1 echos [🐐Transcriber is running?!?!?!]
        endiff

                if "1" == "%been_here_1339%" echos %ANSI_MOVE_UP_2%``

                rem save and restore our position:
                        iff not defined WAITING_FOR_COMPL_ROW then
                                SET WAITING_FOR_COMPL_ROW=%_row
                        else
                                echos %@ANSI_MOVE_TO_ROW[%@EVAL[%WAITING_FOR_COMPL_ROW%-1]]
                        endiff
                        iff not defined WAITING_FOR_COMPL_COL then
                                SET WAITING_FOR_COMPL_COL=%_column
                        else
                                echos %@ANSI_MOVE_TO_COL[%WAITING_FOR_COMPL_COL%]
                        endiff
                        set DEBUG_TEXT=[r/c=%WAITING_FOR_COMPL_ROW%/%WAITING_FOR_COMPL_COL%]{rs/cs=%_rows/%_columns}

                @echo %ansi_color_warning_soft%%star% %italics_on%%TRANSCRIBER_PDNAME%%italics_off% is %@colorful[already] running%ansi_color_normal%
                @echo %ANSI_COLOR_WARNING_SOFT%%STAR% Waiting for completion of %italics_on%another%italics_on% instance of %italics_on%%@cool[%TRANSCRIBER_PDNAME%]%italics_off% %ansi_color_warning_soft%to finish before starting this one... %DEBUG_TEXT%%ANSI_COLOR_NORMAL%%@ANSI_MOVE_TO_COL[0]                
                set been_here_1339=1
                rem delay 1
                set CONCURRENCY_WAS_TRIGGERED=1
                unset /q ANSWER
                call AskYN "Continue anyway%ansi_erase_to_end_of_line%" no 2
                iff "Y" == "%ANSWER%" then
                        if %DEBUG_LOCKFILE% gt echo 🐐 goto /i :no_concurrency_issues no wait actually :actually_do_it
                        goto /i :actually_do_it
                endiff
                goto /i :concurrency_checks

                :Check_If_Transcriber_Is_Running_Again
                        rem Echo a random-colored dot:
                                @echos %@randfg_soft[].

                        rem Wait a random number of seconds to lower the odds of multiple waiting processes seeing an opening and all starting at the same time]:
                                rem call sleep.bat %@random[7,29]        
                                set HOW_MANY=%@random[7,29]        
                                set LEFT=%HOW_MANY%
                                do i = 1 to %how_many%
                                        title %emoji_stopwatch% %left% more seconds...
                                        set left=%@EVAL[%left% - 1]
                                        echos %@randcursor[]
                                        *delay 1
                                enddo
                                delay /m %@RANDOM[0,1000]
                                title $0

                        rem Check to see if we waited long enough for the other transcriber instance to no longer be running:
                                rem "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i concurrency_checks
                                rem "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i Check_If_Transcriber_Is_Running_Again
                                if  "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i concurrency_checks

                        rem When finally done, echo a green “...”:
                                @echo %ansi_color_green%...%ansi_color_bright_green%Done%blink_on%!%blink_off%%ansi_reset%
        :no_concurrency_issues
        if %DEBUG_LOCKFILE% gt echo 🐐 at :no_concurrency_issues "@PID[%%TRANSCRIBER_PDNAME%%]" == “%@PID[%TRANSCRIBER_PDNAME%]”


REM ════════════════════════════════════════════════════════════════════════════════════ WE’RE DOING IT NOW!!! ════════════════════════════════════════════════════════════════════════════════════ 
        



REM  ✨ ✨ Get ready to actually generate the SRT file [used to be LRC but we have now coded specifically to SRT] —— start AI: ✨ ✨ 
REM  ✨ ✨ ✨ Concurrency checks: ✨ ✨ ✨ 
        rem One last concurrency check:
                iff "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then
                        echo %ANSI_COLOR_WARNING% Actually, it’s still running! %ANSI_RESET%
                        call status-bar unlock
                        rem  /i Check_If_Transcriber_Is_Running_Again
                        goto /i concurrency_checks
                else
                        rem One last extra random wait in case 2 different ones get here at the same time. 
                        rem (And only do this if we already had to wait before):
                        rem if "%CONCURRENCY_WAS_TRIGGERED%" == "1" delay /m %@random[7000,29000]                    
                            if "%CONCURRENCY_WAS_TRIGGERED%" == "1" delay /m %@random[70,290]                    
                endiff

rem Determine log file name:
        set OUR_LOGFILE=%@NAME[%@UNQUOTE[%INPUT_FILE]].log

rem A 3rd concurrency check became necessary in my endeavors:
        rem   /m %@RANDOM[2000,12000]
        delay /m %@RANDOM[20,120]
        rem "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i Check_If_Transcriber_Is_Running_Again %+ rem yes, a 3rd concurrency check at the very-very last second!
        if  "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i concurrency_checks                    %+ rem yes, a 3rd concurrency check at the very-very last second!



REM  ✨ ✨ ✨ Concurrency check 1435: ✨ ✨ ✨ 
        echo LOCKFILE_ALREADY_EXISTS==“%LOCKFILE_ALREADY_EXISTS%”>nul                          %+ rem debugging for when we have echo 0n
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i concurrency_checks
        delay /m %@RANDOM[100,1000]
        rem if "1" == "%LOCKFILE_ALREADY_EXISTS%" goto /i concurrency_checks
        iff "1" == "%LOCKFILE_ALREADY_EXISTS%" then
                if not isfile "%TRANSCRIBER_LOCK_FILE%" (
                        set LOCKFILE_ALREADY_EXISTS=0
                ) else (
                        goto /i concurrency_checks
                )
        endiff


rem 4ᵗʰ concurrency is a new level of preposterousness in this maddening concurrency situation:
rem echo f "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i Check_If_Transcriber_Is_Running_Again  [4ᵗʰ concurrency check] 🐐
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i concurrency_checks



REM set a status bar to keep us from getting confused about which file / what we’re doing / etc
        rem call top-message Transcribing %FILE_TITLE% by %FILE_ARTIST%
        set LOCKED_MESSAGE_COLOR_BG=%@ANSI_BG[0,0,64]                               %+ rem copied from top-banner/status-bar.bat
        iff not defined FILE_ARTIST .and. "1" != "%SOLELY_BY_AI%" .and. "APPROVED" != "%LYRIC_STATUS%" then
            call warning_soft "%italics_on%FILE_ARTIST%italics_on% is not defined here and %italics_on%generally%italics_off% should be, particularly because %underline_on%SOLELY_BY_AI%underline_off%=“%SOLELY_BY_AI%” [lyric_status=“%lyric_status%”]"
            set FILE_ARTIST= ``
            rem It turns out that it’s okay most of the time, so better not get 
            rem                all hung up about it with a mandatory interacton:
            if "1" == "%INSIST_ON_HAVING_ARTIST%" call eset-alias FILE_ARTIST quick
        endiff                                                    
        rem echo %ansi_color_debug%- DEBUG: FILE_TITLE is “%FILE_TITLE%” / FILE_ARTIST is “%FILE_ARTIST%” / INPUT_FILE is “%INPUT_FILE%”%ansi_color_normal% 
        rem >nul
        if "%FILE_ARTIST%" ==  " " unset /q FILE_ARTIST
        unset /q banner_song
                iff        "" != "%FILE_TITLE%" .or. "" != "%FILE_ARTIST%" then
                        if "" != "%FILE_TITLE%"  set banner_song= %faint_off%“%italics_on%%FILE_TITLE%%italics_off%”
                        if "" != "%FILE_ARTIST%" set banner_song=%banner_song% by %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%blink_on%%@cool[%FILE_ARTIST%]%blink_off%
                else
                         set banner_song= “%@NAME["%INPUT_FILE%"]”
                endiff

        rem call debug "Banner_song is “%banner_song%” "

        unset /q banner_message
        rem set  banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%ZZZZZZZZ%AI-Transcribing%faint_off% %ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%“%italics_on%%FILE_TITLE%%italics_off%” %faint_on%%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%by%faint_off% %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%ZZZZZZZZ%%@cool[%FILE_ARTIST%]%%ZZZZZZZZZ%
        rem set  banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%faint_on%%ansi_color_normal%%@ANSI_BG[0,0,64]AI–Transcribing%faint_off%%ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%%@IF["" != "%FILE_TITLE%" .and. "" != "%FILE_ARTIST%", %@NAME["%INPUT_FILE%"],]%@IF["" != "%FILE_TITLE%", “%italics_on%%FILE_TITLE%%italics_off%”,]%LOCKED_MESSAGE_COLOR_BG%%@IF["" != "%FILE_ARTIST%", %@randfg_soft[]%faint_on%by%faint_off% %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%blink_on%%@cool[%FILE_ARTIST%]%%blink_off%,]
        set      banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%faint_on%%ansi_color_normal%%@ANSI_BG[0,0,64]AI–Transcribing%faint_off%%ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%%banner_song%

rem Cosmetics:
        if defined CURSOR_RESET echos %CURSOR_RESET%
        echos %ANSI_CURSOR_CHANGE_TO_vertical_bar_steady%   


rem Check lockfile once again at the end:
        gosub lockfile_create_transcriber_lock_file 
        if "%_" == "666" goto /i concurrency_checks

rem We have to then READ the lockfile for it’s process 
        gosub lockfile_read_lockfile_values
        if "1" == "%DEBUG_LOCKFILE%" call debug "lockfile_pid is “%lockfile_pid%”"
        iff "%lockfile_pid%" != "%_PID%" then
                call less_important "This is another process’s lockfile"
                goto /i concurrency_checks
        else
                if "1" == "%DEBUG_LOCKFILE%" call less_important "This is our lockfile"
        endiff


REM Turn on the status bar we created earlier:
        rem echo about to call status-bar "%banner_message%" ... %+ pause
        call status-bar "%banner_message%"
        gosub divider


REM  ✨ ✨ ✨ ✨ ✨ ✨ ACTUALLY DO THE AI-TRANSCRIPTION: ✨ ✨ ✨ ✨ ✨ ✨ 
        rem PRETTY HEADER FOR AI-TRANSCRIPTION:
                rem Cosmetics:
                        @if "1" == "%LAUNCHING_AI_DISPLAYED%" goto :launching_ai_already_displayed
                        @echo.
                        @call bigecho %ANSI_COLOR_BRIGHT_RED%%EMOJI_FIREWORKS% Preparing to launch AI! %EMOJI_FIREWORKS%%ansi_color_normal%
                        set LAUNCHING_AI_DISPLAYED=1
                        echo.
                        echo %faint_on%%star2% Now = %[_ISODATE] %[_TIME]%faint_off%
                        echo %faint_on%%star2% Dir = %italics_on%%[_CWD]%italics_on%

                        rem 2025/06/09: now that deadlock detection is more thorough, we can skip this delay: delay /m %@RANDOM[1000,3000] 
                        rem that firework emoji was so much cooler in emoji11/win10 than emoji13/win11
                        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[magenta]%ANSI_CURSOR_CHANGE_TO_vertical_bar_BLINKING%   
                        title waiting: %BASE_TITLE_TEXT%
                        :launching_ai_already_displayed

rem Prepare to actually do it!
                echo. %+ rem this is the blank line after “launching ai”
                option //UnicodeOutput=yes
                on break rem
                rem    %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper 
                rem    %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper  |&:u8 tee      /a      "%OUR_LOGFILE%"
                rem    %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper  |&:u8 tee.exe --append "%OUR_LOGFILE%"
                rem    %LAST_WHISPER_COMMAND% |&:u8  grep -v ctranslate  |:u8 copy-move-post whisper   |:u8 tee.exe --append "%OUR_LOGFILE%"
                rem   (%LAST_WHISPER_COMMAND% |&|:u8 grep -v ctranslate) |:u8 copy-move-post whisper   |:u8 tee.exe --append "%OUR_LOGFILE%"
                rem  ((%LAST_WHISPER_COMMAND% |&|:u8 grep -v ctranslate) |:u8 copy-move-post whisper)  |:u8 tee.exe --append "%OUR_LOGFILE%"
                rem  ((%LAST_WHISPER_COMMAND%                          ) |:u8 copy-move-post whisper   |:u8 tee.exe --append "%OUR_LOGFILE%")
                rem  ((%LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper) |&:u8 tee.exe --append "%OUR_LOGFILE%")
                rem   (%LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper  |&:u8 tee.exe --append "%OUR_LOGFILE%")
                rem    %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper                                          %+ rem works great....but no log
                rem    %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper   |:u8 tee.exe --append "%OUR_LOGFILE%"  %+ rem does NOT fully work. cycling yes but no italicized cycling lyrics just the whole thing
rem temporary cosmetic feature removal while working out copy-move-post.py post-TCCv33 modifications is to remove the postprocessor:
rem                    %LAST_WHISPER_COMMAND%                                                          |:u8 tee.exe --append "%OUR_LOGFILE%"  %+ rem does NOT fully work. cycling yes but no italicized cycling lyrics just the whole thing
rem but y’know rather than using tee, i could maybe use copy-move-post ITSELF to write the  logfile and escape these complications entirely!                       


rem 5ᵗʰ++++ concurrency is a new level of preposterousness in this maddening concurrency situation:
        delay /m %@RANDOM[222,5938]
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" (delay /m %@RANDOM[1000,10000] %+ goto /i concurrency_checks)
        delay /m %@RANDOM[333,8327]
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" (delay /m %@RANDOM[1000,10000] %+ goto /i concurrency_checks)
        delay /m %@RANDOM[123,4567]
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" (delay /m %@RANDOM[1000,10000] %+ goto /i concurrency_checks)
        delay /m %@RANDOM[873,3567]
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" (delay /m %@RANDOM[1000,10000] %+ goto /i concurrency_checks)
        delay /m %@RANDOM[113,2763]
        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" (delay /m %@RANDOM[1000,10000] %+ goto /i concurrency_checks)

rem Title the window:
                :actually_do_it
                title %EMOJI_EAR%%BASE_TITLE_TEXT%


rem ACTUALLY DO IT!!!:
                       %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper -t"%OUR_LOGFILE%"  

rem Title the window that we are done!:
                title %CHECK% WhisperAI complete!

rem Varoius cleanup:
                unset /q WAITING_ON_LOCKFILE_ROW WAITING_ON_LOCKFILE_COL %+ rem These need to be unset so that they are properly set next time we wait for a lockfile
                on break cancel                      %+ rem Re-Enable proper Ctrl-Break behavior under TCC+WindowsTerminal                       
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                :Done_Transcribing                   %+ rem  /     If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                option //UnicodeOutput=%UnicodeOutputDefault%
                if defined TOCK         echos %TOCK%           %+ rem just our nickname for an extra-special ansi-reset
                if defined CURSOR_RESET echos %CURSOR_RESET%   %+ rem fix cursor the most
                gosub lockfile_delete_transcriber_lock_file
                call errorlevel "some sort of problem with the AI generation occurred in create-srt-from-file line 744ish"
                unset /q LAUNCHING_AI_DISPLAYED

        rem Cosmetics:
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%                
                call unlock-bot                    %+ rem Disable our status bar
                title Done: %BASE_TITLE_TEXT%      %+ rem Update the window title

REM  ✨ ✨ ✨ ✨ ✨ ✨ LOG WHAT WE’VE DONE: ✨ ✨ ✨ ✨ ✨ ✨         [and window title too]
                iff  "%LOG_PROMPTS_USED%" == "1" then
                        @echo %@REPEAT[%newline%,4]%EMOJI_EAR% %_DATETIME: prompt v%PROMPT_VERSION%: %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%" >>:u8"%OUR_LOGFILE%"
                        @echo %@REPEAT[%newline%,0]%EMOJI_EAR% %_DATETIME: prompt v%PROMPT_VERSION%: %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%" >>:u8"%AUDIOFILE_TRANSCRIPTION_LOG_FILE%"
                        @echo %@REPEAT[%newline%,1]%EMOJI_EAR% %_DATETIME: filename:  %INPUT_FILE%                                                     >>:u8"%AUDIOFILE_TRANSCRIPTION_LOG_FILE%"
                endiff

REM delete zero-byte LRC files that can be created
        rem echo "About to delete zero byte files " %+ pause
        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[orange]%ANSI_CURSOR_CHANGE_TO_BLOCK_steady%                
        call delete-zero-byte-files *.lrc;*.srt silent >nul
        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%                



REM did we create the SRT file? If not, ask about the instrumental situation
        rem echo "About to check if we created the expected output file of “%EXPECTED_OUTPUT_FILE%” file " %+ pause
        rem echo if not exist "%EXPECTED_OUTPUT_FILE%" then 
        iff not exist "%@UNQUOTE[%EXPECTED_OUTPUT_FILE%]" then 
                beep
                call warning "Possible instrumental detected" big
                echo %ansi_color_warning%%emoji_warning% expected output file of “%italics%%EXPECTED_OUTPUT_FILE%%italics_off%” does not exist %emoji_warning%%ansi_color_normal%
                call    pause-for-x-seconds 3
                gosub   ask_about_instrumental
                iff "%ANSWER%" == "Y" then 
                        call warning "Aborting because marked as instrumental"
                        goto /i END
                endiff
                goto /i did_not_generate
        endiff
        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[bright green]%ANSI_CURSOR_CHANGE_TO_BLOCK_steady%                



        


REM Post-process the SRT/LRC file(s): 
        gosub postprocess_lrc_srt_files
        



REM did we create the SRT file? If so, then keep track of how many, and if no TXT file exists, create one from the SRT file:
        iff exist "%@UNQUOTE[%EXPECTED_OUTPUT_FILE%]" then
                rem Ensure the folder is marked as having AI-generated transcriptions:
                        rem We don’t need this anymore because our files have ADS tags and comments stating their origin
                                rem if not exist "__ contains AI-generated SRT files __" @echo %EXPECTED_OUTPUT_FILE%%::::%_DATETIME%::::%TRANSCRIBER_TO_USE% >>:u8"__ contains AI-generated SRT files __"

                rem Keep track of how many we’ve done in this session:
                        if "" == "%NUM_TRANSCRIBED_THIS_SESSION%" set NUM_TRANSCRIBED_THIS_SESSION=0
                        set NUM_TRANSCRIBED_THIS_SESSION=%@EVAL[%NUM_TRANSCRIBED_THIS_SESSION% + 1]
                        if %NUM_TRANSCRIBED_THIS_SESSION% gt 1 echo %ANSI_COLOR_IMPORTANT%%check1% %blink_on%Transcribed this session: %italics_on%%@cool[%NUM_TRANSCRIBED_THIS_SESSION%]%blink_off%%italics_off%%ANSI_COLOR_NORMAL%


                rem Create TXT file from freshly-generated lyrics, if none currently exists:
                        if exist "%TXT_FILE%" goto /i :text_file_exists 
                                echo %ansi_color_warning_soft%%star2% No .TXT lyrics exist, so converting SRT transcription to TXT...%ansi_color_normal%
                                call srt2txt "%EXPECTED_OUTPUT_FILE%" "%TXT_FILE%"
                                set JUST_CONVERTED_SRT_TO_TEXT=1
                        :text_file_exists 
        endiff
        title %CHECK%%BASE_TITLE_TEXT%


rem If we did, we need to rename any sidecar TXT file that might be there {from already-having-existed}, becuase 
rem MiniLyrics will default to displaying TXT over SRC
        rem NO NOT ANYMORE if exist "%TXT_FILE%" (ren /q "%TXT_FILE%" "%TXT_FILE.bak.%_datetime" )


rem ///////////////////////////////////////////// OLD DEPRECATED CODE /////////////////////////////////////////////
iff "1" == "%USE_2023_LOGIC%" then
                        REM rename the file & delete the vocal-split wav file
                            iff "%EXPECTED_OUTPUT_FILE%" != "%LRC_FILE%" then
                                set MOVE_DECORATOR=%ANSI_GREEN%%FAINT%%ITALICS% 
                                mv "%EXPECTED_OUTPUT_FILE%" "%LRC_FILE%"
                            endiff
                            if not exist "%LRC_FILE%" call validate-environment-variable LRC_FILE "LRC file not found around line 1501ish"
                            if exist "%LRC_FILE%" .and. "%2" != "keep" (*del /Ns /q /r "%VOC_FILE%")
endiff
rem ///////////////////////////////////////////// OLD DEPRECATED CODE /////////////////////////////////////////////


:did_not_generate
rem echo About to go to cleanup but maybe should be going to cleanup_only
goto /i prompt_about_marking_karaoke_as_untranscribable


rem /////////////////////////////////////////////////////////////////////////////////////////////////////////////////// SUBROUTINES:

        :say_if_exists [it]
                if not defined %[it] (@call error "say_if_exists called but “%it%” is not defined")
                set filename=%[%[it]]
                iff exist %filename then
                        set BOOL_DOES=1 %+ set does_punctuation=: %+ set does=%BOLD%%UNDERLINE%%italics%does%italics_off%%UNDERLINE_OFF%%BOLD_OFF%    ``
                else
                        set BOOL_DOES=0 %+ set does_punctuation=: %+ set does=does %FAINT%%ITALICS%%blink%not%blink_off%%ITALICS_OFF%%FAINT_OFF%
                endiff
                %COLOR_IMPORTANT_LESS%
                        if "%BOOL_DOES%" == "0" (set DECORATOR_ON=  %strikethrough% %+ set DECORATOR_OFF=%strikethrough_off%)
                        if "%BOOL_DOES%" == "1" (set DECORATOR_ON=%PARTY_POPPER%%faint_off%    %+ set DECORATOR_OFF=%PARTY_POPPER%     )
                        @echos * %@FORMAT[11,%it%] %does% exist%does_punctuation% %FAINT%%decorator_on% %filename% %decorator_off%%FAINT_OFF%
                %COLOR_NORMAL%
                @echo.
        return



        :divider_v001_pre_fork []
                rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                set wd=%@EVAL[%_columns - 1]
                set nm=%bat%\dividers\rainbow-%wd%.txt
                iff exist %nm% then
                        *type %nm%
                        if "%1" != "NoNewline" .and. "%2" != "NoNewline" .and. "%3" != "NoNewline" .and. "%4" != "NoNewline" .and. "%5" != "NoNewline"  .and. "%6" != "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                else
                        echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                endiff
        return

        :divider_v002_when_it_lived_in_other_file [opt]
                gosub "%BAT%\get-lyrics-for-file.btm" divider %opt%
        return

        :divider_v003_now_lives_here_AND_in_create_lyrics_so_neither_encroach_upon_maximum_nesting_limit
        :divider [divider_param]
                iff "1" == "%suppress_next_divider%" then
                        set  suppress_next_divider=0
                        return
                endiff

                rem Determine divider file to use:
                        set wd=%@EVAL[%_columns - 1]
                        set nm=%bat%\dividers\rainbow-%wd%.txt

                rem Type divider file if it exists:
                        iff exist %nm% then
                                *type %nm%
                                set last_divider_method=type
                                set last_divider_param=%divider_param%
                rem Otherwise, manually draw the divider:
                        else
                                echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                                set last_divider_method=echo
                        endiff

                rem Our divider files do not include newlines. Do we add one ourself?
                        rem debug: *pause>nul
                        iff "%divider_param%" == "NoNewline"  then
                                set last_divider_newline=False
                        else 
                                set last_divider_newline=True

                                rem Go to the next line:           
                                        rem echos %NEWLINE%
                                        echo.

                                rem Then move to column 0/1 [which are the same column]:
                                        echos %@ANSI_MOVE_TO_COL[0] 

                        endiff

                rem Debug:
                        echo wtf last_divider_newline=%last_divider_newline% should we do one? >nul
        return

rem ////////////////////////////////////////////////////////////////////////////////////////////////////////////////


:Finishing_Up
:Cleanup
:prompt_about_marking_karaoke_as_untranscribable
rem :Cleanup old label was here

rem Let user know if we were NOT succesful, then skip to the end:
        iff not exist "%SRT_FILE%" then
                if "1" == "%UNFORTUNATELY_WE_COULD_NOT_CREATE_SAID%" goto /i END
                gosub divider
                @call warning "Unfortunately, we could not create the karaoke file %emphasis%%SRT_FILE%%deemphasis%"
                set UNFORTUNATELY_WE_COULD_NOT_CREATE_SAID=1
                title %emoji_warning% Karaoke not generated! %emoji_warning% 
                :ask_about_instrumental_1500
                        gosub ask_about_instrumental
                        if "1" == "%JUST_RENAMED_TO_INSTRUMENTAL%" goto /i END
                :ask_about_failed
                        gosub divider
                        unset /q ANSWER
                        call AskYN "Mark karaoke as failed so we don’t try again [%ansi_color_bright_green%N%ansi_color_prompt%=No, mark instrumental instead,%ansi_color_bright_green%P%ansi_color_prompt%=Play it]" no %KARAOKE_APPROVAL_WAIT_TIME% IPQS I:no_instead_mark_mark_instrumental,Q:enQueue_in_winamp,P:play,S:no_instead_mark_mark_as_sound_effect
                                gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                                gosub check_for_answer_of_P "%@UNQUOTE["%INPUT_FILE%"]"
                                gosub check_for_answer_of_Q "%@UNQUOTE["%INPUT_FILE%"]"
                                gosub check_for_answer_of_S "%@UNQUOTE["%INPUT_FILE%"]"
                                if  "P" == "%ANSWER%" .or. "Q" == "%ANSWER%" .or. "S" == "%ANSWER%" goto /i ask_about_instrumental_1500
                                iff "Y" == "%ANSWER%" .or. "I" == "%ANSWER%" then
                                      echo Tru`>%@`UNQUOTE["%INPUT_FILE%"]:karaoke_failed" 🐐🐐🐐🐐🐐🐐🐐>nul
                                      echo True>"%@UNQUOTE["%INPUT_FILE%"]:karaoke_failed"
                                endiff
                        goto /i nothing_generated
        endiff


rem Cleanup:
        rem MiniLyrics will pick up a TXT file in the %lyrics% repo *instead* of a SRT file in the local folder
        rem   for sure: in the case of %lyrics%\<first letter of artist name?>\<same name as audio file>.txt  ——— MAYBE_LYRICS_2
        rem      maybe: in the case of %lyrics%\letter\artist - title.txt             ——— MAYBE_LYRICS_1
        rem So we must delete at least the first one, if it exists.  We use our get-lyrics script in SetVarsOnly mode:
        rem moved to beginning: call get-lyrics-for-file "%SONGFILE%" SetVarsOnly
        rem ...which sets MAYBE_LYRICS_1 and MAYBE_LYRICS_2
        rem echo %ansi_color_debug%- DEBUG: (7) Checking[gg] if exists: “%underline_on%%MAYBE_LYRICS_2%%underline_off%” for deprecation%ansi_color_normal%
        set MAYBE_SRT_2=%@PATH[%maybe_lyrics_2]%@NAME[%MAYBE_LYRICS_2].lrc

        iff exist "%MAYBE_LYRICS_2%" then
                rem call deprecate "%MAYBE_LYRICS_2%"
                set NEWNAME=%@NAME[%MAYBE_LYRICS_2%].txt
                iff exist "%NEWNAME%" then
                        call deprecate "%MAYBE_LYRICS_2%"
                        rem  deprecate changes the extension to ".dep"/".deprecated" and is just a way of almost-deleting files
                else
                        ren "%MAYBE_LYRICS_2%" "%NEWNAME%"
                endiff
        endiff
        



rem Preliminary success SRT-generation message:
        @gosub divider
        @call success "%blink_on%Karaoke created%blink_off% at: %blink_on%%italics_on%%emphasis%%SRT_FILE%%deemphasis%%ANSI_RESET%" 
        title %check% %BASE_TITLE_TEXT% generated successfully! %check% 
        if "%SOLELY_BY_AI%" == "1" (call warning_soft "%double_underline_on%%italics_on%ONLY%italics_off%%double_underline_off% AI was used. Lyrics were %underline_on%%italics_on%not%italics_off%%underline_off% used for transcription prompting." silent)



rem A chance to edit/reject the karaoke: 
        :display_karaoke_before_asking_to_edit_it 
                iff "%LYRICS_ACCEPTABLE%" != "0" .or. "%LYRICS_ACCEPTABLE%" == "" then 
                        iff not exist "%TXT_FILE%" .or. %@FILESIZE["%TXT_FILE%"] eq 0 then 
                                echo %ansi_color_warning_soft%%star% Lyrics were approved but can’t find “%italics_on%%TXT_FILE%%italics_on%”%ansi_reset% 
                                echo %ansi_color_debug%- DEBUG: LYRICS_ACCEPTABLE=“%LYRICS_ACCEPTABLE%” %blink_oN%do we ... exit now if this happens???%blink_off%%ansi_reset%
                        endiff 
                else 
                        rem echo LYRICS_ACCEPTABLE is “%LYRICS_ACCEPTABLE%” 
                endiff


rem Make sure postprocessed lyrics exist because we’re about to print them:
        gosub create_or_set_postprocessed_lyrics "%POSTPROCESSED_LYRICS%" 
        call subtle "%star2% Postprocessed lyrics are now “%postprocessed_lyrics%” GOAT"
        if "1" == "%DEBUG_TRACE_CSFF%" pause "Are we here at 1882"


rem Compare lyrics vs postprocessed vs transcription, with visual stripes between (stL=lower stripe, stB=both, stU=upper stripe):
        :review_changes_with_stripes
        iff exist "%TXT_FILE%" then
                if %@FILESIZE["%TXT_FILE%"] gt 2 call review-file -wh -stL      "%TXT_FILE%"            "¹Lyrics (raw)"
        endiff



        if "1" == "%DEBUG_TRACE_CSFF%" pause "Are we even here 1911"        
        iff "" != "%POSTPROCESSED_LYRICS%" then
                rem pause "postprocessed lyrics are defined"
                if not exist "%POSTPROCESSED_LYRICS%" goto :endiff_1897
                        rem pause "postprocessed lyrics exist"
                        rem if     exist "%POSTPROCESSED_LYRICS%" echo    exists: POSTPROCESSED_LYRICS: "%POSTPROCESSED_LYRICS%"
                        rem if not exist "%POSTPROCESSED_LYRICS%" echo NOT exist: POSTPROCESSED_LYRICS: "%POSTPROCESSED_LYRICS%"
                        if %@FILESIZE["%POSTPROCESSED_LYRICS%"] gt 2 call review-file -wh -stB      "%POSTPROCESSED_LYRICS" "²Lyrics (processed)"
                :endiff_1897
        endiff
@echo off


rem Review the subtitle file, if it exists and is non-zero (enough) in size:
        iff exist "%SRT_FILE%" then
                if %@FILESIZE["%SRT_FILE%"] gt 5 call review-file -wh -stU -ins "%SRT_FILE%"            "³Transcription"
        endiff
        rem @gosub divider                                                                                          
        rem @call bigecho %ANSI_COLOR_BRIGHT_GREEN%%check%  %underline_on%Transcription%underline_off%:
        rem echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]
        rem dislike doing this, but it’s for consistency with print_with_columns.py not having a blank there: @echo. %+ rem .... i just REALLY want one on this and the one before just this time haha
        rem 2025/05/07 taking out as experiment @echos %TOCK%                       %+ rem just our nickname for an extra-special ansi-reset we sometimes call after  copy-move-post.py postprocessing
        rem fast_cat fixes ansi rendering errors in some situations
        rem  (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line "%faint_on%%ansi_color_red%SRT:%faint_off%%ansi_color_bright_Green%        "     |:u8 fast_cat
        rem  (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line.py  "SRT:        %CHECK%" |:u8 fast_cat
        rem  (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line.py  "%check%%ansi_color_green% SRT: %@cool[-------->] %ANSI_COLOR_bright_yellow%
        rem  (grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%SRT_FILE%")  |:u8 insert-before-each-line.py  "%check%%ansi_color_green% SRT: %@cool[-------->] %ANSI_COLOR_bright_yellow%
        rem  (grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%SRT_FILE%")  |:u8 print-with-columns -wh
        rem ^ 2025/05/07 — review-files.bat is now good enough to view SRTs directly without this nonsense
        rem @echo.


rem Cosmetic resets:
        if defined ANSI_RESET (echos %ANSI_RESET%)
        if defined TOCK       (echos %TOCK%)        %+ rem my internal nickname for fancy-extra ansi-reset


rem Full-endeavor success message:
        rem 2025/02/19: Oops! So much has been done about running these through quality control after,
        rem             and it turns out we’ve made 10,000 or so with auto-subtitle-approval-on, oops!
        rem          In actuality, we want to save final approval for when/if we proofread/compare 
        rem                        the original lyrics to the final transcription, including 
        rem                        the possibility of further aligning them against the 
        rem                        original lyrics with the WhisperTimeSync project, 
        rem                        which is integrated into this system.
        rem @gosub divider
        rem call approve-subtitle-file "%SRT_FILE%"
        @gosub divider
        @call  bigecho "%check%%check%%check% %bold_on%%ansi_color_green%“%bold_off%%italics_on%%@NAME[%SRT_FILE%].%@EXT[%SRT_FILE%]%italics_off%” %ansi_color_bright_green%generated successfully!%ansi_color_normal% %check%%check%%check%%party_popper%%emoji_birthday_cake%" 
        title %CHECK% %SRT_FILE% generated successfully! %check%             
        echo %TAB%%TAB%%TAB%%TAB%%ansi_color_less_important%%star2% in dir: %faint_off%%italics_on%%[_CWP]%italics_off%%faint_off%%ansi_color_normal%
        @gosub divider
        if "%_CWD\" != "%SONGDIR%" *cd "%SONGDIR%"
        REM gosub debug "CWP = “%_CWP” 
        iff "1" == "%FORCE_REGEN%" then
                set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE=%EDIT_KARAOKE_AFTER_FORCE_REGEN_WAIT_TIME%
        else
                set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE=%EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME%
        endiff

        rem Ask to approve our karaoke:
                rem if "1" == "%DEBUG_KARAOKE_APPROVAL%" echo About to ask_to_approve_karaoke around line 1969ish
                if "1" == "%DEBUG_KARAOKE_APPROVAL%" echo %ansi_color_warning_soft%🐐 about to gosub ask_to_approve_approve_karaoke [1670] BUT MAYBE WE CAN SKIP THIS%ansi_color_normal% but let’s try adding if not exist "%TXT_FILE%" 
                if not exist "%TXT_FILE%" gosub ask_to_approve_karaoke
                rem TODO remove: if "Y" == "%ANSWER%"      goto /i go_here_if_we_just_approved_the_karaoke

        rem (1) Stuations to EXCLUDE from asking to improve our karaoke:
                if not exist "%TXT_FILE%" .or. "1" == "%JUST_CONVERTED_LRC_TO_TEXT%" .or. "1" == "%JUST_CONVERTED_SRT_TO_TEXT%" .or. "1" == "%whisper_alignment_happened%" goto /i do_not_ask_to_align_with_txt

        rem (2) Ask to IMPROVE our karaoke:
                :ask_about_alignment
                if "1" == "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" set WHISPERTIMESYNC_QUERY_WAIT_TIME=0                                               %+ rem for some reason this is getting reset prior to this, so let’s just set it again here as a kludge
               
                unset /q answer 
                rem call debug "* UNQUOTED INPUT FILE IS “%@UNQUOTE["%INPUT_FILE%"]”"
                rem l AskYN "Align %italics_on%mis-heard%italics_off% karaoke to original lyrics with %italics_on%WhisperTimeSync%%italics_off% [%ansi_green%P%ansi_color_prompt%=Play 1st,%ansi_green%A%ansi_color_prompt%=Approve now,%ansi_color_bright_green%T%ansi_color_prompt%=Dele%ansi_color_green%t%ansi_color_prompt%e,%ansi_color_green%E%ansi_color_prompt%dit transcription]" no %WHISPERTIMESYNC_QUERY_WAIT_TIME% notitle AEIPQTW Q:enQueue_in_winamp,P:Play_It,A:approve_the_karaoke_right_now,T:delete,E:Edit_transcription,I:mark_as_instrumental
                @call AskYN "Align %italics_on%mis-heard%italics_off% karaoke to original lyrics with %italics_on%WhisperTimeSync%%italics_off% [%ansi_green%P%ansi_color_prompt%=Play 1st,%ansi_green%A%ansi_color_prompt%=Approve now,%ansi_color_bright_green%T%ansi_color_prompt%=Dele%ansi_color_green%t%ansi_color_prompt%e+retry,%ansi_color_green%E%ansi_color_prompt%dit it]"            no %WHISPERTIMESYNC_QUERY_WAIT_TIME%         AEIPQTW Q:enQueue_in_winamp,P:Play_It,A:approve_the_karaoke_right_now,T:delete,E:Edit_transcription,I:mark_as_instrumental,W:align_with_WhisperTimeSync
                        rem @Echo OFF %+ echo answer is %ANSWER%
                        set HELD_ANSWER_1787=%ANSWER%
                        rem Option “I”:
                                set ANSWER=%HELD_ANSWER_1787%
                                gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                        rem Option “E”:
                                set ANSWER=%HELD_ANSWER_1787%
                                gosub check_for_answer_of_E "%txt_file%" "%srt_file%" 
                        rem Option “T”:
                                set ANSWER=%HELD_ANSWER_1787%
                                gosub check_for_answer_of_T 

                        rem Option “P”: [1794]
                                set ANSWER=%HELD_ANSWER_1787%
                                set      player_command_extra_options=show_karaoke
                                if  "P" == "%ANSWER%" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%input_file%"
                                unset /q player_command_extra_options
                                if  "P" == "%ANSWER%" goto /i ask_about_alignment          

                        rem Option “Q”: [1794]
                                set ANSWER=%HELD_ANSWER_1787%
                                if  "Q" == "%ANSWER%" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_Q "%input_file%"
                                if  "Q" == "%ANSWER%" goto /i ask_about_alignment          

                        rem Option “A”:
                                set ANSWER=%HELD_ANSWER_1787%
                                iff "A" == "%ANSWER%" then
                                        call approve-karaoke "%srt_file%"
                                        goto /i :go_here_if_we_just_approved_the_karaoke
                                endiff

                        rem Option “Y”:
                                :just_before_affirmative_whisper_timesync
                                :Do_Whisper_Time_Sync
                                set ANSWER=%HELD_ANSWER_1787%
                                iff "Y" == "%ANSWER%" .or. "W" == "%ANSWER%" .or. "1" == "%DO_WHISPER_TIME_SYNC%" then
                                        set DO_WHISPER_TIME_SYNC=0                                                                      %+ rem Turn Off Flag
                                        call debug "call WhisperTimeSync “%SRT_FILE%” “%TXT_FILE%”  “%@UNQUOTE["%INPUT_FILE%"]”"                                     %+ rem GOAT1813
                                        call             WhisperTimeSync "%SRT_FILE%" "%TXT_FILE%"  "%@UNQUOTE["%INPUT_FILE%"]"
                                        goto /i display_karaoke_before_asking_to_edit_it
                                endiff
                        :WhisperTimeSync_alignment_complete

        rem At this point, the karaoke is generated, possibly corrected, and awaiting our approval:
                if  "%KARAOKE_STATUS%" == "APPROVED" goto :karaoke_already_approved_1913
                        if "1" == "%JUST_RENAMED_TO_INSTRUMENTAL%" goto /i END
                        if "1" == "%DEBUG_KARAOKE_APPROVAL%" echo About to ask_to_approve_karaoke around line 2060ish
                        gosub ask_to_approve_karaoke
                :karaoke_already_approved_1913
                :do_not_ask_to_align_with_txt


        rem Last chance to edit the karaoke —— absolutely we need to ask this one last time, even if it’s annoying, because in some situations, it’s the only time:
                :ask_about_karaoke_edit
                        unset /q ANSWER
                        if not exist "%TXT_FILE%" .and. not exist "%SRT_FILE%" goto :skip_asking_to_edit_karaoke_file
                        @call askyn  "Edit karaoke file%blink_on%?%blink_off% %faint_on%[in case of mistakes]%faint_off% [%ansi_color_bright_green%W%ansi_color_prompt%=Run %italics_on%WhisperTimeSync%italics_off%,%ansi_color_bright_green%A%ansi_color_prompt%=Approve karaoke,%ansi_color_bright_green%U%ansi_color_prompt%=Unapprove,%ansi_color_bright_green%T%ansi_color_prompt%=Dele%ansi_color_green%t%ansi_color_prompt%e+retry]" no %EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE% notitle AIEFPQUWT Q:enQueue_in_winamp,E:edit_the_karaoke_file,P:Play_It,W:Fix_With_WhisperTimeSync,A:go_ahead_and_approve_the_karaoke_file,U:unapprove_karaoke,T:delete_karaoke_file,I:Yooo_it's_an_instrumental_actually,F:mark_as_failed_and_untranscribeable
                        set HELD_ANSWER_1922=%ANSWER%
                        :just_asked_to_edit_karaoke
                                rem “Y”/“E”:
                                        rem This can work for either of the previous AskYN calls:
                                        echo %ansi_color_debug%- DEBUG: about to check iff "%ANSWER" == "Y" ...... 🍪%ansi_color_normal%>nul
                                        iff "%ANSWER" == "Y" .or. "%ANSWER" == "E" then
                                                rem @echo %ANSI_COLOR_DEBUG%- DEBUG: %EDITOR% "%SRT_FILE%" [and maybe "%TXT_FILE%"] %ANSI_RESET%
                                                title %check% %SRT_FILE% generated successfully! %check%             
                                                iff not exist "%TXT_FILE%" then
                                                        %EDITOR% "%SRT_FILE%" 
                                                else
                                                        %EDITOR% "%TXT_FILE%" "%SRT_FILE%" 
                                                endiff
                                                echos %emoji_pause% Hit any key when done editing...
                                                *pause>nul
                                                goto /i ask_about_karaoke_edit
                                        endiff
                                rem “I”:
                                        set ANSWER=%HELD_ANSWER_1922%
                                        rem  gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]" and answer=%ANSWER%
                                        gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                                rem “F”:
                                        set ANSWER=%HELD_ANSWER_1922%
                                        gosub check_for_answer_of_F "%@UNQUOTE["%INPUT_FILE%"]"
                                rem “T”:
                                        set ANSWER=%HELD_ANSWER_1922%
                                        gosub check_for_answer_of_T "%@UNQUOTE["%INPUT_FILE%"]"
                                rem “P”/“Q”: 
                                        set ANSWER=%HELD_ANSWER_1922%
                                        set player_command_extra_options=show_karaoke
                                        iff "%ANSWER" == "P" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%input_FILE%"
                                        iff "%ANSWER" == "Q" gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_Q "%input_FILE%"
                                        unset /q player_command_extra_options
                                        set ANSWER=%HELD_ANSWER_1922%
                                        iff "%ANSWER" == "P" then goto /i ask_about_karaoke_edit
                                        iff "%ANSWER" == "Q" then goto /i ask_about_karaoke_edit
                                rem “A”/“U”: 
                                        set ANSWER=%HELD_ANSWER_1922%
                                        iff "A" == "%ANSWER%" then
                                                call  approve-karaoke "%srt_file%"
                                                goto /i go_here_if_we_just_approved_the_karaoke
                                        endiff
                                        iff "U" == "%ANSWER%" then
                                                call disapprove-subtitles "%srt_file%"
                                                goto /i go_here_if_we_unpproved_or_deleted_the_karaoke
                                        endiff
                        set ANSWER=%HELD_ANSWER_1922%


        rem If we got here, we need to ask about karaoke approval:
                if "1" == "%DEBUG_KARAOKE_APPROVAL%" echo * about to gosub approve karaoke 1526
                gosub ask_to_approve_karaoke
                :go_here_if_we_just_approved_the_karaoke

        rem Update the title to say we’re done! We are!
                set MSG=%CHECK% %SRT_FILE% generated successfully! %check%      
                title %MSG%
                echo %ansi_color_important%%star% %msg%%ansi_color_normal%
                if "%SOLELY_BY_AI%" == "1" (call warning "ONLY AI WAS USED. Lyrics were not used for prompting")

        rem If we deleted/unapproved our karaoke, we should end up here:
                :skip_asking_to_edit_karaoke_file
                :go_here_if_we_unpproved_or_deleted_the_karaoke


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
goto /i skip_subroutines


        :ask_about_instrumental [opt opt2 opt3]
                gosub "%BAT%\get-lyrics-for-file.btm" ask_about_instrumental %opt% %opt2% %opt3%
        return
        :ask_to_approve_karaoke [opt]
                if "%KARAOKE_STATUS%" == "APPROVED" (echo %ansi_color_important_less%%star2% Karaoke already approved...%zzzzzz%%ansi_color_normal% %+ return)
                if not exist "%SRT_FILE%"           (echo %ansi_color_important_less%%star2% Karaoke doesn’t exist to approve...%ansi_color_normal% %+ return)

                rem assumes %SRT_FILE% is our karaoke file and %INPUT_FILE% is our audio file
                :ask_about_karaoke_approval                                        
                unset /q ANSWER
                @call askyn  "Approve/edit karaoke file [D=%ansi_color_bright_green%D%ansi_color_prompt%isapprove,dele%ansi_color_bright_green%T%ansi_color_prompt%e,P=%ansi_color_bright_green%P%ansi_color_prompt%lay,E=%ansi_color_bright_green%E%ansi_color_prompt%dit karaoke,W=%ansi_color_bright_green%W%ansi_color_prompt%hisperTimeSync]" no %KARAOKE_APPROVAL_WAIT_TIME% notitle ABDEIPQTWM  E:edit_karaoke,Q:enQueue_in_winamp,P:Play_It,D:DISapprove_them,W:Whisper_Time_sync_fix,A:Yes_approve_it,I:mark_instrumental,T:delete__it,M:restart_winamp,B:regenerate_karaoke
                set HOLD_ANSWER_2006=%ANSWER%
                gosub check_for_answer_of_T "%@UNQUOTE["%INPUT_FILE%"]"
                gosub check_for_answer_of_I "%@UNQUOTE["%INPUT_FILE%"]"
                gosub check_for_answer_of_E "%SRT_FILE%" "%TXT_FILE%"
                gosub check_for_answer_of_B
                gosub check_for_answer_of_M
                set ANSWER=%HOLD_ANSWER_2006%
                iff "%ANSWER" == "W" then
                        set   DO_WHISPER_TIME_SYNC=1
                        gosub DO_WHISPER_TIME_SYNC
                        set ANSWER=Y
                        pause "About to goat-goto just_before_affirmative_whisper_timesync"
                        goto /i just_before_affirmative_whisper_timesync
                endiff
                iff "%ANSWER" == "Y" .or. "%ANSWER" == "A" then
                        call approve-subtitles    "%SRT_FILE%" 
                        set karaoke_status=APPROVED
                endiff
                iff "%ANSWER%" == "D" .or. "%ANSWER" == "N" then
                        set karaoke_status=NOT_APPROVED
                        iff "%ANSWER%" == "D" then
                                call disapprove-subtitles "%SRT_FILE%" 
                        endiff
                        title %RED_X% %SRT_FILE% NOT generated successfully! %RED_X%      
                        goto /i go_here_if_we_unpproved_or_deleted_the_karaoke
                endiff
                set player_command_extra_options=show_karaoke
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%INPUT_FILE%"
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_Q "%INPUT_FILE%"
                unset /q player_command_extra_options

                rem Which answers should lead us back to asking the question agan?  Answer: N/P/Q
                        if "%ANSWER%" == "M" goto /i ask_about_karaoke_approval
                        if "%ANSWER%" == "P" goto /i ask_about_karaoke_approval
                        if "%ANSWER%" == "Q" goto /i ask_about_karaoke_approval

                rem Which answers should take us to where we go if the karaoke is approved: Answer: Y
                        if "%ANSWER%" == "Y" goto /i go_here_if_we_just_approved_the_karaoke
        return
        :check_for_answer_of_B [opt1]                        
                iff "B" == "%ANSWER%" then
                        goto :regenerate_karaoke
                endiff
        return
        :check_for_answer_of_E [opt1 opt2 opt3 opt4]          
                rem check_for_answer_of_H in get-lyrics usually edits the lyrics
                rem check_for_answer_of_E pretty exclusively is for editing the subtitles after
                rem Thing is, if there are mistakes in subtitles, there may be mistakes in lyrics, too.
                rem echo GOAT opt1=“%opt1%”, opt2=“%opt2%”
                if not defined EDITOR call fatal_error "EDITOR needs to be defined as your text editor command,a nd was not, in create-srt-from-file subroutine check_for_answer_of_E"
                iff "E" == "%ANSWER%" then
                        set FILES_TO_USE=%TXT_FILE% 
                        if "" != "%@UNQUOTE["%opt1%"]" .and. exist "%@UNQUOTE["%opt1%"]" set FILES_TO_USE="%@UNQUOTE["%opt1%"]"
                        if "" != "%@UNQUOTE["%opt2%"]" .and. exist "%@UNQUOTE["%opt2%"]" set FILES_TO_USE=%FILES_TO_USE% "%@UNQUOTE["%opt2%"]"
                        if "" != "%@UNQUOTE["%opt3%"]" .and. exist "%@UNQUOTE["%opt3%"]" set FILES_TO_USE=%FILES_TO_USE% "%@UNQUOTE["%opt3%"]"
                        if "" != "%@UNQUOTE["%opt4%"]" .and. exist "%@UNQUOTE["%opt4%"]" set FILES_TO_USE=%FILES_TO_USE% "%@UNQUOTE["%opt4%"]"
                        echo COMMAND IS: %EDITOR% "%FILES_TO_USE%" [goat20394] %+ pause
                        %EDITOR% %FILES_TO_USE%
                        pause "%ansi_color_warning%%blink_on%Press any key when done with edits...%blink_off%%ansi_color_normal%"
                        goto /i review_changes_with_stripes
                endiff
        return
        :check_for_answer_of_F [opt]
                iff "F" == "%ANSWER%" then
                        goto /i ask_about_failed
                endiff
                iff "W" == "%ANSWER%" then
                        set   DO_WHISPER_TIME_SYNC=1
                        goto /i Do_Whisper_Time_Sync
                endiff           
        return
        :check_for_answer_of_M [opt1]                        
                iff "M" == "%ANSWER%" then
                      call restart-winamp
                endiff
        return
        :check_for_answer_of_G [opt]
                if "%@UNQUOTE["%opt%"]" == "" call fatal_error "check_for_answer_of_G in create-srt-from-file.bat needs to be passed a filename"

                if "G" == "%ANSWER%" call get-lyrics "%@UNQUOTE["%opt%"]" force
        return
        :check_for_answer_of_I [opt]                        
                on break resume
                rem echo * calling: gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instr_if_answer_was_I %opt% goat
                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instr_if_answer_was_I %opt%
                on break cancel
        return
        :check_for_answer_of_L [opt opt2]                        
                on break resume
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_L %opt% %opt2%
                on break cancel
        return
        :check_for_answer_of_P [opt]                        
                on break resume
                rem set player_command_extra_options=show_karaoke
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P %opt%
                rem unset /q player_command_extra_options
                on break cancel
        return
        :check_for_answer_of_Q [opt]                        
                on break resume
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_Q %opt%
                on break cancel
        return
        :check_for_answer_of_S [opt]                        
                on break resume
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_S %opt%
                on break cancel
        return
        :check_for_answer_of_T [opt]
                set file_to_use=%INPUT_FILE%
                set opt_1=%@UNQUOTE["%opt%"]
                if exist "%opt_1%" set file_to_use=%opt_1%
                iff "T" == "%ANSWER%" then
                        if     exist "%srt_file%" (echos %ansi_color_removal%%emoji_axe%  `` %+ *del /p /Ns "%srt_file%")
                        if     exist "%lrc_file%" (echos %ansi_color_removal%%emoji_axe%  `` %+ *del /p /Ns "%lrc_file%")
                        if     exist "%txt_file%" (echos %ansi_color_removal%%emoji_axe%  `` %+ *del /p /Ns "%txt_file%")
                        if not exist "%srt_file%" set KARAOKE_STATUS=NOT_APPROVED
                        if not exist "%txt_file%" set   LYRIC_STATUS=NOT_APPROVED
                        set HELD_ANSWER=%ANSWER%
                                iff not exist "%srt_file%" then
                                        unset /q ANSWER
                                        call AskYN "Rename as instrumental" yes 0
                                        iff "Y" == "%ANSWER%" then
                                                gosub rename_audio_file_as_instrumental "%file_to_use%" ask
                                        else
                                                unset /q ANSWER
                                                call AskYN "Try transcribing again with a lower voice detection threshold (current is “%italics_on%%VAD_threshold%%italics_off%”)" no 0
                                                        iff "Y" == "%ANSWER%" then
                                                                gosub VAD_threshold_advice
                                                                eset  vad_threshold
                                                                set goto_try_again=1
                                                        endiff
                                                        unset /q ANSWER
                                                call AskYN "Try again with a different language (current is “%italics_on%%our_language%%italics_off%”)" no 0
                                                        iff "Y" == "%ANSWER%" then
                                                                eset  our_language
                                                                set goto_try_again=1
                                                        endiff
                                                        unset /q ANSWER
                                                echo %star2% Current lyrics are: %italics_on%%our_lyrics%%italics_on%
                                                rem  AskYN "Try again with unsetting the lyrics so there are no lyrics"   no   0
                                                call AskYN "Try the whole process again from the very very start"         yes  0
                                                        iff "Y" == "%ANSWER%" then
                                                                echo %ansi_color_removal%%emoji_axe% Unsetting lyrics...%ansi_color_normal%
                                                                unset our_lyrics*
                                                                set goto_try_again=1
                                                        endiff
                                                set ANSWER=%HELD_ANSWER%
                                        endiff
                                        if "1" == "%goto_try_again%" goto /i :go_here_for_encoding_retries
                                endiff
                        set ANSWER=%HELD_ANSWER%
                        goto /i go_here_if_we_unpproved_or_deleted_the_karaoke
                endiff
        return
        :clear_rows_for_lockfile_messages [num_rows]
                repeat %num_rows% echo. %+ echo %@ANSI_MOVE_TO_ROW[%@EVAL[%_ROWS-(%num_rows%+1)]]
        return
        :debug [msg]
                echo %ANSI_COLOR_DEBUG%- DEBUG: %msg% %ansi_color_normal%
        return
        :debug_show_lyric_status []
                if "%debug_show_lyric_status%" != "0" echo %ansi_color_debug%- DEBUG: LYRICLESSNESS_STATUS=%bold_on%“%bold_off%%LYRICLESSNESS_STATUS%%bold_on%”%bold_off% ...LYRIC_STATUS=%bold_on%”%bold_off%%LYRIC_STATUS%%bold_on%”%bold_off%%ansi_color_normal%
        return
        :DisplayAudioFileName
                echo %star% Audio filename: %faint_on%%INPUT_FILE%%faint_off%%conceal_on%%0%%conceal_off%
        return                                     

        rem if not defined  AUDIO_FILE_LOCK_FILE set  AUDIO_FILE_LOCK_FILE=%@UNQUOTE[%@path["%INPUTFILE%"]].lock
        :lockfile_set_transcriber_lock_file_variables [opt]
                if not defined TRANSCRIBER_LOCK_FILE set TRANSCRIBER_LOCK_FILE=%@UNQUOTE[%@path[%search%]%@NAME[%TRANSCRIBER_TO_USE%]].lock
        return
        :lockfile_create_transcriber_lock_file [opt]
                if not defined TRANSCRIBER_LOCK_FILE set gosub lockfile_set_transcriber_lock_file_variables
                :check_lock_file_try_again
                        rem xist "%TRANSCRIBER_LOCK_FILE%" (gosub lockfile_wait_on_transcriber_lock_file %+ return)
                        iff    exist "%TRANSCRIBER_LOCK_FILE%" then
                                gosub clear_rows_for_lockfile_messages %LOCKFILE_MESSAGE_ROWS_TO_CLEAR%
                                echo %ansi_color_warning_soft%%STAR2% Lockfile already exists!%ansi_erase_to_end_of_line% 
                                set LOCKFILE_ALREADY_EXISTS=1 
                                type %TRANSCRIBER_LOCK_FILE% 
                                delay 2 
                                return 666
                        endiff
                        if not exist "%TRANSCRIBER_LOCK_FILE%" set LOCKFILE_ALREADY_EXISTS=0
                :actually_create_it
                        iff not exist "%TRANSCRIBER_LOCK_FILE%" then
                                rem call debug "Creating lock file “%TRANSCRIBER_LOCK_FILE%”"
                                rem echo. %+ rem added very late 2024/04/28 then removed 2025/05/08
                                set LOCKFILE_ALREADY_EXISTS=0
                                gosub divider
                                delay /m %@RANDOM[1000,5000]
                                iff exist "%TRANSCRIBER_LOCK_FILE%" return 666
                                echo %ansi_color_important_less%%STAR2% Creating lock file: %faint_on%“%italics_on%%@UNQUOTE["%TRANSCRIBER_LOCK_FILE%"]%italics_off%” [time=%_datetime]%faint_off%%ansi_color_normal%
                                echo %ansi_color_green%%star2% Process %ansi_color_orange%%[_PID]%ansi_color_green% is transcribing: %ansi_color_cyan%“%ansi_color_pink%%SONGFILE%%ansi_color_cyan%”%ansi_color_green%%ansi_erase_to_end_of_line%>"%TRANSCRIBER_LOCK_FILE%"
                                echo %ansi_color_green%                 %star2% beginning at %ansi_color_purple%%[_time]%ansi_color_green% on date %ansi_color_purple%%_date%>>"%TRANSCRIBER_LOCK_FILE%"
                                echo %ansi_color_green%                 %star2% in folder “%_CWP”>>"%TRANSCRIBER_LOCK_FILE%"
                                attrib +r "%TRANSCRIBER_LOCK_FILE%"   >&nul
                        endiff
        return
        :lockfile_read_lockfile_values [opt]
                rem Make sure lockfile exists:
                        if not defined TRANSCRIBER_LOCK_FILE set gosub lockfile_set_transcriber_lock_file_variables
                        if not exist %TRANSCRIBER_LOCK_FILE% return -1

                rem Strip ANSI from lockfile contents if it exists:
                        set raw=%@if[exist %TRANSCRIBER_LOCK_FILE%,%@LINE[%TRANSCRIBER_LOCK_FILE%,0],NONE]
                        iff "%raw" == "NONE" then
                                unset /q lockfile_filename lockfile_pid
                                return
                        endiff
                        set clean=%@STRIPANSI[%raw%]

                rem Get lockfile’s stated PID:
                        set pos=%@INDEX[%clean,Process ]
                        set after=%@SUBSTR[%clean,%@EVAL[%pos + 8]]
                        set lockfile_pid=%@WORD[0,%after]
                        if %DEBUG_LOCKFILE% gt 0 call debug "🔒🔒🔒 Detected lockfile PID of “%lockfile_pid%” (our pid is %_PID) GOAT" 

                rem Get lockfile’s filename:
                        set pos1=%@INDEX[%clean,“]
                        set pos2=%@INDEX[%clean,”]
                        set start=%@EVAL[%pos1 + 2]
                        set len=%@EVAL[%pos2 - %start]
                        set lockfile_filename=%@SUBSTR[%clean,%start,%len]
                        if %DEBUG_LOCKFILE% gt 0 call debug "🔒🔒🔒 Detected lockfile filename of “%lockfile_filename%” GOAT"         
        return %lockfile_pid%
        :lockfile_delete_transcriber_lock_file [opt]
                if %DEBUG_LOCKFILE% gt 0 echo 📞📞📞 called :lockfile_delete_transcriber_lock_file [%opt%] 📞📞📞 🐐
                if not defined TRANSCRIBER_LOCK_FILE gosub lockfile_set_transcriber_lock_file_variables
                :lockfile_delete_transcriber_lock_file_begin
                iff exist "%TRANSCRIBER_LOCK_FILE%" then
                        echo %ansi_color_removal%%emoji_axe% Deleting lock file: “%italics_on%%faint_on%%TRANSCRIBER_LOCK_FILE%%faint_off%%italics_off%”"%ansi_color_normal%
                        attrib -r          "%TRANSCRIBER_LOCK_FILE%" >&nul
                        *del /q /Ns /z /a: "%TRANSCRIBER_LOCK_FILE%" >&nul
                endiff
                iff exist "%TRANSCRIBER_LOCK_FILE%" then
                        call error "Why does the lockfile of “%TRANSCRIBER_LOCK_FILE%” still exist?"
                        goto /i lockfile_delete_transcriber_lock_file_begin
                endiff
        return
        :lockfile_wait_on_transcriber_lock_file [opt]
                if not defined TRANSCRIBER_LOCK_FILE gosub lockfile_set_transcriber_lock_file_variables
                :start_waiting
                if %DEBUG_LOCKFILE% gt 0 echos 🐐 [%_datetime Checking lockfile...if exist “%TRANSCRIBER_LOCK_FILE%”] ``
                delay /m %@RANDOM[23,53]
                if exist "%TRANSCRIBER_LOCK_FILE%" if %DEBUG_LOCKFILE% gt 0 (echos [🐐 It exists!] %+ goto :do_it_1992)
                if exist "%TRANSCRIBER_LOCK_FILE%" if %DEBUG_LOCKFILE% gt 0 (echos [🐐 It didn’t exist but then did right away!] %+ goto :skip_it_2024)

                if %DEBUG_LOCKFILE% gt 0 echo returning Nolockfile...                
                return "NO_LOCKFILE"

                        :do_it_1992
                        if %DEBUG_LOCKFILE% gt 0 [lockfile echos 🐐do_it_1992 %_datetime]
                        rem Check if it’s the lockfile for the current process, and delete it if it is, 
                        rem because we ARE the current process, so this is leftover from a previous failure
                                if     exist "%TRANSCRIBER_LOCK_FILE%" if %DEBUG_LOCKFILE% gt 0 echos [🐐LF exists!]
                                if not exist "%TRANSCRIBER_LOCK_FILE%" if %DEBUG_LOCKFILE% gt 0 echos [🐐LF DNE!]
                                if not exist "%TRANSCRIBER_LOCK_FILE%" goto  :skip_it_2024
                                if     exist "%TRANSCRIBER_LOCK_FILE%" gosub :lockfile_read_lockfile_values
                                set SAME_PROC=0
                                set DO_NEXT_BLOCK=0
                                rem     "1" == "%@RegEx[%_PID,"%LOCKFILE_CONTENTS%"]" (set DO_NEXT_BLOCK=1)
                                if  "%_PID" == "%lockfile_pid%"                       (set DO_NEXT_BLOCK=1 %+ set SAME_PROC=1)
                                iff     "0" == "%ALREADY_ASKED_TO_DELETE_LOCKEFILE%"  then
                                        set DO_NEXT_BLOCK=1 
                                        type %TRANSCRIBER_LOCK_FILE%
                                        set my_wait_time=45 %+ rem I hope this is a sensible choice... GOAT
                                else
                                        set my_wait_time=%@RANDOM[3,13]
                                endiff
                                if %DEBUG_LOCKFILE% gt 0 echo DO_NEXT_BLOCK is %DO_NEXT_BLOCK% 🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞🌞 [wait time is %my_wait_time%]>nul
                                iff      "1" == "%DO_NEXT_BLOCK%" then
                                        echos %ansi_color_warning_soft%%star3% Lockfile exists!%ansi_color_green%...
                                        iff "1" == "%SAME_PROC%" then 
                                                echos but it%smart_apostrophe%s the lockfile for %italics_on%this%italics_off% process...
                                        else
                                                echos and is the lockfile for %italics_on%this%italics_off% process...
                                        endiff
                                        echo %ansi_erase_to_end_of_screen%

                                        set my_question=Delete the lockfile
                                        iff "1" == "%SAME_PROC%" set my_question=%my_question% since it is for this process

                                        call AskYN "%my_question" no %my_wait_time%
                                        set ALREADY_ASKED_TO_DELETE_LOCKEFILE=1

                                        if "Y" == "%ANSWER%" gosub lockfile_delete_transcriber_lock_file
                                        return 777
                                :endif_1997
                                :start_waiting_at_point_of_having_contents_already

                        
                        rem Ask to delete the lockfile, or wait for it to finish:
                                rem repeat 8 echo. %+ echos %@ANSI_MOVE_UP[8] 
                                echos %ansi_position_save%
                                rem gosub divider seems to give me batch nesting limits due to recursion.. Let’s try calling our batfile instead
                                rem call divider ism ore specifically this:
                                call display-horizontal-divider
                                iff "1" != "%LOCKFILE_MENTIONED_ALREADY%" then
                                        set num_lines=10
                                        repeat %num_lines% echo.
                                        echos %@ANSI_MOVE_UP[%num_lines%]
                                endiff
                                rem Make it be on same part of screen over and over:
                                        if     defined WAITING_ON_LOCKFILE_ROW echos %@ANSI_MOVE_TO_ROW[%@EVAL[%WAITING_ON_LOCKFILE_ROW% + 1]]
                                        if     defined WAITING_ON_LOCKFILE_COL echos %@ANSI_MOVE_TO_COL[%@EVAL[%WAITING_ON_LOCKFILE_COL% + 0]]
                                        if not defined WAITING_ON_LOCKFILE_ROW set WAITING_ON_LOCKFILE_ROW=%_row 
                                        if not defined WAITING_ON_LOCKFILE_COL set WAITING_ON_LOCKFILE_COL=%_column
                                call divider
                                echos %ansi_color_important_less%%star2% Waiting on lockfile...
                                set LOCKFILE_MENTIONED_ALREADY=1
                                echo %ANSI_COLOR_WARNING_SOFT%%STAR2% Lockfile already exists❕  %faint_on%Status:%faint_off%%ansi_erase_to_end_of_line%%ansi_eol%%ansi_reset%
                                echos         %ansi_color_debug%``                              
                                if     exist "%TRANSCRIBER_LOCK_FILE%" (type "%TRANSCRIBER_LOCK_FILE%" %+ set LOCKFILE_ALREADY_EXISTS=1)
                                if not exist "%TRANSCRIBER_LOCK_FILE%" (echo ...But it just vanished!  %+ set LOCKFILE_ALREADY_EXISTS=0 %+ goto /i :skip_it_2024)
                

                                unset /q ANSWER
                                echos %ansi_erase_to_end_of_line%
                                call  AskYN  "Delete lockfile%ansi_erase_to_end_of_line%"  no  %@RANDOM[3,13] 
                                rem This one makes no sense here: E E:Edit_ai_prompt
                                rem if  "%ANSWER%" == "E" gosub eset_fileartist_and_filesong
                                iff "%ANSWER%" == "Y" then
                                        call warning "Deleteing lockfile because you answered Y" 
                                        gosub lockfile_delete_transcriber_lock_file
                                else
                                        rem echos %ansi_restore_position%%@ansi_move_up[4]%ansi_erase_to_end_of_screen%%ansi_reset%
                                        echos %@ANSI_MOVE_TO_ROW[%@EVAL[%_rows-10]]
                                        echos %@ANSI_MOVE_TO_COL[0]
                                        echos %ansi_erase_to_end_of_screen%
                                        echos %ansi_reset%
                                        rem goto /i check_lock_file_try_again
                                endiff
                :skip_it_2024
                        if %DEBUG_LOCKFILE% gt 0 echos [🐐locfile :skip_it_2024]
                        iff exist "%TRANSCRIBER_LOCK_FILE%" then
                                echos [₁lockfile exists]🐐
                                *delay /m %@RANDOM[75,125]
                                set LOCKFILE_ALREADY_EXISTS=1
                                goto /i start_waiting_at_point_of_having_contents_already
                        endiff
                        set LOCKFILE_ALREADY_EXISTS=0
                if %DEBUG_LOCKFILE% gt 0 echo 📞 returning  lockfile_wait_on_transcriber_lock_file 
        return
        :mark_as_untranscribeable [file_to_mark_as_untrans]
                echo %ansi_color_important%%star% Marking file as untranscribeable / karaoke_failed / do not try again: %ansi_color_normal%
                echo %ansi_color_important%%zzzz%     %italics_on%%file_to_mark_as_untrans%%italics_off% %ansi_color_normal%
                echo True>"%@UNQUOTE["%file_to_mark_as_untrans%"]:karaoke_failed"  
                echo    %ansi_color_warning% ...Aborting subtitle/karaoke creation! %ansi_color_normal%
                goto /i END
        return
        :postprocess_lrc_srt_files
                rem cls %+ type "%SRT_FILE%" %+ echo %arrow_up% there it was.... temporary pause before processing subtitle file to check on apostrophe corruption strangeness %+ pause
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[purple]%ANSI_CURSOR_CHANGE_TO_BLOCK_steady%                
                set review_srt=0                                                                
                set review_lrc=0                                                               
                set review_txt=0                                                               
                if     exist "%LRC_FILE%" .and.     exist "%SRT_FILE%"  echo %ANSI_COLOR_IMPORTANT_LESS%%STAR% Postprocessing %italics_on%SRT%italics_off% and %italics_on%LRC%italics_off% files...
                if not exist "%LRC_FILE%" .and.     exist "%SRT_FILE%"  echo %ANSI_COLOR_IMPORTANT_LESS%%STAR% Postprocessing %italics_on%SRT%italics_off% file...
                if     exist "%LRC_FILE%" .and. not exist "%SRT_FILE%"  echo %ANSI_COLOR_IMPORTANT_LESS%%STAR% Postprocessing %italics_on%LRC%italics_off% file...

                rem SRT: Postprocess the SRT file to remove the “invisible periods” we add to cause WhisperAI’s “--sentence” parameter to work correctly:
                rem LRC: Also do the same for the LRC file, even though it shoudln’t have any “invisible periods”
                        if exist "%SRT_FILE%" subtitle-postprocessor.pl -w "%SRT_FILE%"     
                        if exist "%LRC_FILE%" subtitle-postprocessor.pl -w "%LRC_FILE%"     

                rem This whole block of reviewing only should happen in certain situations, not all situations. It looked cool when put in, then ended up being too much for most situations:
                        goto /i todo_figure_this_out_1841
                                if  exist  "%SRT_FILE%"   set    review_srt=1
                                if  exist  "%LRC_FILE%"   set    review_lrc=1
                                if  exist  "%TXT_FILE%"   .and.  ("1" == "%REVIEW_SRT%" .or. "%review_lrc%" == "1") set review_txt=1
                                if  "1" == "%REVIEW_LRC%" call   review-file  -stL       "%LRC_FILE%"
                                if  "1" == "%REVIEW_TXT%" call   review-file  -stB       "%TXT_FILE%"
                                if  "1" == "%REVIEW_SRT%" call   review-file  -stU  -ins "%SRT_FILE%"
                        :todo_figure_this_out_1841

                rem echo ...%CHECK% %ANSI_COLOR_GREEN%Success%BOLD_ON%!%BOLD_OFF%%ANSI_COLOR_NORMAL%
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%                
        return
        :refresh_lyric_status [opt]
                gosub "%BAT%\get-lyrics-for-file.btm" refresh_lyric_status %opt%
        return
        :refresh_lyriclessness_status [opt]
                rem TODO GOAT change audio_file to input_file and see if no problems
                goto :fast
                                :slow
                                        if ("" == "%LYRICLESSNESS_STATUS%" .and. exist "%AUDIO_FILE%") .or. "%opt%" == "force" call get-lyriclessness-status "%AUDIO_FILE%" silent
                                goto :refreshed
                        :fast
                                if ("" == "%LYRICLESSNESS_STATUS%" .and. exist "%AUDIO_FILE%") .or. "%opt%" == "force" set LYRICLESSNESS_STATUS=%@EXECSTR[type <"%@unquote["%AUDIO_FILE%"]:lyriclessness" >&>nul]``
                        goto :refreshed
                :refreshed
        return
        :rename_audio_file_as_instrumental [opt opt2 opt3] 
                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental %opt% %opt2% %opt3%
        return
                                                                                :rename_audio_file_as_instrumental_deprecate_20250501_oops_had_two_diff_funcs_doing_very_similar_things_so_refactored_this_one_out [opt opt2] 
                                                                                        rem DEBUG:
                                                                                                rem echo %ansi_color_debug%- DEBUG: called rename_audio_file_as_instrumental [opt=%opt%,opt2=%opt2%]  %ansi_color_normal%

                                                                                        rem If we have been asked to ask [if it’s an instrumental], then we need to ask [if it’s an instrumental]:
                                                                                                :rafai_ask_again
                                                                                                unset /q ANSWER                       
                                                                                                if "%1" == "ask" .or. "%opt2%" == "ask" .and. "Y" != "%OUTER_INSTRUMENTAL_ANSWER%"  call AskYN "DEPRECATED QUESTION SHOULD NEVER HAPPEN!! WTF !! Mark as instrumental? [P=%ansi_color_bright_green%P%ansi_color_prompt%lay]" no 500 PQ Q:enQueue_in_winamp,P:play_it

                                                                                        rem Rename it if we are supposed to!
                                                                                                if  "Y" == "%ANSWER%"  gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental %opt%

                                                                                        rem Play it, if we were asked to do that instead, prior to renaming:
                                                                                                iff "P" == "%ANSWER%" then
                                                                                                        gosub   check_for_answer_of_P   %opt%
                                                                                                        goto /i rafai_ask_again       
                                                                                                endiff
                                                                                return
        :rename_audio_file_as_instr_if_answer_was_I [opt]
                if "I" == "%ANSWER%" gosub rename_audio_file_as_instrumental %opt%
        return
        :create_or_set_postprocessed_lyrics [opt]
                if "1" == "%DEBUG_ECHO_CALLS_TO_GETLYRICS%" echo %ansi_color_debug%%EMOJI_PHONE%  BEGIN: gosub [get-karaoke::]create_or_set_postprocessed_lyrics %opt%  ... postprocessed_lyrics is now =“%postprocessed_lyrics%”%ansi_color_normal%
                gosub "%BAT%\get-lyrics-for-file.btm" create_or_set_postprocessed_lyrics "%@UNQUOTE["%opt%"]"
                if "1" == "%DEBUG_ECHO_CALLS_TO_GETLYRICS%" echo %ansi_color_debug%%EMOJI_PHONE%  ENDED: gosub [get-karaoke::]create_or_set_postprocessed_lyrics %opt%  ... postprocessed_lyrics is now =“%postprocessed_lyrics%”%ansi_color_normal%
        return
        :usage
                %color_advice%
                echo.
                        echo USAGE: COMMON:
                        echo        $0 {filename} ——————————————————————————————— create karaoke transcription for a specific audio file
                        echo        $0 {filename} PromptAnalysis ———————————————— generate prompt to create karaoke transcription for a specific audio file, but do not actually run prompt
                        echo.
                        echo USAGE COMPLETE:
                        echo        $0 {filename} ai  ——————————————————————————— use AI only; no lyrics; with   normal  prompt wait times
                        echo        $0 {filename} AutoLyricApproval or la ——————— long  way to: consider all lyric files to be in APPROVED status, even if they are not marked as such                
                        echo        $0 {filename} la ———————————————————————————— short way to: consider all lyric files to be in APPROVED status, even if they are not marked as such                
                        echo        $0 {filename} cleanup ——————————————————————— clean up trash after transcription —— clean-up-AI-transcription-trash-files.bat also cleans these
                        echo        $0 {filename} fast —————————————————————————— normal execution but with shortenedp rompt wait times
                        echo        $0 {filename} force ————————————————————————— generate even if SRT/LRC already exists
                        echo        $0 {filename} last —————————————————————————— redo the previous generation again [in case it was interrupted]
                        echo        $0 {filename} PromptAnalysis ———————————————— generate prompt to create karaoke transcription for a specific audio file, but do not actually run prompt
                        echo.
                        echo COMMON USE CASES:
                        echo        $0 {filename} fast —————————————————————————— to quickly do a file w/o lyrics, using AI only, with short prompt times.
                        echo        $0 {filename} la force —————————————————————— regenerate a new SRT with the existing lyric file even if it’s not approved
                        echo.
                        echo ENVIRONMENT VARIABLE PARAMETERS:
                        echo        set OVERRIDE_LANGUAGE=None ————————————————— to change the default language for a session, for example if it’s a Rammstein album, set to “de” for German. 
                        echo                                                     If you aren’t sure, set it to “None”, because our default language is usually set to “en” for English 
                        echo        set OVERRIDE_VAD_THRESHOLD=0.01 ———————————— to change the default VAD_THRESHOLD for a session, for example lowering to 0.01 on a low-production punk album with hard to hear vocals.  Usually 0.75-ish is a decent value that is the best tradeoff. But now that we auto-remove well-known WhisperAI hallucations, it’s a bit safer to lower it in special situations.
                        echo        set CONSIDER_ALL_LYRICS_APPROVED=1  ———————— another way to trigger AutoLyricApproval mode
                        echo 
                        echo INTERNAL-ONLY USAGE:
                        echo        %0 postprocess_lrc_srt_files ——————————————— just run the postprocess_lrc_srt_files function
                echo.
                %color_normal%
        return
        :VAD_threshold_advice []
                call advice "Lower the VAD threshold from %DEFAULT_VAD_THRESHOLD% to something lower to capture more detail."                silent
                call advice "I have had to go as low as 0 for success!"                                                                      silent
        return

        :skip_subroutines


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem
rem                                   T  H  E         E   N   D 
rem
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


:END
:Cleanup2
:Cleanup_Only
:csff_onbreak
:nothing_generated
:just_do_the_cleanup
        rem Stop the Timer:
                setdos /x0
                if defined ansi_color_unimportant echos %ansi_color_unimportant%
                timer /5 off
                if defined ansi_color_reset       echos %ansi_color_reset%

        rem Unlock the status bar:
                setdos /x0
                call status-bar unlock

        rem Delete certain junk files if present:
                if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav >nul)
                if exist     *vad_original*.srt (*del /q     *vad_original*.srt >nul)

        rem This happens earlier, but we also want it to happen in cleanup, because sometimes cleanup is called from transcribed stuff *NOT* made with this script:
                iff "1" == "%CLEANUP%" then
                        if exist *.lrc call delete-zero-byte-files *.lrc silent >nul
                        if exist *.srt call delete-zero-byte-files *.srt silent >nul
                endiff

:The_Very_END
:EOF
        rem Reset cursor/test color/size with ANSI:
                setdos /x0
                @echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[orange]%ANSI_CURSOR_CHANGE_TO_DEFAULT%                
                @echos %ANSI_RESET%%CURSOR_RESET%


:PopD
        rem Get us back to the folder we were in when we called this... but only if told to:
                setdos /x0
                rem if "1" == "%pushd_performed_in_create_srt%" (echo * 2025 POPD! %+ pause)
                    if "1" == "%pushd_performed_in_create_srt%" (popd)

:Fix_Command_Separator
        rem Extra-safe command separator fixing:
                *setdos /x-5
                *setdos /c%default_command_separator_character%
                 setdos /x0

:Save_Variables
        rem Some variables we want to save before unsetting:
                set last_failure_ads_result=%failure_ads_result%
                set last_postprocessed_lyrics=%postprocessed_lyrics%

:Warn_Variables
        rem Some override variables we want to warn the user they are set:
                if "" != "%OVERRIDE_VAD_THRESHOLD%"  (call warning "%italics_on%％OVERRIDE_VAD_THRESHOLD％%italics_off% is still set (value=“%OVERRIDE_VAD_THRESHOLD%”)" big %+ sleep 3)
                if "" != "%OVERRIDE_LANGUAGE%"       (call warning "%ITALICS_ON%％OVERRIDE_LANGUAGE％%ZZZ%%italics_off% is still set (value=“%OVERRIDE_LANGUAGE%”)"      big %+ sleep 3)

:Unset_Variables
        rem The big list of vars to unset:
                unset /q failure_ads_result PROMPT_CONSIDERATION_TIME PROMPT_EDIT_CONSIDERATION_TIME JUST_APPROVED_LYRICLESSNESS goto_forcing_ai_generation LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE ABANDONED_SEARCH LYRICLESSNESS_STATUS AUTO_LYRIC_APPROVAL        ALREADY_HAND_EDITED FORCE_AI_ENCODE_FROM_LYRIC_GET JUST_RENAMED_TO_INSTRUMENTAL  goto_end abort_karaoke_kreation MAYBE_SRT* karaoke_status audio_file input_file postprocessed_lyrics LAUNCHING_AI_DISPLAYED WAITING_ON_LOCKFILE_ROW WAITING_ON_LOCKFILE_COL WAITING_FOR_COMPL_ROW WAITING_FOR_COMPL_COL  ALREADY_ASKED_TO_DELETE_LOCKEFILE SONG_PROBED_VIA_CALL_FROM_CREATE_SRT LOCKFILE_NOT_FOR_THIS_PROCESS_MENTIONED JUST_CONVERTED_SRT_TO_TEXT JUST_CONVERTED_LRC_TO_TEXT LYRICS_ACCEPTABLE OKAY_THAT_WE_HAVE_SRT_ALREADY UNFORTUNATELY_WE_COULD_NOT_CREATE_SAID

               
:The_Very_Very_END
        setdos /x0
        set MAKING_KARAOKE=0
        echo 🐐%@COLORFUL[[END-CREATE-SRT-FROM-FILE, CWP=%_CWP]]
