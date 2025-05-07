@echo %@colorful[🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗 CREATE-SRT-FROM-FILE 🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗🚗] CWP=%_CWP
rem >nul
@loadbtm on
@Echo off
@rem @set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=1
@setdos /x0
@on break cancel
@rem echo **** create-srt-from-file.bat called **** 🌭🌭🌭 
@if not defined Default_command_Separator_Character set Default_command_Separator_Character=`^`
@call status-bar unlock
@set temporarily_disable_status_bar=0
rem 20250328 let’s try removing this: @setlocal

rem TODO: pull WhisperTimeSync karaoke-fix functionality OUT or make a bat file that calls it from within here

rem TODO: not outfitted for the situation of successful generation but no words found so no file produced

rem TODO: concurrency: not just lock file, but per-file lock so we don’t operate on the same file...

rem TODO: add another srt to subtitles if the last one is not empty to combat stuck lyrics:
                rem 17
                rem 00:02:20,060 --> 00:02:21,060
                rem This should be default functionality of srt2lrc as well — the resulting lrc should have an empty at the end too
                rem So we must postprocess before we would ever even use srt2lrc
                rem     no need to include functionality in srt2lrc as we’re not sure this will be a final part of the workflow
                rem     plus, we need to run this on pre-existing SRTs

rem MAYBE TODO afterregen anyway, do we need to ask about ecc2fasdfasf.bat?


:REQUIRES:     <see validators>
:DEPENDENCIES: 2024 version: Faster-Whisper-XXL.exe delete-zero-byte-files.bat validate-in-path.bat debug.bat error.bat warning.bat errorlevel.bat print-message.bat validate-environment-variable.bat —— see validators for complete list
:DEPENDENCIES: 2023 version: whisper-faster.bat delete-zero-byte-files.bat validate-in-path.bat debug.bat error.bat warning.bat errorlevel.bat print-message.bat validate-environment-variable.bat

:USAGE: lrc.bat whatever.mp3 {force|ai|cleanup|last|fast|AutoLyricApproval|PromptAnalysis} {rest=options to pass on to whisper} ... ai=force ai regeneration, last=redo last one again, force=proceed even if LRC file is there, cleanup=clean up leftover files,  AutoLyricApproval=consider sidecar TXT files to be pre-approvedl yrics, PromptAnalysis=gather prompts to log file, don’t actually run the encoding
:USAGE: set USE_LANGUAGE=jp                ——— to encode in a different language from en, like jp
:USAGE: set CONSIDER_ALL_LYRICS_APPROVED=1 ——— for *forced* pre-approved-lyrics mode (deprecated)


rem ———————————————————————————————————————————————— USAGE: ———————————————————————————————————————————
iff "%1" == "" then 
        gosub usage
        goto /i The_Very_END
endiff
goto :subroutine_definitions_end
     :subroutine_definitions_begin
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
                        echo        set USE_LANGUAGE=jp ———————————————————————— to change the default language, for example if it’s a Rammstein album, set to de
                        echo        set CONSIDER_ALL_LYRICS_APPROVED=1  ———————— another way to trigger AutoLyricApproval mode
                        echo 
                        echo INTERNAL-ONLY USAGE:
                        echo        %0 postprocess_lrc_srt_files ——————————————— just run the postprocess_lrc_srt_files function
                echo.
                %color_normal%
        return
    :subroutine_definitions_end

rem Pre-Cleanup:
        unset /q goto_download_with_lyric_downloader* goto_end JUST_APPROVED_LYRICLESSNESS goto_forcing_ai_generation ABANDONED_SEARCH LYRICLESSNESS_STATUS FAILURE_ADS_RESULT LYRIC_APPROVAL LYRICS_APPROVAL LYRICLESSNESS_APPROVAL return_point 
        unset /q LYRIC_STATUS  %+ rem 20250505 todo am i gonna regret this❔?⁉️❔?❔?❔⁉️⁉️⁉️⁉️❓❓⁉️❓⁉️❓⁉️❓⁉️?⁉️❔
        unset /q our_lyrics*   %+ rem 20250505 todo am i gonna regret this❔?⁉️❔?❔?❔⁉️⁉️⁉️⁉️❓❓⁉️❓⁉️❓⁉️❓⁉️?⁉️❔
        unset /q tmppromptfile %+ rem 20250505 todo am i gonna regret this❔?⁉️❔?❔?❔⁉️⁉️⁉️⁉️❓❓⁉️❓⁉️❓⁉️❓⁉️?⁉️❔


rem MAJOR BRANCHING:
        iff "%1" ==  "postprocess_lrc_srt_files" then
                gosub postprocess_lrc_srt_files
                goto /i EOF
        endiff




REM CONFIG: LOGFILES: 
        iff not defined LOGS then                                                                      %+ rem copy this line to get-lyrics-for-file as well
                mkdir c:\logs                                                                          %+ rem copy this line to get-lyrics-for-file as well
                set logs=c:\logs                                                                       %+ rem copy this line to get-lyrics-for-file as well
                if not isdir %logs% mkdir %logs%                                                       %+ rem copy this line to get-lyrics-for-file as well
        endiff                                                                                         %+ rem copy this line to get-lyrics-for-file as well
        set              AUDIOFILE_TRANSCRIPTION_LOG_FILE=%LOGS%\audiofile-transcription.log           %+ rem copy this line to get-lyrics-for-file as well
        set AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE=%LOGS%\audiofile-transcription-prompts.log   %+ rem copy this line to get-lyrics-for-file as well

REM CONFIG: 2025: 
        set DELETE_BAD_AI_TRANSCRIPTIONS_FIRST=0                                                       %+ rem TODO keep this set to 1 usually, but 0 for speeding up
REM CONFIG: 2024: 
        gosub set_TRANSCRIBER_VALID_EXTENSIONS_AND_LOCK_FILE_NAME                                      %+ rem Done as subroutine so it can be called by get-lyrics in case it needs it too
        set INSIST_ON_HAVING_ARTIST=0                                                                  %+ rem Set to 1 to ALWAYS ask for an artist, even if one can’t be found. For me personally, I found this to be too naggy.
        set DEFAULT_PLAYER_COMMAND=vlc.exe                                                             %+ rem UPDATE THIS IN GET-LYRICS TOO! ——> program we use to play audio files, i.e. VLCplayer, MPC, etc.
        set DEFAULT_PLAYER_COMMAND=call preview-audio-file                                             %+ rem Command to run to play files with a media player
        set OUR_LANGUAGE=en                                                                            %+ rem May need to set this to something else if your collection’s primarily language isn’t English                          
        set LOG_PROMPTS_USED=1                                                                         %+ rem 1=save prompt used to create SRT into sidecar ..log file
        set SKIP_SEPARATION=1                                                                          %+ rem 1=disables the 2023 process of separating vocals out, a feature that is now built in to Faster-Whisper-XXL, 0=run old code that probably doesn’t work anymore
        SET SKIP_TXTFILE_PROMPTING=0                                                                   %+ rem 0=use lyric file to prompt AI, 1=go in blind
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
        set PROMPT_EDIT_CONSIDERATION_TIME=20                                                          %+ rem wait time for “do you want to edit the AI prompt”-type questions
        set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=0                                         %+ rem wait time for “hey lyrics not found!”-type notifications/questions. Set to 0 to not pause at all.
        set WHISPERTIMESYNC_QUERY_WAIT_TIME=300
        set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=120                                                  %+ rem wait time for “edit it now that we’ve made it?”-type questions ... Have decided it should probably last longer than the average song
        set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=1200                                                 %+ rem wait time for “edit it now that we’ve made it?”-type questions ... Have decided it should probably last longer than the average song
        set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME=600                                                  %+ rem wait time for “edit it now that we’ve made it?”-type questions ... Have decided it should probably last longer than the average song
        set EDIT_KARAOKE_AFTER_FORCE_REGEN_WAIT_TIME=12                                                %+ rem wait time for “edit it now that we’ve made it?”-type questions when we are in force-regen mode
        set KARAOKE_APPROVAL_WAIT_TIME=60                                                              %+ rem wait time for “Approve karaoke file” prompt after creating karaoke
        set AI_GENERATION_ANYWAY_DEFAULT_ANSWER=no                                                     %+ rem default answer for “Generate AI anyway?”-type questions


REM config: 2023:
        rem set TRANSCRIBER_TO_USE=call whisper-faster.bat 
        rem set SKIP_SEPARATION=0         
        rem SET SKIP_TXTFILE_PROMPTING=0  
REM OLD 2023 USAGE:
        rem    Not sure if applicable with 2024 version: :USAGE: lrc.bat whatever.mp3 keep  {keep vocal files after separation}
        rem    Not sure if applicable with 2024 version: :USAGE: lrc.bat last               {quick retry again at the point of creating the lrc file —— separated vocal files must already exist}


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

rem Set filemask to match audio files:
        iff not defined filemask_audio then
                set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        endiff

REM validate environment [once]:
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
                        if not defined ANSI_COLOR_BRIGHT_YELLOW                    set ANSI_COLOR_BRIGHT_YELLOW=%@CHAR[27][93m
                        if not defined ANSI_COLOR_ORANGE                           set ANSI_COLOR_ORANGE=%@CHAR[27][38;2;235;107;0m
                        rem TODO BLINK_ON, BLINK_OFF ITALICS_ON ITALICS_OFF, QUOTE, etc
                rem Perform the actual validations:
                        @call validate-in-path              %TRANSCRIBER_TO_USE% get-lyrics.bat  debug.bat  lyricy.exe  copy-move-post  paste.exe  divider  less_important  insert-before-each-line  bigecho  deprecate  errorlevel  grep  isRunning fast_cat  top-message  top-banner  unlock-top  status-bar.bat footer.bat unlock-bot deprecate.bat  add-ADS-tag-to-file.bat remove-ADS-tag-from-file.bat display-ADS-tag-from-file.bat display-ADS-tag-from-file.bat review-subtitles.bat  error.bat print-message.bat  get-lyrics-for-file.btm delete-bad-ai-transcriptions.bat subtitle-postprocessor.pl lyric-postprocessor.pl success.bat alarm.bat  WhisperTimeSync.bat WhisperTimeSync-helper.bat
                        @call validate-environment-variable  TRANSCRIBER_PDNAME  skip_validation_existence
                        @call validate-environment-variables FILEMASK_AUDIO COLORS_HAVE_BEEN_SET QUOTE emphasis deemphasis ANSI_COLOR_BRIGHT_RED check check party_popper emoji_birthday_cake red_x ansi_color_bright_Green ansi_color_Green ANSI_COLOR_NORMAL ansi_reset cursor_reset underline_on underline_off faint_on faint_off EMOJI_FIREWORKS star check emoji_warning ansi_color_warning_soft ANSI_COLOR_BLUE UnicodeOutputDefault bold_on bold_off ansi_color_blue machinename emoji_ear emoji_microphone emdash ansi_color_warning_fg
                        @call validate-is-function           ansi_randfg_soft randfg_soft ANSI_CURSOR_CHANGE_COLOR_WORD                
                        @call validate-plugin                StripANSI
                        @call checkeditor
                        @set VALIDATED_CREATE_LRC_FF=1
        endiff

                        





REM branch on certain paramters, and clean up various parameters 
        rem %1 "last" is a very unique situation:
        echo %ansi_color_red% if "%@UNQUOTE[%1]" == "last" (goto /i actually_make_the_lrc) >nul
        echo %@ansi_randfg_soft[][AAA1] %%1$ is %1$ >nul
        if "%1" == "last" (goto /i actually_make_the_lrc) %+ rem to repeat the last regen
        rem %1 was unique. Now we do the normal stuffs:

        rem ENVIRONMENT-ONLY parameters:               
        if defined USE_LANGUAGE (set OUR_LANGUAGE=%USE_LANGUAGE%)

        rem If the next parameter is special, we must grab it and shift again so the rest properly reaches Whisper:
        REM default modes:
        set FAST_MODE=0 
        set SOLELY_BY_AI=0
        set FORCE_REGEN=0 
        set CLEANUP=0 
        set AUTO_LYRIC_APPROVAL=0
        set LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE=0
        set ALREADY_HAND_EDITED=0
        set JUST_RENAMED_TO_INSTRUMENTAL=0
        set PROMPT_ANALYSIS_ONLY=0
        set CHIPTUNE_ENCOUNTERED=0
        unset /q karaoke_status

        iff "%CONSIDER_ALL_LYRICS_APPROVED%" == "1" then
                set AUTO_LYRIC_APPROVAL=1
                rem This is deprecated/testing only and we don’t want it to persist:
                unset /q CONSIDER_ALL_LYRICS_APPROVED   
        endiff                

        echo %@ansi_randfg_soft[][BBB1] %%1$ is %1$ >nul
        
        :process_for_mode_variants
        rem %1 is the filename, but %2+++ can be various options to pull off, while the rest is to go to Whisper/our transcriber
        rem iff "%2" == "ai" .or. "%2" == "fast" .or. "%2" == "redo" .or. "%2" == "force-regen" .or. "%2" == "cleanup" then
        echos %ANSI_COLOR_MAGENTA%
        rem echo tail is %1$
        rem echo  one is %1
        set TMP_PARAM_1=%1
        rem echo TMP_PARAM_1 is “%TMP_PARAM_1%”
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


REM Determine the base text used for our window title:
        set BASE_TITLE_TEXT=%FILE_ARTIST - %FILE_TITLE% 

REM Determine our expected input and output files:
        unset /q INPUT_FILE
        set INPUT_FILE=%SONGFILE%
        rem EXPECTED_OUTPUT_FILE=%LRC_FILE%   %+ rem //This was for the 2023 version
        SET EXPECTED_OUTPUT_FILE=%SRT_FILE%



rem Make sure it’s a transcribeable filename:
        rem echo α 100
        gosub validate_transcribeable_filename "%INPUT_FILE%" "transcribing"
        if "%_?" == "666" .or. "%retval%" == "666" .or. "1" == "%goto_end%" (
                rem echo Aborting...
                goto /i The_Very_Very_END
        )
        goto skip_sub_414
                                :validate_transcribeable_filename [input_file verb]
                                        rem Debug:
                                                rem echo %ansi_color_debug%-DEBUG: called validate_transcribeable_filename [input_file=%input_file% verb=%verb%]%ansi_color_normal%

                                        rem Failure flag:
                                                set fail=0

                                        rem Make our filename checks:                                                                           //NOTE: A redundant check occurs later but shoudl no longer happen, and looks like this: if "%@REGEX[instrumental,%INPUT_FILE%]" == "1" (@call warning "Sorry, nothing to transcribe because this appears to be an instrumental: %INPUT_FILE%" silent %+ goto :END)
                                                set chipt_in_filename=%@REGEX["\[[cC][hH][iI][pP][tT][uU][nN][eE][sS]*\]",%INPUT_FILE%]
                                                set chipt_in_foldname=%@REGEX["\\[cC][hH][iI][pP][tT][uU][nN][eE][sS]*\\",%@FULL["%INPUT_FILE%"]]
                                                set instr_in_filename=%@REGEX["[^\-][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][\)\]]",%INPUT_FILE%]
                                                set instr_in_foldname=%@REGEX["[\[\(][iI][nN][sS][tT][rR][uU][mM][eE][nN][tT][aA][lL][sS]*[\)\]]",%@FULL["%INPUT_FILE%"]]
                                                set sndfx_in_filename=%@REGEX["[\[\(][sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*[\)\]]",%INPUT_FILE%]
                                                set sndfx_in_foldname=%@REGEX["[sS][oO][uU][nN][dD] [eE][fF][fF][eE][cC][tT][sS]*\\",%@FULL["%INPUT_FILE%"]]

                                        rem These definitely happen in this order for the reason of error message precedence:
                                                unset /q fail_type fail_point
                                                if "1" == "%instr_in_filename%" ( set fail_type=instrumental  %+ set fail_point=filename) 
                                                if "1" == "%chipt_in_filename%" ( set fail_type=chiptune      %+ set fail_point=filename)
                                                if "1" == "%sndfx_in_filename%" ( set fail_type=sound effects %+ set fail_point=filename)
                                                if "1" == "%instr_in_foldname%" ( set fail_type=instrumental  %+ set fail_point=dir name)
                                                if "1" == "%chipt_in_foldname%" ( set fail_type=chiptune      %+ set fail_point=dir name)
                                                if "1" == "%sndfx_in_foldname%" ( set fail_type=sound effects %+ set fail_point=dir name)

                                        rem Debug stuffs:
                                                goto :debug_406_no
                                                goto :debug_406_yes
                                                     :debug_406_yes
                                                        echo chipt_in_foldname == “%chipt_in_foldname%”
                                                        echo instr_in_filename == “%instr_in_filename%”
                                                        echo sndfx_in_filename == “%sndfx_in_filename%”
                                                        echo chipt_in_filename == “%chipt_in_filename%”
                                                        echo instr_in_foldname == “%instr_in_foldname%”
                                                        echo sndfx_in_foldname == “%sndfx_in_foldname%”
                                                        echo fail_type         == “%fail_type%”
                                                        echo fail_point        == “%fail_point%”
                                                :debug_406_no

                                        rem Notify of error and quit if applicable:
                                                if "" == "%fail_type%" goto :we_are_fine_403 %+ rem else:
                                                        unset /q strN
                                                        if "%fail_type%" == "instrumental" set strN=n
                                                        echo %ansi_color_warning%%no% Sorry! Not %italics_on%%verb%%italics_off% because this %italics_on%%fail_point%%italics_off% indicates a%strN% %ansi_resetNOLETSNOTDOTHAT%%ansi_color_red%%ansi_color_warning_bg_soft%%italics_on%%blink_on%%fail_type%%blink_off%%italics_off%%ANSI_COLOR_WARNING% file:%ansi_color_normal% %faint_on%“%@UNQUOTE["%INPUT_FILE%"]”%faint_off%%ansi_color_normal%
                                                        set fail=1
                                                :we_are_fine_403

                                        rem Return success/fail:
                                                if "1" == "%fail%" (return 666)
                                                if "1" != "%fail%" (return 777)
                                return

                
        :skip_sub_414


rem Do subtitles exist?
        if exist "%EXPECTED_OUTPUT_FILE%" .and. "1" !=  "%FORCE_REGEN%" (
                rem echo exp output file exists!
                rem echo %big_Top%%ansi_color_warning_soft%%star2%%star2% Karaoke already exists!%ansi_color_normal%
                rem echo %big_bot%%ansi_color_warning_soft%%star2%%star2% Karaoke already exists!%ansi_color_normal%
                echo %big_top%%ansi_color_warning_soft%%star2% Karaoke already exists!%ansi_color_normal%%big_off%
                echo %big_bot%%ansi_color_warning_soft%%star2% Karaoke already exists!%ansi_color_normal%%big_off%
                gosub divider
                rem set goto_end=1
                goto /i END
        ) else (
                rem echo exp output file does not exist! 
                rem echo goto_end == "%goto_end%" 
        )
        if "1" == "%goto_end%" goto /i END
        REM echo if exist "%POTENTIAL_LYRIC_FILE%" 
        if exist "%POTENTIAL_LYRIC_FILE%" (
                rem gosub refresh_lyric_status "%POTENTIAL_LYRIC_FILE%"
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: POTENTIAL_LYRIC_FILE file exists! - %lq%%POTENTIAL_LYRIC_FILE%%rq%%ANSI_COLOR_NORMAL% (status=%lq%%LYRIC_STATUS%%rq%)
        ) else (
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: POTENTIAL_LYRIC_FILE file does not exist! - %lq%%POTENTIAL_LYRIC_FILE%%rq%%ANSI_COLOR_NORMAL%
        )

               
rem If the file has been marked as failed previously, abort (unless in force mode):
        rem echo α 200
        unset /q failure_ads_result
        set  failure_ads_result=%@EXECSTR[type "%@UNQUOTE["%INPUT_FILE%"]:karaoke_failed"  >>&>nul] 
        REM echo failure_ads_result is “%failure_ads_result%”, force_regen=“%force_regen%”
        iff "True" == "%failure_ads_result%" .and. "1" != "%FORCE_REGEN%" .and. "1" != "%PROMPT_ANALYSIS_ONLY%" then
                gosub divider
                @call warning "Sorry, this file has failed in transcription, and won’t be tried again without the “force” parameter being used: %faint_on%%INPUT_FILE%%faint_off%" silent 
                gosub divider
                goto /i END
        endiff

REM Values fetched from input file:
        :initial_probing
        rem echo solely_by_ai is %solely_by_ai% %+ pause
        rem echo α 300
        if "1" == "%SOLELY_BY_AI%" .and. "1" != "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" (
                set PROMPT_CONSIDERATION_TIME=3
                set PROMPT_EDIT_CONSIDERATION_TIME=3
        )
        set song_probed_via_call_from_create_srt=0
        iff "1" != "%SOLELY_BY_AI%" then
                echo %ansi_color_unimportant%🐐 %@cool[calling get-lyrics-for-file] [111] - CALLING %@colorful_string[━━━━━━━━━━━━━━━━(to probe the file)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] CWP=%_CWP
                call get-lyrics-for-file "%SONGFILE%" SetVarsOnly %+ rem probes the song file and sets FILE_ARTIST / FILE_TITLE / etc
                set song_probed_via_call_from_create_srt=1
                echo %ansi_color_unimportant%🐐 return: %@cool[get-lyrics-for-file] [111] - RETURNED %@colorful_string[━━━━━━━━━━━━━━━(after file probing)━━━━━━━━━━━━━━ CWP=%_CWP] 
                if "%_CWD\" != "%SONGDIR%" (*cd "%SONGDIR%")
                set last_file_probed=%SONGFILE%                               %+ rem prevents get-lyrics from probing twice
        else
                set song_probed_via_call_from_create_srt=0
                unset /q FILE_TITLE
        endiff



REM Chiptune stuff:
        rem call debug "CHIPTUNE_ENCOUNTERED is “%CHIPTUNE_ENCOUNTERED%”"
        if "1" == "%CHIPTUNE_ENCOUNTERED%" goto /i END



REM Lyric file stuffs:
        rem echo α 400
        set sidecar_was_present_from_the_start=0
        iff not exist "%POTENTIAL_LYRIC_FILE%" then
                echo Lyrics don’t exist ... PROMPT_ANALYSIS_ONLY=%PROMPT_ANALYSIS_ONLY% .. goatgoatgoat ... so if we are in prompt analyais mode we shoudl actually goto /i END !!
        endiff
        if not exist "%POTENTIAL_LYRIC_FILE%" goto /i end_of_potential_lyric_file_initial_processing
                set TXT_FILE=%@UNQUOTE["%POTENTIAL_LYRIC_FILE%"]
                echos %STAR%%ANSI_COLOR_IMPORTANT% Checking lyrics at %faint_on%%italics_on%%lq%%TXT_FILE%%rq%%italics_off%%faint_off%...%ansi_color_normal%
                gosub refresh_lyric_status "%TXT_FILE%"
                if "%LYRIC_STATUS%" == "APPROVED" (
                        echo %ansi_color_bright_green%...%italics_on%and they are %blink_on%approved%blink_off%!%italics_off%%ansi_color_normal%
                        set sidecar_was_present_from_the_start=1
                        set LYRIC_FILE=%TXT_FILE%
                        goto /i AI_generation 
                ) else (
                        echo %ansi_color_bright_red%...but it is not approved!%ansi_color_normal%
                        goto /i AI_generation 
                )
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
        iff exist "%@UNQUOTE[%MAYBE_SRT_1%]" .or. exist "%@UNQUOTE[%MAYBE_SRT_2%]" then
                if exist "%@UNQUOTE[%MAYBE_SRT_2%]" set found_subtitle_file=%@UNQUOTE["%MAYBE_SRT_2%"]
                if exist "%@UNQUOTE[%MAYBE_SRT_1%]" set found_subtitle_file=%@UNQUOTE["%MAYBE_SRT_1%"]
                gosub divider
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%   
                call bigecho      "%ansi_color_warning_soft%%star2% Already have the karaoke!%ansi_reset%"
                call warning_soft "Pre-existing transcription found in lyric repository at: “%emphasis%%italics_on%%found_subtitle_file%%deemphasis%%italics_off%”" silent
                iff exist "%found_subtitle_file%"" then
                        call review-file  "%found_subtitle_file%"
                else
                        call warning "found subtitle file of “%found_subtitle_file%” doesn’t exist"
                endiff
                call warning_soft "Pre-existing transcription found in lyric repository at: “%emphasis%%italics_on%%found_subtitle_file%%deemphasis%%italics_off%”" silent
                echo %STAR% %ANSI_COLOR_ADVICE%Copy this file %italics_on%from our local repo%italics_off% into this folder, as a sidecar file for %@NAME[%SONGFILE%]%ansi_color_normal%
                rem You’d think the answer would be yes, but actually, every live version of a song does NOT want the LRC/SRT for the studio version instead!
                rem Sadly, these must be rejected unless explicitly accepted...
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
                        rem echo GOAT displayaudiofilename 06
                        gosub DisplayAudioFileName
                        call  AskYN "Do these still look acceptible [%ansi_color_bright_green%H%ansi_color_prompt%=hand-edit,%ansi_color_bright_green%I%ansi_color_prompt%=Instrumental(%ansi_color_bright_green%X%ansi_color_prompt%=All)]" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME% HIX H:Yes_but_hand-_edit_them,I:Rename_as_instrumental,X:rename_all_the_files_as_instrumentals %+ rem borrowed wait time

                        iff "%ANSWER%" == "I" then
                                gosub rename_audio_file_as_instrumental
                        endiff
                        iff "%ANSWER%" == "N" then
                                call disapprove-subtitle-file "%target%"
                                call askYN "Delete file “%target%”" yes %PROCEED_WITH_AI_CONSIDERATION_TIME% %+ rem borrowed wait time
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
        endiff
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


REM if we already have a SRT file, we have a problem:
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
                        @call askYN "%conceal_on%22%conceal_off%Regenerate it anyway? %faint_on%[“no” will mark karaoke as %italics%approved%italics_off%]%faint_off%" no %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME%
                endiff
                set GOTO_END=0
                set GOTO_FORCE_AI_GEN=0
                
                iff "%ANSWER%" == "Y" .or. "1" == "%FORCE_REGEN%" then
                        iff exist "%SRT_FILE%" then
                                ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak" >nul
                        endiff
                        set OKAY_THAT_WE_HAVE_SRT_ALREADY=1

                        rem TODO show lyrics again?
                        
                        set DEFAULT_ANSWER_FOR_THIS=no
                        call get-lyric-status "%TXT_FILE%"

                        if "1" == "%AUTO_LYRIC_APPROVAL%" .or. "%LYRIC_STATUS%" == "APPROVED" (set DEFAULT_ANSWER_FOR_THIS=no)
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
                                      call review-file -wh  "%LRC_FILE%"
                                     @call AskYN   "Mark LRC file as %italics_on%approved%italics_off%" no %EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME%
                                     if "%ANSWER%" == "Y" call approve-subtitles "@UNQUOTE[%LRC_FILE%]"
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
   
        rem not exist "%TXT_FILE%" .and.  1  ne  %FORCE_REGEN%  .and.  1  eq  %LYRIC_ATTEMPT_MADE   then
        rem not exist "%TXT_FILE%" .and.  1  ne  %FORCE_REGEN%                                      then
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

rem Mandatory review of lyrics 
        :mandatory_review_of_lyrics
        rem echo α 1500.20.1 ━━ mandatory_review_of_lyrics
        iff exist "%TXT_FILE%" .and. %@FILESIZE["%TXT_FILE%"] gt 0 then
                rem Deprecating this section which is redundant because it’s done in get-lyrics:
                        iff 0 == 1 then
                                                        call review-file -wh -st  "%TXT_FILE%" "Review the lyrics now"
                                                        @gosub divider
                                                        gosub DisplayAudioFileName
                                                        @call AskYn "[REDUNDANT?] Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                                                        iff "%ANSWER%" == "N" then
                                                                %color_removal%
                                                                ren  /q "%TXT_FILE%" "%TXT_FILE%.%_datetime.bak"
                                                                %color_normal%
                                                                @call warning "Aborting because you don’t find the lyrics acceptable"
                                                                @call advice  "To skip lyrics and transcribe using only AI: %blink_on%%0 “%$ ai”%blink_off%"
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
        echo ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇  AI generation: go! ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ ❇ 
        rem >nul


REM if a text file of the lyrics exists, we need to engineer our AI transcription prompt with it to get better results
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
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True 
        rem Alas, completely disabling VAD filter results in major major major hallucinations during silence... Let’s try turning it on again, sigh.
        rem 10v2: gave "unrecognized arguments: --vad_filter_threshold=0.2" oops it should be vad_threshold not vad_filter_threshold plus we had accidentally left vad_filter=False
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.2   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v3:                                                                                                                                                                                                                                                                                                      
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.2   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v4:  lowering vad_threshold from 0.2 to 0.1 because of metal & punk with fast/hard vocals. May increase hallucations tho                                                                                                                                                                                 
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 11:  adding --best_of 5  and --vad_alt_method=pyannote_v3 & removed --ff_mdx_kim2 but this clearly gave worse lyrics, terrible ones, with Wet Leg – Girlfriend                                                                                                                                             
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20               --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --vad_alt_method=pyannote_v3 
        rem 12:  going back to original --ff_mdx_kim2 vocal separation but keeping the best_of 5 ... Looks great?                                                                                                                                                                                                      
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --vad_alt_method=pyannote_v3 
        rem 12v2:  reordering                                                                                                                                                                                                                                                                                          
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5
        rem 13: adding --max_comma_cent 70                                                                                                                                                                                                                                                                             
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70
        rem 14: adding -hst 2 via Purview’s advice to stop the thing where one subtitle gets stuck on for a whollleeee solooooo — it is short for --hallucination_silence_threshold  ... But it absolutely 100% does not solve that problem and gives output that causes concern for discarded lyrics. Have added logging the whisper output [and not just prompt] to the logfile to help track this...
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70               -hst 2 
        rem 15: adding --max_gap 3.0 — Purfview said there is a --max_gap option -- default is 3.0 but i’m getting gaps way larger than that so I don’t think it’s being enforced so i’m going to explicitly add it                                                                                                     
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 3.0 -hst 2 
        rem 16b: adding --max_gap 3.0 — Purfview said there is a --max_gap option -- default is 3.0 but i’m getting gaps way larger than that so I don’t think it’s being enforced so i’m going to explicitly add it                                                                                                    
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 3.0 
        rem 17: try shortening max_gap ———————— FINALLY VERY VERY GOOD RESULTS!!!! ————————                                                                                                                                                                                                                             
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 17b: dropping %PARAM_2% business ━━ 🌟 🌟 🌟 🌟 🌟 🌟 This prompt ran for 5,000+ songs!!!!!! 🌟 🌟 🌟 🌟 🌟 🌟                                                                                                                                                                                               
        set CLI_OPS=--model=large-v2           %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1   --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 18: But then we hit Gwar: Bloody Pit Of Horror Pt 2, that had very low-talking words, and WhisperAI could *NOT* get it right. It just couldn’t.  Not until the vad threshold was lowered...                                                                                                                     
        rem 18: 202501xx: lowering --vad_filter Threshold for the 1ˢᵗ time since v10
        set CLI_OPS=--model=large-v2           %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.05  --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 
        rem 19: 20250219: raising --vad_filter Threshold back up to halfway between what we had for a long time, and what we recently lowered it to. There’s some wonkyness sometimes and we’re just not sure if it may be caused by this. Mostly going on gut feeling from observing it churn and churn and churn.
        set CLI_OPS=--model=large-v2           %3$ --language=%OUR_LANGUAGE% --output_dir "%OUTPUT_DIR%" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.075 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 

        set PROMPT_VERSION=19 %+ rem used in log files

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
        rem         Lower the VAD threshold to 0.35 or 0.3 to capture more detail. [I had to go to 0.1 for most songs in a punk/metal/industrial collection, and then even 0.05 after that]
        rem --vad_filter_off
        rem         Disable VAD filtering with --vad_filter_off to ensure the whole audio is processed without aggressively skipping sections.
        rem --max_comma_cent 70
        rem         Roughly, break the subtitle at a comma... I think 70 is if it’s 70% through the line but i’m probably wrong
        rem NOTE: We also have --batch_recursive - {automatically sets --output_dir} but you can’t prompt each file with individual lyrics that way


        if "1" == "%AUTO_LYRIC_APPROVAL%" goto /i use_text
        if not exist %TXT_FILE% .or. "1" == "%SKIP_TXTFILE_PROMPTING%" .or. ("1" == "%SOLELY_BY_AI%" .and. "1" != "%AUTO_LYRIC_APPROVAL%") goto /i endiff_no_text_1017
                :use_text

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

                        rem The newer way: Letting the lyric postprocessor pen up the file directly:
                                lyric-postprocessor.pl -A -1 -L "%@UNQUOTE["%TXT_FILE%"]" >:u8 %tmppromptfile%

                rem Safely ingest postprocessed lyrics into environment variable:
                        *setdos /x-25
                        set OUR_LYRICS_3a=%@EXECSTR[type %tmppromptfile%]
                        set OUR_LYRICS_3=%@unquote["%@LEFT[%MAXIMUM_PROMPT_SIZE%,"%our_lyrics_3a"]"]
                        setdos /x0
                        rem echo our_lyrics_1=“%OUR_LYRICS_TRUNCATED%”
                        rem echo our_lyrics_2=“%our_lyrics_2%”
                        rem echo our_lyrics_3=“%our_lyrics_3%”

                rem Add the lyrics to our existing whisper prompt:
                        *setdos /x-5
                        set WHISPER_PROMPT=--initial_prompt "%OUR_LYRICS_3%"
                        setdos /x0
                        rem @echo %ANSI_COLOR_DEBUG%Whisper_prompt is:%newline%%tab%%tab%%faint_on%%WHISPER_PROMPT%%faint_off%%ANSI_COLOR_NORMAL%

                rem Leave a hint to future-self, because we definitely do "env whisper" to look into the environment to find the whisper prompt last-used, for when we want to do minor tweaks... And remembering --batch_recursive is hard 😂
                        set WHISPER_PROMPT_ADVICE_NOTE_TO_SELF______________________________=*********** FOR RECURSIVE: do %%whisper_prompt%% but instead of the filename do --batch_recursive *.mp3

                rem Preface our whisper prompt with our hard-coded default command line options from above:
                        *setdos /x-5
                        set CLI_OPS=%CLI_OPS% %WHISPER_PROMPT%
                        setdos /x0


                setdos /x0
        :endiff_no_text_1017
        :No_Text
        rem if "1" == "%goto_end%" goto /i END

        

rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////
REM        REM demucs vocals out (or not——we don’t do this in 2024):
REM                                        if %SKIP_SEPARATION eq 1 (goto /i Vocal_Separation_Skipped)
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
        if "1" == "%DELETE_BAD_AI_TRANSCRIPTIONS_FIRST%" call delete-bad-ai-transcriptions 3

REM does our input file exist?
        if not exist "%@UNQUOTE[%INPUT_FILE%]" call validate-environment-variable  INPUT_FILE

REM Assemble the full command-line to transcribe the file:
        *setdos /x-5
        set LAST_WHISPER_COMMAND=%TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%"    
        setdos /x0


REM Log the prompt we generated for analysis:
        echo %newline%%newline%%newline%%newline%%emoji_ear%%emoji_microphone% %_datetime ━━━━━━ %INPUT_FILE% ━━━━━━ PROMPT: %LAST_WHISPER_COMMAND% >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"
                          echo %newline%%newline%%emoji_ear%%emoji_microphone% %_datetime ━━━━━━ %INPUT_FILE% ━━━━━━ LYRICS: %OUR_LYRICS_3%         >>:u8"%AUDIOFILE_TRANSCRIPTION_PROMPTS_USED_LOG_FILE%"


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
                        set ADDITIONAL_OPTIONS_TEXT= [%ansi_color_bright_green%P%ansi_color_prompt%=Play,%ansi_color_bright_green%L%ansi_color_prompt%=mark lyricless%underline_on%ness%underline_off%,%ansi_color_bright_green%I%ansi_color_prompt%=Instr,%ansi_color_bright_green%K%ansi_color_prompt%=skip,%ansi_color_bright_green%G%ansi_color_prompt%=get lyrics]
                        set ADDITIONAL_OPTIONS_LETTERS=GIKLP
                        set ADDITIONAL_OPTIONS_MEANINGS=L:Mark_as_lyricless!,P:play_the_file,I:mark_as_instrumental
                else
                        set ADDITIONAL_OPTIONS_TEXT= [%ansi_color_bright_green%P%ansi_color_prompt%=Play,%ansi_color_bright_green%I%ansi_color_prompt%=instr,%ansi_color_bright_green%K%ansi_color_prompt%=skip,%ansi_color_bright_green%G%ansi_color_prompt%=get lyrics]
                        set ADDITIONAL_OPTIONS_LETTERS=GIKP
                        set ADDITIONAL_OPTIONS_MEANINGS=P:preview_the_file,I:mark_as_instrumental
                endiff
        :determine_dynamic_prompt_options_end


rem Ask if we should proceed:
        if "%LYRIC_STATUS%" == "APPROVED" .and. "1" != "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" set PROCEED_WITH_AI_CONSIDERATION_TIME=9
        :proceed_prompt
        @call AskYn "Proceed with this AI generation%ADDITIONAL_OPTIONS_TEXT%" yes %PROCEED_WITH_AI_CONSIDERATION_TIME% %ADDITIONAL_OPTIONS_LETTERS% %ADDITIONAL_OPTIONS_MEANINGS%
                set STORED_ANSWER=%ANSWER%                                                                                     %+ rem echo stored_answer is “%stored_answer” %+ pause %+ echo on
                rem “K”:
                        if  "%STORED_ANSWER%" == "K" goto /i END
                rem “G”:
                        gosub check_for_answer_of_G "%INPUT_FILE%"
                        if  "%STORED_ANSWER%" == "G" goto /i initial_probing
                rem “I”:
                        iff "%STORED_ANSWER%" == "I" then
                                gosub check_for_answer_of_I "%INPUT_FILE%"
                                @call warning "Aborting because you marked it as an instrumental..."
                                gosub divider
                                goto /i END
                        endiff
                rem “P”:
                        set answer=%STORED_ANSWER%
                        gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%INPUT_FILE%"
                        if  "%STORED_ANSWER%" == "P" goto /i  proceed_prompt
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



REM quick chance to edit prompt:
        :edit_ai_prompt
        @call AskYn "Edit the AI prompt" no %PROMPT_EDIT_CONSIDERATION_TIME%
        iff "%answer%" == "Y" (call eset-alias LAST_WHISPER_COMMAND quick)


REM Updated Concurrency Check: wait on lock file
        gosub :lockfile_wait_on_transcriber_lock_file 


REM Original Concurrency Check: Check if the encoder is already running in the process list. Don’t run more than 1 at once.
        rem slower call isRunning %TRANSCRIBER_PRNAME% silent
        rem slower if "%isRunning" != "1" (goto /i no_concurrency_issues)
        rem faster:
        rem echo %ANSI_COLOR_DEBUG%- DEBUG: (4) iff @PID[TRANSCRIBER_PDNAME=%TRANSCRIBER_PDNAME%] %@PID[%TRANSCRIBER_PDNAME%] ne 0 then %ANSI_COLOR_NORMAL%
        set CONCURRENCY_WAS_TRIGGERED=0        
        iff "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then
                @echo %ansi_color_warning_soft%%star% %italics_on%%TRANSCRIBER_PDNAME%%italics_off% is already running%ansi_color_normal%
                @echos %ANSI_COLOR_WARNING_SOFT%%STAR% Waiting for completion of %italics_on%another%italics_on% instance of %italics_on%%@cool[%TRANSCRIBER_PDNAME%]%italics_off% %ansi_color_warning_soft%to finish before starting this one...%ANSI_COLOR_NORMAL%
                set CONCURRENCY_WAS_TRIGGERED=1
        else 
                goto /i :no_concurrency_issues
        endiff

        :Check_If_Transcriber_Is_Running_Again
                rem Echo a random-colored dot:
                        @echos %@randfg_soft[].

                rem Wait a random number of seconds to lower the odds of multiple waiting processes seeing an opening and all starting at the same time]:
                        call sleep.bat %@random[7,29]        
                        if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i Check_If_Transcriber_Is_Running_Again

                rem When finally done, echo a green “...”:
                        @echo %ansi_color_green%...%ansi_color_bright_green%Done%blink_on%!%blink_off%%ansi_reset%
        :no_concurrency_issues
        
REM set a non-scrollable header on the console to keep us from getting confused about which file / what we’re doing / etc
        rem call top-message Transcribing %FILE_TITLE% by %FILE_ARTIST%
        set LOCKED_MESSAGE_COLOR_BG=%@ANSI_BG[0,0,64]                               %+ rem copied from top-banner/status-bar.bat
        iff not defined FILE_ARTIST .and. "1" != "%SOLELY_BY_AI%" .and. "APPROVED" != "%LYRIC_STATUS%" then
            call warning_soft "%italics_on%FILE_ARTIST%italics_on% is not defined here and %italics_on%generally%italics_off% should be, particularly because %underline_on%SOLELY_BY_AI%underline_off%=“%SOLELY_BY_AI%” [lyric_status=“%lyric_status%”]"
            set FILE_ARTIST= ``
            rem It turns out that it’s okay most of the time, so better not get 
            rem                all hung up about it with a mandatory interacton:
            if "1" == "%INSIST_ON_HAVING_ARTIST%" call eset-alias FILE_ARTIST quick
        endiff                                                    
        echo %ansi_color_debug%-DEBUG: FILE_TITLE is “%FILE_TITLE%” / FILE_ARTIST is “%FILE_ARTIST%” / INPUT_FILE is “%INPUT_FILE%”%ansi_color_normal% 
        rem >nul
        if "%FILE_ARTIST%" ==  " " unset /q FILE_ARTIST


        unset /q banner_song
                iff         "" != "%FILE_TITLE%" .or. "" != "%FILE_ARTIST%" then
                        if "" != "%FILE_TITLE%"  set banner_song= %faint_off%“%italics_on%%FILE_TITLE%%italics_off%”
                        if "" != "%FILE_ARTIST%" set banner_song=%banner_song% by %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%blink_on%%@cool[%FILE_ARTIST%]%blink_off%
                else
                         set banner_song= “%@NAME["%INPUT_FILE%"]”
                endiff

        call debug "Banner_song is “%banner_song%” GOAT"

        unset /q banner_message
        rem set  banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%ZZZZZZZZ%AI-Transcribing%faint_off% %ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%“%italics_on%%FILE_TITLE%%italics_off%” %faint_on%%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%by%faint_off% %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%ZZZZZZZZ%%@cool[%FILE_ARTIST%]%%ZZZZZZZZZ%
        rem set  banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%faint_on%%ansi_color_normal%%@ANSI_BG[0,0,64]AI–Transcribing%faint_off%%ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%%@IF["" != "%FILE_TITLE%" .and. "" != "%FILE_ARTIST%", %@NAME["%INPUT_FILE%"],]%@IF["" != "%FILE_TITLE%", “%italics_on%%FILE_TITLE%%italics_off%”,]%LOCKED_MESSAGE_COLOR_BG%%@IF["" != "%FILE_ARTIST%", %@randfg_soft[]%faint_on%by%faint_off% %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%blink_on%%@cool[%FILE_ARTIST%]%%blink_off%,]
        set      banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%faint_on%%ansi_color_normal%%@ANSI_BG[0,0,64]AI–Transcribing%faint_off%%ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%%banner_song%

        rem echo about to call status-bar "%banner_message%" ... %+ pause
        call status-bar "%banner_message%"
        gosub divider


REM  ✨ ✨ Get ready to actually generate the SRT file [used to be LRC but we have now coded specifically to SRT] —— start AI: ✨ ✨ 
REM  ✨ ✨ ✨ Concurrency checks: ✨ ✨ ✨ 
        rem One last concurrency check:
                iff "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then
                        echo %ANSI_COLOR_WARNING% Actually, it’s still running! %ANSI_RESET%
                        goto /i :Check_If_Transcriber_Is_Running_Again
                else
                        rem One last extra random wait in case 2 different ones get here at the same time. 
                        rem (And only do this if we already had to wait before):
                                if "%CONCURRENCY_WAS_TRIGGERED%" == "1" call sleep.bat %@random[7,29]                    
                endiff

        rem Determine log file name:
                set OUR_LOGFILE=%@NAME[%@UNQUOTE[%INPUT_FILE]].log

        rem A 3rd concurrency check became necessary in my endeavors:
                if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto /i Check_If_Transcriber_Is_Running_Again %+ rem yes, a 3rd concurrency check at the very-very last second!

REM  ✨ ✨ ✨ Concurrency checks: ✨ ✨ ✨ 
        gosub :lockfile_create_transcriber_lock_file 


REM  ✨ ✨ ✨ ✨ ✨ ✨ LOG WHAT WE’RE DOING: ✨ ✨ ✨ ✨ ✨ ✨         [and window title too]
                title %EMOJI_EAR%%BASE_TITLE_TEXT%
                iff  "%LOG_PROMPTS_USED%" == "1" then
                        @echo %@REPEAT[%newline%,2]%EMOJI_EAR% %_DATETIME: prompt v%PROMPT_VERSION%: %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%" >>:u8"%OUR_LOGFILE%"
                        @echo %@REPEAT[%newline%,0]%EMOJI_EAR% %_DATETIME: prompt v%PROMPT_VERSION%: %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%" >>:u8"%AUDIOFILE_TRANSCRIPTION_LOG_FILE%"
                        @echo %@REPEAT[%newline%,4]%EMOJI_EAR% %_DATETIME: filename:  %INPUT_FILE%                                                     >>:u8"%AUDIOFILE_TRANSCRIPTION_LOG_FILE%"
                endiff

REM  ✨ ✨ ✨ ✨ ✨ ✨ ACTUALLY DO THE AI-TRANSCRIPTION: ✨ ✨ ✨ ✨ ✨ ✨ 
        rem PRETTY HEADER FOR AI-TRANSCRIPTION:
                rem Cosmetics:
                    @echo.
                    @call bigecho %ANSI_COLOR_BRIGHT_RED%%EMOJI_FIREWORKS% Launching AI! %EMOJI_FIREWORKS%%ansi_color_normal%
                    echo.
                    echo CWP=%_CWP, time=%_DATETIME
                    rem that firework emoji was so much cooler in emoji11/win10 than emoji13/win11
                    echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[magenta]%ANSI_CURSOR_CHANGE_TO_vertical_bar_BLINKING%   
                    title waiting: %BASE_TITLE_TEXT%

        rem ACTUALLY DO IT!!!:
                if defined CURSOR_RESET echos %CURSOR_RESET%
                echos %ANSI_CURSOR_CHANGE_TO_vertical_bar_steady%   
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
                       %LAST_WHISPER_COMMAND%                            |:u8 copy-move-post whisper -t"%OUR_LOGFILE%"  

                on break cancel                      
                       
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                goto /i Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                :Done_Transcribing                 %+ rem  /     If this seems ridiculous, it is because we want to make sure we don’t lose our place in this script if the script has been modified during running. It’s probably a hopeless endeavor to recover from that.
                option //UnicodeOutput=%UnicodeOutputDefault%
                if defined TOCK echos %TOCK%       %+ rem just our nickname for an extra-special ansi-reset
                if defined CURSOR_RESET echos %CURSOR_RESET%
                gosub lockfile_delete_transcriber_lock_file
                call errorlevel "some sort of problem with the AI generation occurred in create-srt-from-file line 744ish"

        rem Cosmetics:
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%                
                call unlock-bot                    %+ rem Disable our status bar
                title Done: %BASE_TITLE_TEXT%      %+ rem Update the window title

REM delete zero-byte LRC files that can be created
        rem echo "About to delete zero byte files " %+ pause
        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[orange]%ANSI_CURSOR_CHANGE_TO_BLOCK_steady%                
        call delete-zero-byte-files *.lrc;*.srt silent >nul
        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[green]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%                



REM did we create the SRT file?
        rem echo "About to check if we created the expected output file of “%EXPECTED_OUTPUT_FILE%” file " %+ pause
        rem echo if not exist "%EXPECTED_OUTPUT_FILE%" then 
        iff not exist "%EXPECTED_OUTPUT_FILE%" then 
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
        if not exist "%@UNQUOTE[%EXPECTED_OUTPUT_FILE%]" goto /i endiff_1286
                rem Ensure the folder is marked as having AI-generated transcriptions:
                        if not exist "__ contains AI-generated SRT files __" @echo %EXPECTED_OUTPUT_FILE%%::::%_DATETIME%::::%TRANSCRIBER_TO_USE% >>:u8"__ contains AI-generated SRT files __"

                rem Keep track of how many we’ve done in this session:
                        if "" == "%NUM_TRANSCRIBED_THIS_SESSION%" set NUM_TRANSCRIBED_THIS_SESSION=0
                        set NUM_TRANSCRIBED_THIS_SESSION=%@EVAL[%NUM_TRANSCRIBED_THIS_SESSION% + 1]
                        if %NUM_TRANSCRIBED_THIS_SESSION% gt 1 echo %ANSI_COLOR_IMPORTANT%%check1% %blink_on%Transcribed this session: %italics_on%%NUM_TRANSCRIBED_THIS_SESSION%%blink_off%%italics_off%%ANSI_COLOR_NORMAL%


                rem Create TXT file from freshly-generated lyrics, if none currently exists:
                        if exist "%TXT_FILE%" goto /i :text_file_exists 
                                echo %ansi_color_warning_soft%%star2% No text file exists, converting transcription to text...%ansi_color_normal%
                                call srt2txt "%EXPECTED_OUTPUT_FILE%" "%TXT_FILE%"
                        :text_file_exists 
        :endiff_1286
        title %CHECK%%BASE_TITLE_TEXT%


        
REM Post-process the SRT file: Cosmetics:
        rem When we had headers, we needed to do this:
                rem gosub divider
        rem But now that we switched to status-bar/footers, i noticed that we end up on the 3ʳᵈ  line of the footer
        rem after footer unlock. The way I noticed this was that gosub'ing ’divider’ up above overwrote the status bar
        rem divider with our own, which had an incongruent background color, which made me realize the bottom divider
        rem line of the status-bar was being overrwritten with our “call  divider” from above.  So we changed it
        rem and instead of calling divider, we simply move one line down. The divider is already there.
        rem NOTE: that this may change after we update unlock-bot to clean off the footer after unlocking.
        rem NOTE:      Currently, this implementation is slated to be a temporary cosmetic fix that will likely break later
        rem Finally romving this very late, 2025/04/24:        echo.

REM Post-process the SRT file: Actual postprocessing:    
        rem echo "About to remove invisible periods" %+ pause
        gosub postprocess_lrc_srt_files
        




rem If we did, we need to rename any sidecar TXT file that might be there {from already-having-existed}, becuase 
rem MiniLyrics will default to displaying TXT over SRC
        rem NO NOT ANYMORE if exist "%TXT_FILE%" (ren /q "%TXT_FILE%" "%TXT_FILE.bak.%_datetime" )


rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////
iff "1" == "%USE_2023_LOGIC%" then
                        REM rename the file & delete the vocal-split wav file
                            iff "%EXPECTED_OUTPUT_FILE%" != "%LRC_FILE%" then
                                set MOVE_DECORATOR=%ANSI_GREEN%%FAINT%%ITALICS% 
                                mv "%EXPECTED_OUTPUT_FILE%" "%LRC_FILE%"
                            endiff
                            if not exist "%LRC_FILE%" call validate-environment-variable LRC_FILE "LRC file not found around line 1501ish"
                            if exist "%LRC_FILE%" .and. "%2" != "keep" (*del /Ns /q /r "%VOC_FILE%")
endiff
rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////


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
                                        echos %NEWLINE%

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
                gosub divider
                @call warning "Unfortunately, we could not create the karaoke file %emphasis%%SRT_FILE%%deemphasis%"
                title %emoji_warning% Karaoke not generated! %emoji_warning% 
                :ask_about_instrumental_1500
                        gosub ask_about_instrumental
                        gosub divider
                        call AskYN "Mark karaoke as failed so we don’t try again [%ansi_color_bright_green%N%ansi_color_prompt%=No, mark instrumental instead,%ansi_color_bright_green%P%ansi_color_prompt%=Play it]" no %KARAOKE_APPROVAL_WAIT_TIME% IP I:no_instead_mark_mark_instrumental,P:play
                        gosub check_for_answer_of_I "%INPUT_FILE%"
                        gosub check_for_answer_of_P "%INPUT_FILE%"             
                if  "P" == "%ANSWER%" goto /i ask_about_instrumental_1500
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
echo 🐐 gosub create_or_set_postprocessed_lyrics "%POSTPROCESSED_LYRICS%" 
        gosub create_or_set_postprocessed_lyrics "%POSTPROCESSED_LYRICS%" 
call subtle "postprocessed_lyrics is now “%postprocessed_lyrics%” GOAT"

rem Compare lyrics vs postprocessed vs transcription, with visual stripes between (stL=lower stripe, stB=both, stU=upper stripe):
        if exist "%TXT_FILE%"             call review-file -wh -stL "%TXT_FILE%"            "¹Lyrics (raw)"
        if exist "%POSTPROCESSED_LYRICS%" call review-file -wh -stB "%POSTPROCESSED_LYRICS" "²Lyrics (processed)"
        if exist "%SRT_FILE%"             call review-file -wh -stU "%SRT_FILE%"            "³Transcription"
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
        if defined ANSI_RESET (echos %ANSI_RESET%)
        if defined TOCK       (echos %TOCK%)        %+ rem nickname for fancy-extra ansi-reset

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
        echo %TAB%%TAB%%TAB%%TAB%%ansi_color_less_important%%star2% in dir: %faint_on%%italics_on%%[_CWP]%italics_off%%faint_off%%ansi_color_normal%
        @gosub divider
        if "%_CWD\" != "%SONGDIR%" *cd "%SONGDIR%"
        REM gosub debug "CWP = “%_CWP” 
        iff "1" == "%FORCE_REGEN%" then
                set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE=%EDIT_KARAOKE_AFTER_FORCE_REGEN_WAIT_TIME%
        else
                set EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE=%EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME%
        endiff

        rem Ask to approve our karaoke:
                rem 
                echo %ansi_color_warning_soft%🐐 about to gosub ask_to_approve_approve_karaoke [1670] BUT MAYBE WE CAN SKIP THIS%ansi_color_normal% but let’s try adding if not exist "%TXT_FILE%" 
                if not exist "%TXT_FILE%" gosub ask_to_approve_karaoke
                rem TODO remove: if "Y" == "%ANSWER%"      goto /i go_here_if_we_just_approved_the_karaoke

        rem (1) Stuations to EXCLUDE from asking to improve our karaoke:
                if not exist "%TXT_FILE%" .or. "1" == "%JUST_CONVERTED_LRC_TO_TEXT%" .or. "1" == "%JUST_CONVERTED_SRT_TO_TEXT%" .or. "1" == "%whisper_alignment_happened%" goto /i do_not_ask_to_align_with_txt
        rem (2) Ask to IMPROVE our karaoke:
                :ask_about_alignment
                @call AskYN "Align %italics_on%mis-heard%italics_off% karaoke to original lyrics with %italics_on%WhisperTimeSync%%italics_off% [%ansi_green%P%ansi_color_prompt%=Play 1st,%ansi_green%A%ansi_color_prompt%=Approve now,%ansi_color_bright_green%T%ansi_color_prompt%=Dele%ansi_color_green%t%ansi_color_prompt%e,%ansi_color_green%E%ansi_color_prompt%dit transcription]" no %WHISPERTIMESYNC_QUERY_WAIT_TIME% notitle AEIPT P:Play_It,A:approve_the_karaoke_right_now,T:delete,E:Edit_transcription,I:mark_as_instrumental
                        rem Option “I”:
                                gosub check_for_answer_of_I "%input_file%"
                        rem Option “E”:
                                gosub check_for_answer_of_E "%srt_file%"
                        rem Option “T”:
                                gosub check_for_answer_of_T 

                        rem Option “P”:
                                set      player_command_extra_options=show_karaoke
                                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%input_file%"
                                unset /q player_command_extra_options
                                if  "P" == "%ANSWER%" goto /i ask_about_alignment          

                        rem Option “A”:
                                iff "A" == "%ANSWER%" then
                                        call approve-karaoke "%srt_file%"
                                        goto /i :go_here_if_we_just_approved_the_karaoke
                                endiff

                        rem Option “Y”:
                                :Do_Whisper_Time_Sync
                                iff "Y" == "%ANSWER%" .or. "1" == "%DO_WHISPER_TIME_SYNC%" then
                                        set DO_WHISPER_TIME_SYNC=0                                                                      %+ rem Turn Off Flag
                                        call WhisperTimeSync "%SRT_FILE%" "%TXT_FILE%" 

                                        rem        rem Run WhisperTimeSync to re-align:
                                        rem                call WhisperTimeSync-helper "%SRT_FILE%" "%TXT_FILE%" preview
                                        rem        rem Was a new file actually created? 
                                        rem        rem WhisperTimeSync.bat sets %SRT_NEW% to the expected new filename
                                        rem                iff not exist "%SRT_NEW%" then
                                        rem                        call alarm "Newly-synchronized file doesn’t exist! We will continue..."
                                        rem                        goto /i :WhisperTimeSync_alignment_complete
                                        rem                else
                                        rem                        call success "%italics_on%WhisperTimeSync%italics_off% successful"
                                        rem                endiff
                                        rem        rem Preview the old lyrics vs OLD srt with stripes next to each other:
                                        rem                call review-file       -wh -st  "%TXT_FILE%"
                                        rem                call review-file       -wh -stU "%SRT_FILE%"
                                        rem        rem Preview the old lyrics vs NEW srt with stripes next to each other:
                                        rem                gosub divider
                                        rem                call print-with-columns.py -st  "%TXT_FILE%"
                                        rem                call review-file        wh -stU "%SRT_NEW%"
                                        rem        rem Ask if it’s better or not...
                                        rem                call AskYN "Is this better than the old" no 666 
                                        rem        rem If it is better, back up the old version and replace it with this one:
                                        rem                iff "Y" == "%ANSWER%" then
                                        rem                        rem back up the old/existing karaoke:
                                        rem                                echo     *copy /Nst "%SRT_FILE%" "%SRT_FILE%.📀.%_DATETIME.bak" %+ pause
                                        rem                                echo ray|*copy /Nst "%SRT_FILE%" "%SRT_FILE%.📀.%_DATETIME.bak" %+ pause
                                        rem                        rem move the new karaoke to overwrite the now-backed-up old karaoke:
                                        rem                                echo     *copy /Nst "%SRT_NEW%" "%SRT_FILE%" %+ pause
                                        rem                                echo ray|*copy /Nst "%SRT_NEW%" "%SRT_FILE%" %+ pause
                                        rem                else
                                        rem                                echo ray|*del /q "%SRT_NEW%" 
                                        rem                endiff
                                        goto /i display_karaoke_before_asking_to_edit_it
                                endiff
                        :WhisperTimeSync_alignment_complete

        rem At this point, the karaoke is generated, possibly corrected, and awaiting our approval:
                echo %ansi_color_debug%- DEBUG: about to gosub approve karaoke 1644%ansi_color_normal%
                if "1" == "%JUST_RENAMED_TO_INSTRUMENTAL%" goto END
                gosub ask_to_approve_karaoke
                rem TODO remove: if "Y" == "%ANSWER%" goto /i go_here_if_we_just_approved_the_karaoke
                :do_not_ask_to_align_with_txt


        rem Last chance to edit the karaoke:
                :ask_about_karaoke_edit
                echo %ansi_color_warning_soft%- DEBUG: pretty sure we can: goto /i skip_this_part_we_no_longer_need_it_1670 ... perhaps unless whisper_alignment_happened=1 (whisper_alignment_happened==“%whisper_alignment_happened%”)
                                        @call askyn  "Edit karaoke file%blink_on%?%blink_off% %faint_on%[in case of mistakes]%faint_off% [%ansi_color_bright_green%W%ansi_color_prompt%=Run %italics_on%WhisperTimeSync%italics_off%,%ansi_color_bright_green%A%ansi_color_prompt%=Approve karaoke,%ansi_color_bright_green%U%ansi_color_prompt%=Unapprove,%ansi_color_bright_green%T%ansi_color_prompt%=Dele%ansi_color_green%t%ansi_color_prompt%e]" no %EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE% notitle APUWT P:Play_It,W:Fix_With_WhisperTimeSync,A:go_ahead_and_approve_the_karaoke_file,U:unapprove_karaoke,T:delete_karaoke_file
                                        :just_asked_to_edit_karaoke
                                        gosub check_for_answer_of_E
                                        gosub check_for_answer_of_T
                                        iff "A" == "%ANSWER%" then
                                                call  approve-karaoke "%srt_file%"
                                                goto /i go_here_if_we_just_approved_the_karaoke
                                        endiff
                                        iff "U" == "%ANSWER%" then
                                                call disapprove-subtitles "%srt_file%"
                                                goto /i go_here_if_we_unpproved_or_deleted_the_karaoke
                                        endiff
                                        iff "W" == "%ANSWER%" then
                                                set   DO_WHISPER_TIME_SYNC=1
                                                goto /i Do_Whisper_Time_Sync
                                        endiff                
                :skip_this_part_we_no_longer_need_it_1670

                rem This can work for either of the previous AskYN calls:
                echo %ansi_color_debug%-DEBUG: about to check iff "%ANSWER" == "Y" ...... 🍪%ansi_color_normal%>nul
                iff "%ANSWER" == "Y" then
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
                rem “P”:
                        set player_command_extra_options=show_karaoke
                        gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%input_FILE%"
                        unset /q player_command_extra_options
                        iff "%ANSWER" == "P" then goto /i ask_about_karaoke_edit


        echo 🐐 about to gosub approve karaoke 1526
        gosub ask_to_approve_karaoke
        rem TODO remove: if  "Y" == "%ANSWER%" goto /i go_here_if_we_just_approved_the_karaoke
        rem TODO remove: iff "N" == "%ANSWER%" then
        rem TODO remove:         title %RED_X% %SRT_FILE% NOT generated successfully! %RED_X%      
        rem TODO remove:         goto /i :go_here_if_we_unpproved_or_deleted_the_karaoke
        rem TODO remove: endiff

        

        :go_here_if_we_just_approved_the_karaoke

        rem Update the title to say we’re done! We are!
                title %CHECK% %SRT_FILE% generated successfully! %check%      
                if "%SOLELY_BY_AI%" == "1" (call warning "ONLY AI WAS USED. Lyrics were not used for prompting")


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
                @call askyn  "Approve karaoke file [D=%ansi_color_bright_green%D%ansi_color_prompt%isapprove,dele%ansi_color_bright_green%T%ansi_color_prompt%e,P=%ansi_color_bright_green%P%ansi_color_prompt%lay,E=%ansi_color_bright_green%E%ansi_color_prompt%dit karaoke,W=%ansi_color_bright_green%W%ansi_color_prompt%hisperTimeSync]" no %KARAOKE_APPROVAL_WAIT_TIME% notitle ADEIPTW E:edit_karaoke,P:Play_It,D:DISapprove_them,W:Whisper_Time_sync_fix,A:Yes_approve_it,I:mark_instrumental,T:delete_it
echo ** calling gosub check_for_answer_of_I "%INPUT_FILE%" goat
                gosub check_for_answer_of_T "%INPUT_FILE%"
                gosub check_for_answer_of_I "%INPUT_FILE%"
                gosub check_for_answer_of_E "%SRT_FILE%"
                iff "%ANSWER" == "W" then
                        set ANSWER=Y
                        goto /i just_asked_to_edit_karaoke
                endiff
                iff "%ANSWER" == "W" then
                        set   DO_WHISPER_TIME_SYNC=1
                        gosub DO_WHISPER_TIME_SYNC
                endiff
                REM call debug "about to check iff “%ANSWER%” == “Y” ...... 🍪"
                iff "%ANSWER" == "Y" .or. "%ANSWER" == "A" then
                        call approve-subtitles    "%SRT_FILE%" 
                        set karaoke_status=APPROVED
                endiff
                iff "%ANSWER" == "N" .or. "%ANSWER" == "D" then
                        set karaoke_status=NOT_APPROVED
                        call disapprove-subtitles "%SRT_FILE%" 
                        iff "N" == "%ANSWER%" then
                                title %RED_X% %SRT_FILE% NOT generated successfully! %RED_X%      
                                goto /i go_here_if_we_unpproved_or_deleted_the_karaoke
                        endiff
                endiff
                set player_command_extra_options=show_karaoke
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P "%INPUT_FILE%"
                unset /q player_command_extra_options
                if "%ANSWER%" == "P" goto /i ask_about_karaoke_approval
                if "%ANSWER%" == "Y" goto /i go_here_if_we_just_approved_the_karaoke
        return
        :check_for_answer_of_E [opt1]                        
                iff "E" == "%ANSWER%" then
                        rem TODO MAYBE: wonder if this should really be LYRIC_FILE and we’re just getting luck all the time:
                        set FILE_TO_USE=%TXT_FILE% 
                        if "" !=  "%opt1%" set FILE_TO_USE=%@UNQUOTE["%opt1%"]
                        %EDITOR% "%FILE_TO_USE%"
                        pause "%ansi_color_warning%%blink_on%Press any key when done with edits...%blink_off%%ansi_color_normal%"
                endiff
        return
        :check_for_answer_of_G [opt]
                if "%@UNQUOTE["%opt%"]" == "" call fatal_error "check_for_answer_of_G in create-srt-from-file.bat needs to be passed a filename"

                if "G" == "%ANSWER%" call get-lyrics "%@UNQUOTE["%opt%"]" force
        return
        :check_for_answer_of_I [opt]                        
echo * calling: gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instr_if_answer_was_I %opt% goat
                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instr_if_answer_was_I %opt%
        return
        :check_for_answer_of_L [opt opt2]                        
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_L %opt% %opt2%
        return
        :check_for_answer_of_P [opt]                        
                rem set player_command_extra_options=show_karaoke
                gosub "%BAT%\get-lyrics-for-file.btm" check_for_answer_of_P %opt%
                rem unset /q player_command_extra_options
        return
        :check_for_answer_of_T [opt]
                rem TODO opt->file2use conversion
                iff "T" == "%ANSWER%" then
                        if exist "%srt_file%" (echos %ansi_color_removal%%emoji_axe%  `` %+ *del /p /Ns "%srt_file%")
                        if exist "%lrc_file%" (echos %ansi_color_removal%%emoji_axe%  `` %+ *del /p /Ns "%lrc_file%")
                        if exist "%txt_file%" (echos %ansi_color_removal%%emoji_axe%  `` %+ *del /p /Ns "%txt_file%")
                        if not exist "%srt_file%" set KARAOKE_STATUS=NOT_APPROVED
                        if not exist "%txt_file%" set   LYRIC_STATUS=NOT_APPROVED
                        if not exist "%srt_file%" .and. not exist "%txt_file%" gosub rename_audio_file_as_instrumental "%input_file%" ask
                        goto /i go_here_if_we_unpproved_or_deleted_the_karaoke
                endiff
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
        :divider [opt]                        
                gosub "%BAT%\get-lyrics-for-file.btm" divider %opt%
        return

        rem if not defined  AUDIO_FILE_LOCK_FILE set  AUDIO_FILE_LOCK_FILE=%@UNQUOTE[%@path["%INPUTFILE%"]].lock
        :lockfile_set_transcriber_lock_file_variables [opt]
                if not defined TRANSCRIBER_LOCK_FILE set TRANSCRIBER_LOCK_FILE=%@UNQUOTE[%@path[%search%]%@NAME[%TRANSCRIBER_TO_USE%]].lock
        return
        :lockfile_create_transcriber_lock_file [opt]
                if not defined TRANSCRIBER_LOCK_FILE set gosub :lockfile_set_transcriber_lock_file_variables
                :check_lock_file_try_again
                        if exist "%TRANSCRIBER_LOCK_FILE%" gosub :lockfile_wait_on_transcriber_lock_file
                :actually_create_it
                        iff not exist "%TRANSCRIBER_LOCK_FILE%" then
                                rem call debug "Creating lock file “%TRANSCRIBER_LOCK_FILE%”"
                                echo. %+ rem added very late 2024/04/28
                                echo %ansi_color_important_less%%STAR2% Creating lock file: %faint_on%“%italics_on%%@UNQUOTE["%TRANSCRIBER_LOCK_FILE%"]%italics_off%”%faint_off%%ansi_color_normal%
                                echo %ansi_color_green%%star2% Process %ansi_color_orange%%[_PID]%ansi_color_green% is transcribing: %ansi_color_cyan%“%ansi_color_pink%%SONGFILE%%ansi_color_cyan%”%ansi_color_green%>"%TRANSCRIBER_LOCK_FILE%"
                                echo %ansi_color_green%                 %star2% beginning at %ansi_color_purple%%[_time]%ansi_color_green% on date %ansi_color_purple%%_date%>>"%TRANSCRIBER_LOCK_FILE%"
                        endiff
        return
        :lockfile_delete_transcriber_lock_file [opt]
                if not defined TRANSCRIBER_LOCK_FILE set gosub :lockfile_set_transcriber_lock_file_variables
                :lockfile_delete_transcriber_lock_file_begin
                iff exist "%TRANSCRIBER_LOCK_FILE%" then
                        call debug "Deleting lock file “%TRANSCRIBER_LOCK_FILE%”"
                        *del /q /Ns "%TRANSCRIBER_LOCK_FILE%" >&nul
                endiff
                iff exist "%TRANSCRIBER_LOCK_FILE%" then
                        call error "Why does the lockfile of “%TRANSCRIBER_LOCK_FILE%” still exist?"
                        goto /i lockfile_delete_transcriber_lock_file_begin
                endiff
        return
        :lockfile_wait_on_transcriber_lock_file [opt]
                if not defined TRANSCRIBER_LOCK_FILE set gosub :lockfile_set_transcriber_lock_file_variables
                :start_waiting
                iff exist "%TRANSCRIBER_LOCK_FILE%" then

                        rem Check if it’s the lockfile for the current process, and ignore it if iti s:
                                set LOCKFILE_CONTENTS=%@ExecStr[type "%TRANSCRIBER_LOCK_FILE%"]
                                rem echo  checking if "1" ==  "@RegEx[%_PID,"%LOCKFILE_CONTENTS%"]" 
                                rem echo  checking if "1" == "%@RegEx[%_PID,"%LOCKFILE_CONTENTS%"]" 
                                if "1" == "%@RegEx[%_PID,"%LOCKFILE_CONTENTS%"]" (
                                        echo %ansi_color_warning_soft%%star3% Lockfile exists!%ansi_color_green%...but it%smart_apostrophe%s the lockfile for %italics_on%this%italics_off% process, so overwriting...
                                        return
                                ) 
                                :start_waiting_at_point_of_having_contents_already
                        
                        rem Ask to delete the lockfile, or wait for it to finish:
                                repeat 8 echo.
                                echos %@ANSI_MOVE_UP[8]
                                echos %ansi_position_save%
                                gosub divider
                                echos %ansi_color_important_less%%star2% Waiting on lockfile...
                                call warning_soft "Lockfile already exists! %START% Status:"                   
                                echos         %ansi_color_debug%``                              
                                type "%TRANSCRIBER_LOCK_FILE%"                                         
                                call  AskYN  "Delete lockfile"  no  10 
                                rem This one makes no sense here: E E:Edit_ai_prompt
                                unset /q return_point
                                if "%ANSWER%" == "E" gosub eset_fileartist_and_filesong
                                if "%ANSWER%" == "Y" gosub lockfile_delete_transcriber_lock_file                            
                                if "%ANSWER%" != "Y" echos %ansi_restore_position%%@ansi_move_up[4]%ansi_erase_to_end_of_screen%%ansi
                                if "%ANSWER%" != "Y" goto /i check_lock_file_try_again                                
                endiff
                if exist "%TRANSCRIBER_LOCK_FILE%" *delay 1
                if exist "%TRANSCRIBER_LOCK_FILE%" goto /i start_waiting_at_point_of_having_contents_already
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
                                if  "1" == "%REVIEW_LRC%" call   review-file  -stL  "%LRC_FILE%"
                                if  "1" == "%REVIEW_TXT%" call   review-file  -stB  "%TXT_FILE%"
                                if  "1" == "%REVIEW_SRT%" call   review-file  -stU  "%SRT_FILE%"
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
                                                                                                echo %ansi_color_debug%-DEBUG: called rename_audio_file_as_instrumental [opt=%opt%,opt2=%opt2%]  goat%ansi_color_normal%

                                                                                        rem If we have been asked to ask [if it’s an instrumental], then we need to ask [if it’s an instrumental]:
                                                                                                :rafai_ask_again
                                                                                                unset /q ANSWER                       
                                                                                                if "%1" == "ask" .or. "%opt2%" == "ask"  call AskYN "Mark as instrumental? [P=%ansi_color_bright_green%P%ansi_color_prompt%lay]" no 500 P P:play_it

                                                                                        rem Rename it if we are supposed to!
                                                                                                if  "Y" == "%ANSWER%"  gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental %opt%

                                                                                        rem Play it, if we were asked to do that instead, prior to renaming:
                                                                                                iff "P" == "%ANSWER%" then
                                                                                                        gosub   check_for_answer_of_P   %opt%
                                                                                                        goto /i rafai_ask_again       
                                                                                                endiff
                                                                                return
        :rename_audio_file_as_instr_if_answer_was_I []
                if "I" == "%ANSWER%" gosub rename_audio_file_as_instrumental
        return
        :create_or_set_postprocessed_lyrics [opt]
                echo %ansi_color_debug%%EMOJI_PHONE%  BEGIN: gosub [get-karaoke::]create_or_set_postprocessed_lyrics %opt%  ... postprocessed_lyrics is now =“%postprocessed_lyrics%”%ansi_color_normal%
                gosub "%BAT%\get-lyrics-for-file.btm" create_or_set_postprocessed_lyrics "%@UNQUOTE["%opt%"]"
                echo %ansi_color_debug%%EMOJI_PHONE%  ENDED: gosub [get-karaoke::]create_or_set_postprocessed_lyrics %opt%  ... postprocessed_lyrics is now =“%postprocessed_lyrics%”%ansi_color_normal%
        return


:skip_subroutines
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:END
:nothing_generated
setdos /x0
if defined ansi_color_unimportant echos %ansi_color_unimportant%
timer /5 off
if defined ansi_color_reset       echos %ansi_color_reset%


:Cleanup2
:Cleanup_Only
:just_do_the_cleanup
        call status-bar unlock
        setdos /x0
        set MAKING_KARAOKE=0
        unset /q LYRICS_ACCEPTABLE
        unset /q OKAY_THAT_WE_HAVE_SRT_ALREADY
        if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav >nul)
        if exist     *vad_original*.srt (*del /q     *vad_original*.srt >nul)

        rem This happens earlier, but we also want it to happen in cleanup, because sometimes cleanup is called from transcribed stuff *NOT* made with this script:
                iff "1" == "%CLEANUP%" then
                        if exist *.lrc call delete-zero-byte-files *.lrc silent >nul
                        if exist *.srt call delete-zero-byte-files *.srt silent >nul
                endiff

:The_Very_END
        setdos /x0
        @echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[orange]%ANSI_CURSOR_CHANGE_TO_DEFAULT%                
        rem @echos %ANSI_COLOR_BLUE%%FAINT_ON%
    
        
        @echos %ANSI_RESET%%CURSOR_RESET%

:EOF

:PopD
        setdos /x0
        if "1" == "%pushd_performed_in_create_srt%" (echo 2025 POPD! %+ pause %+ popd)
        rem if %@DirStack[] gt 0 (echo GOAT POPD! %+ pause %+ popd)                                    %+ rem If we pushd’ed to another folder, popd back
        rem if %@DirStack[] gt 0 (echo STILL MORE POPD! %+ pause %+ goto /i PopD)

:Fix_Command_Separator
        *setdos /x-5
        *setdos /c%default_command_separator_character%
        setdos /x0

:Unset_Variables
        set last_failure_ads_result=%failure_ads_result%
        set last_postprocessed_lyrics=%postprocessed_lyrics%
        unset /q failure_ads_result PROMPT_CONSIDERATION_TIME PROMPT_EDIT_CONSIDERATION_TIME JUST_APPROVED_LYRICLESSNESS goto_forcing_ai_generation LYRICS_SHOULD_BE_CONSIDERED_ACCEPTIBLE ABANDONED_SEARCH LYRICLESSNESS_STATUS AUTO_LYRIC_APPROVAL        ALREADY_HAND_EDITED FORCE_AI_ENCODE_FROM_LYRIC_GET JUST_RENAMED_TO_INSTRUMENTAL return_point goto_end abort_karaoke_kreation MAYBE_SRT* karaoke_status audio_file input_file postprocessed_lyrics

rem end of create-srt setlocal blocvk
rem 20250328 let’s try removing this: endlocal AI_GENERATION_ANYWAY_WAIT_TIME AI_GENERATION_ANYWAY_WAIT_TIME_FOR_LYRICLESSNESS_APPROVED_FILES AUTO_LYRIC_APPROVAL CLEANUP CONCURRENCY_WAS_TRIGGERED EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME EDIT_KARAOKE_AFTER_CREATION_WAIT_TIME_TO_USE EDIT_KARAOKE_AFTER_FORCE_REGEN_WAIT_TIME EXPECTED_OUTPUT_FILE FORCE_REGEN FOUND_SUBTITLE_FILE JSN_FILE LAST_FILE_PROBED LAST_WHISPER_COMMAND LRC_FILE LYRICS_ACCEPTABLE LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME MAKING_KARAOKE MAYBE_LYRICS_2 MAYBE_SRT_2 NEVERMIND_THIS_ONE NUM_TRANSCRIBED_THIS_SESSION OKAY_THAT_WE_HAVE_SRT_ALREADY OUR_LANGUAGE OUR_LYRICS OUTPUT_DIR PROMPT_CONSIDERATION_TIME PROMPT_EDIT_CONSIDERATION_TIME REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME SKIP_TXTFILE_PROMPTING SOLELY_BY_AI SONGBASE SONGDIR SONGFILE SRT_FILE TRANSCRIBER_PDNAME TRANSCRIBER_TO_USE TXT_FILE VALIDATED_CREATE_LRC_FF WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST WHISPER_PROMPT  FORCE_AI_ENCODE_FROM_LYRIC_GET


:The_Very_Very_END
@setdos /x0
echo 🐐%@COLORFUL[[END-CREATE-SRT-FROM-FILE, CWP=%_CWP]]
