@Echo off
 on break cancel

rem TODO: add another srt to subtitles if the last one is not empty: combat stuck lyrics:
rem 
rem 17
rem 00:02:20,060 --> 00:02:21,060
rem This should be default functionality of srt2lrc as well — the resulting lrc should have an empty at the end too
rem So we must postprocess before we would ever even use srt2lrc
rem     no need to include functoinality in srt2lrc as we're not sure this will be a final part of the workflow
rem     plus, we need to run this on pre-existing SRTs



rem todo highlight name/title in prompts, return back to askyn color after, which requires askyn color abstraction
rem TODO if we're doing lyrics, show downloaded lyrics *first* and if we found them chagne 1ˢᵗ question to 'are these better than d/l version'-type question
rem TODO afterregen anyway, we need to ask about ecc2fasdfasf.bat
rem TODO if lyrics are approved already, don't ask about them

:USAGE: lrc.bat whatever.mp3 {force|ai|cleanup|last|fast|AutoLyricApproval} {rest=options to pass on to whisper} ... ai=force ai regeneration, last=redo last one again, force=proceed even if LRC file is there, cleanup=clean up leftover files,  AutoLyricApproval=consider sidecar TXT files to be pre-approvedl yrics
:USAGE: set USE_LANGUAGE=jp                ——— to encode in a different language from en, like jp
:USAGE: set CONSIDER_ALL_LYRICS_APPROVED=1 ——— for *forced* pre-approved-lyrics mode (deprecated)

:REQUIRES:     <see validators>
:DEPENDENCIES: 2024 version: Faster-Whisper-XXL.exe delete-zero-byte-files.bat validate-in-path.bat debug.bat error.bat warning.bat errorlevel.bat print-message.bat validate-environment-variable.bat —— see validators for complete list
:DEPENDENCIES: 2023 version: whisper-faster.bat delete-zero-byte-files.bat validate-in-path.bat debug.bat error.bat warning.bat errorlevel.bat print-message.bat validate-environment-variable.bat


REM OLD 2023 USAGE:
rem    Not sure if applicable with 2024 version: :USAGE: lrc.bat whatever.mp3 keep  {keep vocal files after separation}
rem    Not sure if applicable with 2024 version: :USAGE: lrc.bat last               {quick retry again at the point of creating the lrc file —— separated vocal files must already exist}

REM CONFIG: 2024: 
        set TRANSCRIBER_TO_USE=Faster-Whisper-XXL.exe                %+ rem Command to generate/transcribe [with AI]
        set TRANSCRIBER_PDNAME=faster-whisper-xxl.exe                %+ rem probably the same as as %TRANSCRIBER_TO_USE%, but technically         it's whatever string can go into %@PID[] that returns a nonzero result if we are running a transcriber
        rem TRANSCRIBER_PRNAME=faster-whisper-xxl                    %+ rem this may be unused now!                process last (type "tasklist" to see) ... Generally the base name of any EXE
        set OUR_LANGUAGE=en
        set LOG_PROMPTS_USED=1                                       %+ rem 1=save prompt used to create SRT into sidecar ..log file
        set SKIP_SEPARATION=1                                        %+ rem 1=disables the 2023 process of separating vocals out, a feature that is now built in to Faster-Whisper-XXL, 0=run old code that probably doesn't work anymore
        SET SKIP_TEXTFILE_PROMPTING=0                                %+ rem 0=use lyric file to prompt AI, 1=go in blind
        set MAXIMUM_PROMPT_SIZE=3000                                 %+ rem The most TXT we will use to prime our transcription.  Since faster-whisper-xxx only supports max_tokens of 224, we only need 250 words or so. But will pad a bit extra. We just don't want to go over the command-line-length-limit!
rem CONFIG: 2024: WAIT TIMES:
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=120                 %+ rem wait time for "are these lyrics good?"-type questions
        set AI_GENERATION_ANYWAY_WAIT_TIME=45                        %+ rem wait time for "no lyrics, gen with AI anyway"-type questions
        set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=25      %+ rem wait time for "we already have karaoke, regen anyway?"-type questions
        set PROMPT_CONSIDERATION_TIME=20                             %+ rem wait time for "does this AI command look sane"-type questions
        set PROMPT_EDIT_CONSIDERATION_TIME=10                        %+ rem wait time for "do you want to edit the AI prompt"-type questions
        set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=0       %+ rem wait time for "hey lyrics not found!"-type notifications/questions. Set to 0 to not pause at all.
        set EDIT_KRAOKE_AFTER_CREATION_WAIT_TIME=300                 %+ rem wait time for "edit it now that we've made it?"-type questions ... Have decided it should probably last longer than the average song
        rem ^^^^ TODO: automation mode where all these get shortened to quite significantly, or all to 3, or all to 1, or something 🐮

REM config: 2023:
        rem set TRANSCRIBER_TO_USE=call whisper-faster.bat 
        rem set SKIP_SEPARATION=0         
        rem SET SKIP_TEXTFILE_PROMPTING=0  


REM Pre-run cleanup:
        echos %ansi_color_unimportant%
        timer /5 on                     %+ rem Let's time the overall process
        @call tock                      %+ rem purely cosmetic
        unset /q LYRIC_ATTEMPT_MADE
        unset /q OKAY_THAT_WE_HAVE_SRT_ALREADY
        if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav)
        if exist     *vad_original*.srt (*del /q     *vad_original*.srt)
        call unlock-top                 %+ rem Remove any leftover banners from previous runs

REM validate environment [once]:
        if not defined UnicodeOutputDefault (set UnicodeOutputDefault=no)
        iff 1 ne %VALIDATED_CREATE_LRC_FF then
                rem 2023 versin: call validate-in-path whisper-faster.bat debug.bat
                @call validate-in-path               %TRANSCRIBER_TO_USE%  get-lyrics.bat  debug.bat  lyricy.exe  copy-move-post  unique-lines.pl  paste.exe  divider  less_important  insert-before-each-line  bigecho  deprecate  errorlevel  grep  isRunning fast_cat  top-message  top-banner  unlock-top  deprecate.bat  add-ADS-tag-to-file.bat remove-ADS-tag-from-file.bat display-ADS-tag-from-file.bat display-ADS-tag-from-file.bat remove-period-at-ends-of-lines.pl
                @call validate-environment-variables FILEMASK_AUDIO COLORS_HAVE_BEEN_SET QUOTE emphasis deemphasis ANSI_COLOR_BRIGHT_RED check ansi_color_bright_Green ansi_color_Green ANSI_COLOR_NORMAL ansi_reset cursor_reset underline_on underline_off faint_on faint_off EMOJI_FIREWORKS star check emoji_warning ansi_color_warning_soft ANSI_COLOR_BLUE UnicodeOutputDefault bold_on bold_off
                @call validate-environment-variables TRANSCRIBER_PDNAME skip_validation_existence
                @call validate-is-function           randfg_soft
                @call checkeditor
                @set VALIDATED_CREATE_LRC_FF=1
        endiff

REM values set from parameters:
        set               PARAM1=%1
        set             SONGFILE=%@UNQUOTE[%1]
        set             SONGBASE=%@NAME[%SONGFILE]
        set POTENTIAL_LYRIC_FILE=%@UNQUOTE[%2]
        set LRC_FILE=%SONGBASE%.lrc
        set SRT_FILE=%SONGBASE%.srt
        set TXT_FILE=%SONGBASE%.txt
        set JSN_FILE=%SONGBASE%.json
        rem VOC_FILE=%SONGBASE%.vocals.wav
        rem LRCFILE2=%SONGBASE%.vocals.lrc




REM branch on certain paramters, and clean up various parameters 
        rem %1 "last" is a very unique situation:
        if "%1" eq "last" (goto :actually_make_the_lrc) %+ rem to repeat the last regen
        rem %1 was unique. Now we do the normal stuffs:


        rem ENVIRONMENT-ONLY parameters:               
        if defined USE_LANGUAGE (set OUR_LANGUAGE=%USE_LANGUAGE%)

        rem If the next parameter is special, we must grab it and shift again so the rest properly reaches Whisper:
        REM default modes:
        set FAST_MODE=0 
        set SOLELY_BY_AI=0
        set FORCE_REGEN=0
        set FORCE_REGEN=0 
        set CLEANUP=0 
        set AUTO_LYRIC_APPROVAL=0

        iff %CONSIDER_ALL_LYRICS_APPROVED eq 1 then
                set AUTO_LYRIC_APPROVAL=1
                rem This is deprecated/testing only and we don't want it to persist:
                unset /q CONSIDER_ALL_LYRICS_APPROVED   
        endiff                

        
        echo %%1 is %1 >nul
        echo %%2 is %2 >nul
        echo %%3 is %3 >nul
        echo %%4 is %4 >nul
        echo %%* is %* >nul
        echo %%$ is %$ >nul
        :process_for_mode_variants
        rem %1 is the filename, but %2+++ can be various options to pull off, while the rest is to go to Whisper/our transcriber
        rem iff "%2" eq "ai" .or. "%2" eq "fast" .or. "%2" eq "redo" .or. "%2" eq "force-regen" .or. "%2" eq "cleanup" then
        iff "%1" ne "" then
                set special_parameters_possibly_present=1
        else
                set special_parameters_possibly_present=0
        endiff
        if 1 ne %special_parameters_possibly_present% goto :NoSpecial
                set special=%1
                if "%special%" eq "ai"                 (set SOLELY_BY_AI=1       )
                if "%special%" eq "fast"               (set FAST_MODE=1          )
                if "%special%" eq "cleanup"            (set CLEANUP=1            )
                if "%special%" eq "force-regen"        (set FORCE_REGEN=1        )
                if "%special%" eq "redo"               (set FORCE_REGEN=1        )
                if "%special%" eq "ala"                (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq  "la"                (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq     "LyricApprove"   (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq     "LyricApproved"  (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq     "LyricApproval"  (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq     "LyricsApprove"  (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq     "LyricsApproved" (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq     "LyricsApproval" (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyricsApproval" (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyricApproval"  (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyricsApproved" (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyricApproved"  (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyricsApprove"  (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyricApprove"   (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyrics"         (set AUTO_LYRIC_APPROVAL=1)
                if "%special%" eq "AutoLyric"          (set AUTO_LYRIC_APPROVAL=1)
        :NoSpecial
        iff 1 eq %special_parameters_possibly_present% then       
                shift 
                rem after 'shift', %1 is now the remaining arguments (if any)
                goto :process_for_mode_variants
        endiff        
        
        if 1 eq %CLEANUP (goto :just_do_the_cleanup)

        set MAKING_KARAOKE=1

              
        rem todo: consider going back to the top of this section 2 or 3 times for easier simultaneous option stacking but then you gotta think about what all the combinations really mean



 
 rem Adjust wait times if we are in automatic mode. Also, automatic lyric approval means we're streamilined and should auto-fast it as well:
        iff 1 eq %AUTO_LYRIC_APPROVAL .or. 1 eq %FAST_MODE% then
                set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=3                 %+ rem wait time for "are these lyrics good?"-type questions
                set AI_GENERATION_ANYWAY_WAIT_TIME=3                       %+ rem wait time for "no lyrics, gen with AI anyway"-type questions
                set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=2     %+ rem wait time for "we already have karaoke, regen anyway?"-type questions
                set PROMPT_CONSIDERATION_TIME=4                            %+ rem wait time for "does this AI command look sane"-type questions
                set PROMPT_EDIT_CONSIDERATION_TIME=2                       %+ rem wait time for "do you want to edit the AI prompt"-type questions
                set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=1     %+ rem wait time for "hey lyrics not found!"-type notifications/questions
                set EDIT_KRAOKE_AFTER_CREATION_WAIT_TIME=1                 %+ rem wait time for "edit it now that we've made it?"-type questions ... Have decided it should probably last longer than the average song
        endiff




REM Values fetched from input file:
        call get-lyrics-via-multiple-sources "%SONGFILE%" SetVarsOnly %+ rem probes the song file and sets FILE_ARTIST / FILE_TITLE / etc
        on break cancel

REM Determine the base text used for our window title:
        set BASE_TITLE_TEXT=%FILE_ARTIST - %FILE_TITLE% 

REM Determine our expected input and output files:
        set INPUT_FILE=%SONGFILE%
        rem EXPECTED_OUTPUT_FILE=%LRC_FILE%   %+ rem //This was for the 2023 version
        SET EXPECTED_OUTPUT_FILE=%SRT_FILE%




REM if 2nd parameter is lyric file, use that one:
        iff exist "%POTENTIAL_LYRIC_FILE%" then
                set TXT_FILE=%POTENTIAL_LYRIC_FILE%
                @call less_important "Using existing transcription file: %italics_on%%TXT_FILE%%italics_off%"
                goto :AI_generation
        endiff

rem If we are doing it *SOLELY* by AI, skip some of our lyric logic:
        rem this doesn't really do anything, it's the next thing: if 1 ne %SOLELY_BY_AI% goto :solely_by_ai_jump1

REM display debug info
        :Retry_Point
        :solely_by_ai_jump1
        if %DEBUG gt 0 echo %ansi_color_debug%- DEBUG: (8)%NEWLINE%    SONGFILE='%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%':%NEWLINE%    SONGFILE='%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%':%NEWLINE%%TAB%%TAB%%FAINT_ON%SONGBASE='%ITALICS_ON%%SONGBASE%%ITALICS_OFF%'%NEWLINE%%TAB%%TAB%LRC_FILE='%ITALICS_ON%%LRC_FILE%%ITALICS_OFF%', %NEWLINE%%TAB%%TAB%TXT_FILE='%ITALICS_ON%%TXT_FILE%%ITALICS_OFF%'%FAINT_OFF%%ansi_color_normal%
        gosub say_if_exists SONGFILE
        gosub say_if_exists SRT_FILE
        gosub say_if_exists LRC_FILE
        gosub say_if_exists TXT_FILE
        gosub say_if_exists JSN_FILE
        @echo.



REM if our input MP3/FLAC/audio file doesn't exist, we have problems:
        call validate-environment-variable INPUT_FILE
        rem iff "%FORCE_REGEN%" eq "1" .or. "%SOLELY_BY_AI%" eq "1" then
        rem         rem Skip validation because we're doing things automatically
        rem else
                call validate-file-extension "%INPUT_FILE%" %FILEMASK_AUDIO%
        rem endiff



REM if we already have a SRT file, we have a problem:
        iff exist "%SRT_FILE%" .and. %OKAY_THAT_WE_HAVE_SRT_ALREADY ne 1 .and. %SOLELY_BY_AI ne 1 then
                iff exist "%TXT_FILE%" then
                        @call divider
                        rem @call less_important "(65) Review the lyrics now:" 
                        call bigecho %STAR% %ANSI_COLOR_IMPORTANT_LESS%Review the lyrics:%ANSI_RESET%
                        @echos %ANSI_COLOR_BRIGHT_YELLOW%
                        rem unique-lines -A is a bit of a misnomer because it gives ALL lines, but with -L it gives us a preview of some of the lyric massage prior to the AI prompt
                        rem type "%TXT_FILE%" |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                           (type "%TXT_FILE%" |:u8 unique-lines -A -L)|:u8 print-with-columns
                        iff %@FILESIZE["%TXT_FILE%"] lt 5 then
                            echo         %ANSI_COLOR_WARNING%Hmm. Nothing there.%ANSI_RESET%
                        endiff
                        @call divider
                endiff
                @call bigecho %ansi_color_warning%%emoji_warning%Already have karaoke!%emoji_warning%%ansi_color_normal%
                @call warning "We already have a file created: %emphasis%%srt_file%%deemphasis%"
                if %SOLELY_BY_AI ne 1 (goto :automatic_skip_for_ai_parameter)
                        @call advice "Automatically answer the next prompt as Yes by adding the parameter 'force-regen' or 'redo'"
                        iff exist "%TXT_FILE%" then
                                @call AskYn "%conceal_on%5%conceal_off%Do the above lyrics look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME
                                iff "%answer%" eq "Y" then
                                        rem Proceed with process
                                        set LYRICS_ACCEPTABLE=1
                                else
                                        ren /q "%TXT_FILE%" "%@NAME[%TXT_FILE%].txt.%_datetime.bak" >nul
                                        @call less_important "Okay, let's try fetching new lyrics"
                                        goto :Refetch_Lyrics
                                endiff
                        endiff
                :automatic_skip_for_ai_parameter
                rem FORCE_REGEN is %FORCE_REGEN %+ pause
                iff %FORCE_REGEN% ne 1 then
                        @call askYN "%conceal_on%22%conceal_off%Regenerate it anyway?" no %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME%
                endiff
                iff "%ANSWER%" eq "Y" .or. %FORCE_REGEN eq 1 then
                        iff exist "%SRT_FILE%" then
                                ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak" >nul
                        endiff
                        set OKAY_THAT_WE_HAVE_SRT_ALREADY=1

                        rem TODO show lyrics again?
                        @call AskYN "Re-get lyrics?" no %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME% %+ rem todo make unique wait time for this
                        iff "%ANSWER%" eq "Y" then
                                call get-lyrics "%AUDIO_FILE%"
                        endiff


                        goto :Force_AI_Generation
                else
                        @call warning_soft "Not generating anything, then..."
                        goto :END
                endiff
        endiff





REM If "%SOLELY_BY_AI%" eq "1", we nuke the LRC/SRT file and go straight to AI-generating, and we only use the TEXT
REM file if it is pre-approved or we are set in AutoLyricsApproval mode:
        iff "%SOLELY_BY_AI%" eq "1" then
                @call important_less "Forcing AI generation..."
                if exist "%LRC_FILE%" (ren /q "%LRC_FILE%" "%@NAME[%LRC_FILE%].lrc.%_datetime.bak")
                if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
                if %AUTO_LYRIC_APPROVAL ne 1 (set SKIP_TEXTFILE_PROMPTING=1)
                goto :AI_generation
        endiff

REM If we say "force", skip the already-exists check and contiune
        iff "%2" eq "force" then
                if exist "%LRC_FILE%" (ren /q "%LRC_FILE%" "%@NAME[%LRC_FILE%].lrc.%_datetime_.bak")
                rem do not do this, we're just skipping the check, that's all:
                rem if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
                rem no need to goto :attempt_to_download_LRC because that's what's next anyway
        else
                REM At this point, we are NOT in force mode, so:
                REM At this point, if an LRC file already exists, we shouldn't bother generating anything...
                        rem if exist %LRC_FILE% (@call error   "Sorry, but %bold%LRC%bold_off% file '%italics%%LRC_FILE%%italics_off%' %underline%already%underline_off% exists!" %+ call cancelll)
                            if exist %LRC_FILE% (@call warning "Sorry, but %bold%LRC%bold_off% file '%italics%%LRC_FILE%%italics_off%' %underline%already%underline_off% exists!%" silent %+ goto :END)

        endiff



:attempt_to_download_LRC 
:attempt_to_download_LRC_with_lyricy
        REM FAILED: Let's NOT try downloading a LRC with lyricy first because it gets mismatches whenever none exists, which is almost always:
               rem call get-lrc-with-lyricy "%CURRENT_SONG_FILE%"
               rem if exist %LRC_FILE% (@call success "Looks like %italics_on%lyricy%italics_off% found an LRC for us!" %+ goto :END)




REM If it's an instrumental, don't bother:
        if "%@REGEX[instrumental,%INPUT_FILE%]" eq "1" (@call warning "Sorry, nothing to transcribe because this appears to be an instrumental: %INPUT_FILE%" %+ goto :END)





REM In terms of automation, as of 10/28/2024 we are only comfortable with FULLY automatic (i.e. going through a whole playlist) generation
REM in the event that a txt file also exists.  To enforce this, we will only generate with a "force" parameter if the txt file does not exist.
        :check_for_txt_file



        iff not exist "%TXT_FILE%" .and. 1 ne %FORCE_REGEN% .and. 1 eq %LYRIC_ATTEMPT_MADE then
                @call warning "Failed to generate %emphasis%%SRT_FILE%%deemphasis%%ansi_color_warning%" silent
                @call warning "because the lyrics %emphasis%%TXT_FILE%%deemphasis%%ansi_color_warning% do not exist and could not be downloaded!" silent
                @call advice  "Use 'ai' option to go straight to AI generation"
                @call askYN "Generate AI anyway" no %AI_GENERATION_ANYWAY_WAIT_TIME%
                if "%ANSWER%" eq "Y" (goto :Force_AI_Generation)
                goto :END
        else
                @echo %ansi_color_warning_soft%%star% Not yet generating %emphasis%%SRT_FILE%%deemphasis%%ansi_color_warning_soft% because %emphasis%%TXT_FILE%%deemphasis%%ansi_color_warning_soft% does not exist!%ansi_color_normal%
                @call advice       "Use 'force' option to override." silent
                @call advice       "Try to get the lyrics first. SRT-generation is most accurate if we also have a TXT file of lyrics!" silent
                iff %WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST gt 0 then
                    call pause-for-x-seconds %WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST%
                endiff
                :Refetch_Lyrics
                        call get-lyrics "%SONGFILE%" 
                        set LYRIC_ATTEMPT_MADE=1
                goto :We_Have_A_Text_File_Now
        endiff
        :We_Have_A_Text_File_Now


rem Mandatory review of lyrics 
        iff exist "%TXT_FILE%" then
                rem Deprecating this section which is redundant because it's done in get-lyrics:
                iff 0 = 1 then
                        @call divider
                        @call less_important "[REDUNDANT?] Review the lyrics now:"
                        @call divider
                        @echos %ANSI_COLOR_GREEN%
                        rem  type "%TXT_FILE%" |:u8 unique-lines -A -L  |:u8 insert-before-each-line "        "
                            (type "%TXT_FILE%" |:u8 unique-lines -A -L) |:u8 print-with-columns
                        @call divider
                        @call AskYn "[REDUNDANT?] Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%ANSWER%" eq "N" then
                                %color_removal%
                                ren  /q "%TXT_FILE%" "%TXT_FILE%.%_datetime.bak"
                                %color_normal%
                                @call warning "Aborting because you don't find the lyrics acceptable"
                                @call advice  "To skip lyrics and transcribe using only AI: %blink_on%%0 '%$' ai %emphasis%%deeomphasis%%blink_off%"
                                @call AskYn   "Go ahead and use AI anyway" no %AI_GENERATION_ANYWAY_WAIT_TIME%
                                if "%answer%" eq "Y" goto :Force_AI_Generation
                                goto :END
                        endiff
                endiff
        else
                rem This may be a bad way to deal with the situation:
                goto :check_for_txt_file
        endiff




:Force_AI_Generation
:AI_generation


REM if a text file of the lyrics exists, we need to engineer our AI transcription prompt with it to get better results
        rem 2023 version: set CLI_OPS=
        rem Not adding txt to output_format in case there were hand-edited lyrics that we don't want to overwrite already there
        rem CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words True  --beep_off --check_files --sentence --standard       --max_line_width 99 --ff_mdx_kim2 --verbose True
        rem CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words True  --beep_off --check_files --sentence --standard       --max_line_width 25 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files                             --max_line_width 30 --ff_mdx_kim2 --verbose True
        rem CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files --vad_max_speech_duration 6 --max_line_width 30 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files                             --max_line_width 30 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_threshold 0.35 --max_segment_length isn't even an option! 5
        :et CLI_OPS=--vad_filter false --model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_filter False   --max_segment_length isn't even an option! 5
        rem some tests with Destroy Boys - Word Salad & i threw glass at my... were done with 9 & 10
        rem 9:
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_filter False   
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --vad_filter False   -vad_threshold 0.35 --verbose True
rem     set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  -vad_threshold 0.35 --vad_max_speech_duration_s 5  --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 200
rem     rem 10v1: is better than 9 in one case, same in another
rem     set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_max_speech_duration_s 5  --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 201
rem     rem 11v2: worse than 9 or 10 definitely doesn't pick up on as many lyrics as prompt v9 prompt
rem     set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_max_speech_duration_s 5  --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 202 --vad_threshold 0.35
        rem 9v3: making vad_filter false requires taking out other vad-related args or it errors out
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --verbose True
        rem 9v4: seeing if --sentence still works with 9v3 ... may have to remove verbose?
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True
        rem 9v5:  let's experiment with maxlinecount=1
        :et CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True %PARAM_2% %3$
        rem THE IDEA GARBAGE CAN: 9v5:
        rem Possible improvements, but in practice missed like 2/3rds of X-Ray Spex - Oh Bondage, Up yours! (blooper live version from 2-cd set) whereas vad_filter=false did not
        rem --vad_max_speech_duration_s 5:     [default= ♾] Limits the maximum length of a speech segment to 5 seconds, forcing breaks if a segment runs too long.
        rem --vad_min_speech_duration_ms 500:  [default=250] Ensures that speech segments are at least 500ms long before considering a split.
        rem --vad_min_silence_duration_ms 300: [default=100] Splits subtitles at smaller pauses (300ms).
        rem --vad_speech_pad_ms 200:           [default= 30] Ensures a 200ms buffer around detected speech to avoid clipping.
        rem 9v6:  changing to use equals between some args
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True 
        rem Alas, completely disabling VAD filter results in major major major hallucinations during silence... Let's try turning it on again, sigh.
        rem 10v2: gave "unrecognized arguments: --vad_filter_threshold=0.2" oops it should be vad_threshold not vad_filter_threshold plus we had accidentally left vad_filter=False
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_filter_threshold=0.2 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v3: 
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.2 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v4:  lowering vad_threshold from 0.2 to 0.1 because of metal & punk with fast/hard vocals. May increase hallucations tho
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 11:  adding --best_of 5  and --vad_alt_method=pyannote_v3 & removed --ff_mdx_kim2 but this clearly gave worse lyrics, terrible ones, with Wet Leg – Girlfriend
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20               --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_alt_method=pyannote_v3 --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5
        rem 12:  going back to original --ff_mdx_kim2 vocal separation but keeping the best_of 5 ... Looks great?
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_alt_method=pyannote_v3 --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5
        rem 12v2:  reordering
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5
        rem 13: adding --max_comma_cent 70
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70
        rem 14: adding -hst 2 via Purview's advice to stop the thing where one subtitle gets stuck on for a whollleeee solooooo — it is short for --hallucination_silence_threshold  ... But it absolutely 100% does not solve that problem and gives output that causes concern for discarded lyrics. Have added logging the whisper output [and not just prompt] to the logfile to help track this...
        :et CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 -hst 2 
        rem 15: adding --max_gap 3.0 — Purfview said there is a --max_gap option -- default is 3.0 but i'm getting gaps way larger than that so I don't think it's being enforced so i'm going to explicitly add it
        set CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 -hst 2 --max_gap 3.0 
        rem 16b: adding --max_gap 3.0 — Purfview said there is a --max_gap option -- default is 3.0 but i'm getting gaps way larger than that so I don't think it's being enforced so i'm going to explicitly add it
        set CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 3.0 
        rem 17: try shortening max_gap
        set CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.1 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=198 --vad_dump --best_of 5 --max_comma_cent 70 --max_gap 2.0 

        set PROMPT_VERSION=17 %+ rem used in log files

        rem proposed: Purfview said there is a --max_gap option -- default is 3.0

        rem --vad_dump 
        rem     Enabling --vad_dump might reveal how changes to vad_window_size_samples affect VAD output and help approximate the default behavior based on responsiveness.                               
        rem --vad_alt_method 
        rem     Different music separation engines: [--vad_alt_method {silero_v3,silero_v4,pyannote_v3,pyannote_onnx_v3,auditok,webrtc}]
        rem --nullify_non_speech 
        rem     Avoiding Hallucinations: Sometimes, background noise or soft sounds may cause WhisperAI to “hallucinate” words. --nullify_non_speech helps eliminate this by focusing transcription on clearer speech.
        rem --max_new_tokens
        rem     Purpose: This option limits the maximum number of tokens that WhisperAI generates per segment.
        rem     How it Works: WhisperAI’s model produces text in tokens (small chunks of words or sounds), and --max_new_tokens restricts the number of tokens generated for each detected segment. When the token limit is reached, transcription stops for that segment and moves on to the next.
        rem     When to Use It:
        rem     Control Segment Length: If you’re transcribing long audio files, especially ones with background noise, this option prevents overly long transcriptions for a single detected speech segment, helping keep segments manageable and aligned with the audio.
        rem     Reduce Noise-Induced Errors: In noisy environments, background sounds may stretch a transcription segment unnecessarily. --max_new_tokens allows you to limit the impact of background noise by truncating overly long sections.
        rem     Improve Processing Speed: Setting a lower max_new_tokens value can reduce the time spent on ambiguous or prolonged segments. This is useful if you’re prioritizing speed and only need shorter, precise snippets of audio transcribed.
        rem --vad_window_size_samples VAD_WINDOW_SIZE_SAMPLES
        rem     A typical starting point for vad_window_size_samples is 10 ms to 30 ms of audio data, which would correspond to sample counts based on the audio's sampling rate (for example, 441 samples for 10 ms at a 44.1 kHz sample rate). You could try values within this range to see how they affect detection sensitivity and stability.
        rem --vad_threshold
        rem         Lower the VAD threshold to 0.35 or 0.3 to capture more detail.
        rem --vad_filter_off
        rem         Disable VAD filtering with --vad_filter_off to ensure the whole audio is processed without aggressively skipping sections.
        rem --max_comma_cent 70
        rem         Roughly, break the subtitle at a comma... I think 70 is if it's 70% through the line but i'm probably wrong

        rem NOTE: We also have --batch_recursive - {automatically sets --output_dir}


        if not exist %TXT_FILE% .or. %SKIP_TEXTFILE_PROMPTING eq 1 .or. (1 eq %SOLELY_BY_AI .and. 1 ne %AUTO_LYRIC_APPROVAL%) (goto :No_Text)
                rem the text file %TXT_FILE% does in fact exist!
                setdos /x-1
                        rem 2023 method: set CLI_OPS=%CLI_OPS% --initial_prompt "Transcribe this audio, keeping in mind that I am providing you with an existing transcription, which may or may not have errors, as well as header and footer junk that is not in the audio you are transcribing. Lines th at say 'downloaded from' should definitely be ignored. So take this transcription lightly, but do consider it. The contents of the transcription will have each line separated by ' / '.   Here it is: ``
                        rem set CLI_OPS=%CLI_OPS% --initial_prompt "Transcribe this audio, keeping in mind that I am providing you with an existing transcription, which may or may not have errors, as well as header and footer junk that is not in the audio you are transcribing. Lines th at say 'downloaded from' should definitely be ignored. So take this transcription lightly, but do consider it. The contents of the transcription will have each line separated by ' / '.   Here it is: ``
                        rem 2024: have learned prompt is limited to 224 tokens and should really just be a transcription
                        rem set WHISPER_PROMPT=--initial_prompt "
                        rem @Echo off
                        rem DO line IN @%TXT_FILE (
                        rem         set WHISPER_PROMPT=%WHISPER_PROMPT% %@REPLACE[%QUOTE%,',%line]
                        rem         REM @echo %faint%adding line to prompt: %italics%%line%%italics_off%%faint_off%
                        rem )

                        rem Smush the lyrics into a single line (no line breaks) set of unique lines:
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE[%TXT_FILE]" | uniq | paste.exe -sd " " -]]
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE[%TXT_FILE]" | awk "!seen[$0]++" | paste.exe -sd " " -]]
                                rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE[%TXT_FILE]" | awk "!seen[$0]++" ]] .... This was getting unruly, wrote a perl script that like 'uniq', but more for this specific situation
                                set OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE[%TXT_FILE]" |:u8 unique-lines.pl -1 -L]] %+ rem unique-lines.pl is actually our lyric postprocessor
                                set OUR_LYRICS_TRUNCATED=%@LEFT[%MAXIMUM_PROMPT_SIZE%,%OUR_LYRICS%]

                        rem Add the lyrics to our existing whisper prompt:
                                set WHISPER_PROMPT=--initial_prompt "%OUR_LYRICS_TRUNCATED%"
                                rem @echo %ANSI_COLOR_DEBUG%Whisper_prompt is:%newline%%tab%%tab%%faint_on%%WHISPER_PROMPT%%faint_off%%ANSI_COLOR_NORMAL%

                        rem Leave a hint to future-self, because we definitely do "env whisper" to look into the environment to find the whisper prompt last-used, for when we want to do minor tweaks... And remembering --batch_recursive is hard 😂
                                set WHISPER_PROMPT_ADVICE_NOTE_TO_SELF______________________________=*********** FOR RECURSIVE: do %%whisper_prompt%% but instead of the filename do --batch_recursive *.mp3

                        rem Preface our whisper prompt with our hard-coded default command line options from above:
                                set CLI_OPS=%CLI_OPS% %WHISPER_PROMPT%
                setdos /x0
        :No_Text






rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////
REM        REM demucs vocals out (or not——we don't do this in 2024):
REM                                        if %SKIP_SEPARATION eq 1 (goto :Vocal_Separation_Skipped)
REM                                        if exist %VOC_FILE% (
REM                                            @call warning "Vocal file '%italics%%VOC_FILE%%italics_off%' %underline%already%underline_off% exists! Using it..."
REM                                            goto :Vocal_Separation_Done
REM                                        )
REM                                    REM do it
REM                                        :Vocal_Separation
REM                                        @call unimportant "Checking to see if demuexe.exe music-vocal separator is in the path ... For me, this is in anaconda3\scripts as part of Python" %+ call validate-in-path demucs.exe
REM                                        REM mdx_extra model is way slower but in tneory slightly more accurate to use default, just set model= -- lack of parameter will use default Demucs 3 (Model B) may be best (9.92) which apparently mdx_extra is model b whereas mdx_extra_q is model b quantized faster but less accurate. but it's fast enough already!
REM                                            set MODEL_OPT= %+  set MODEL_OPT=-n mdx_extra 
REM                                        REM actually demux the vocals out here
REM                                            %color_run% %+ @Echo ON %+ demucs.exe --filename "%_CWD\%VOC_FILE%" %MODEL_OPT% --verbose --device cuda --float32 --clip-mode rescale   "%SONGFILE%" %+ @Echo OFF
REM                                            CALL errorlevel "Something went wrong with demucs.exe"
REM                                    REM validate if the vocal file was created, and remove demucs cruft           
REM                                        call validate-environment-variable VOC_FILE "demucs separation did not produce the expected file of '%VOC_FILE%'"
REM                                        :Vocal_Separation_Done
REM                                            set INPUT_FILE=%VOC_FILE% %+  SET EXPECTED_OUTPUT_FILE=%LRCFILE2% %+ if "%2" ne "keep" .and. isdir separated (rd /s /q separated)
REM        :Vocal_Separation_Skipped
rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////


REM does our input file exist?
        call validate-environment-variable  INPUT_FILE

REM Assemble the full command-line to transcribe the file:
        set LAST_WHISPER_COMMAND=%TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%"    



REM Backup any existing SRT file, and ask if we are sure we want to generate AI right now:
        :backup any existing one
        if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
        
        :actually_make_the_lrc
        @echos %STAR% %ANSI_COLOR_WARNING_SOFT%%blink_on%About to: %blink_off%
        @echo  %LAST_WHISPER_COMMAND%%ansi_color_reset% 
        @call AskYn "Proceed with this AI generation?" yes %PROMPT_CONSIDERATION_TIME%
        iff "%answer%" eq "N" then
                @call warning "Aborting because you changed your mind..."
                sleep 1
                goto :END
        endiff



REM quick chance to edit prompt:
        @call AskYn "Edit the AI prompt?" no %PROMPT_EDIT_CONSIDERATION_TIME%
        iff "%answer%" eq "Y" (eset LAST_WHISPER_COMMAND)



REM Concurrency Consideration: Check if the encoder is already running in the process list. Don't run more than 1 at once.
        rem slower call isRunning %TRANSCRIBER_PRNAME% silent
        rem slower if "%isRunning" != "1" (goto :no_concurrency_issues)
        rem faster:
        rem echo %ANSI_COLOR_DEBUG%- DEBUG: (4) iff @PID[TRANSCRIBER_PDNAME=%TRANSCRIBER_PDNAME%] %@PID[%TRANSCRIBER_PDNAME%] ne 0 then %ANSI_COLOR_NORMAL%
        set CONCURRENCY_WAS_TRIGGERED=0        
        iff "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then
                @echo %ansi_color_warning_soft%%star% %italics_on%%TRANSCRIBER_PDNAME%%italics_off is already running%ansi_color_normal%
                @echos %ANSI_COLOR_WARNING_SOFT%%STAR% Waiting for completion of %italics_on%another%italics_on% instance of %italics_on%%@cool[%TRANSCRIBER_PDNAME%]%italics_off% %ansi_color_warning_soft%to finish before starting this one...%ANSI_COLOR_NORMAL%
                set CONCURRENCY_WAS_TRIGGERED=1
        else 
                goto :no_concurrency_issues
        endiff

        :Check_If_Transcriber_Is_Running_Again
                @echos %@randfg_soft[].
                rem Wait a random number of seconds to lower the odds of multiple waiting processes seeing an opening and all starting at the same time]:
                sleep %@random[7,29] 
                rem slow: call isRunning %TRANSCRIBER_PRNAME% silent
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: (55) if "@PID[TRANSCRIBER_PDNAME]" (which is "@PID[%transcriber_pdname]" which is "%@PID[%TRANSCRIBER_PDNAME]") ne 0 (goto :Check_If_Transcriber_Is_Running_Again)%ANSI_COLOR_NORMAL%
                rem echo if "@PID[%TRANSCRIBER_PDNAME%]" ne "0" (goto :Check_If_Transcriber_Is_Running_Again)
                if "%@PID[%TRANSCRIBER_PDNAME%]" ne "0" (goto :Check_If_Transcriber_Is_Running_Again)
                @echo %ansi_color_green%...%ansi_color_bright_green%Done%blink_on%!%blink_off%%ansi_reset%
        :no_concurrency_issues
        
REM set a non-scrollable header on the console to keep us from getting confused about which file / what we're doing / etc
        rem call top-message Transcribing %FILE_TITLE% by %FILE_ARTIST%
        set LOCKED_MESSAGE_COLOR_BG=%@ANSI_BG[0,0,64]                               %+ rem copied from top-banner.bat
        rem banner_message=%@randfg_soft[]%ALOCKED_MESSAGE_COLOR_BG%%ZZZZZZZZ%AI-Transcribing%faint_off% %ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%'%italics_on%%FILE_TITLE%%italics_off%' %faint_on%%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%by%faint_off% %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%ZZZZZZZZ%%@cool[%FILE_ARTIST%]%%ZZZZZZZZZ%
        iff not defined FILE_ARTIST .and. 1 ne %SOLELY_BY_AI then
            call warning "FILE_ARTIST  is not defined here and should generally be, since SOLELY_BY_AI=%SOLELY_BY_AI%"
            set FILE_ARTIST= ``
            rem eset FILE_ARTIST
            rem pause
        endiff
        call divider %+ set banner_message=%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%faint_on%AI-Transcribing%faint_off% %ansi_color_important%%LOCKED_MESSAGE_COLOR_BG%'%italics_on%%FILE_TITLE%%italics_off%' %faint_on%%@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%by%faint_off% %@randfg_soft[]%LOCKED_MESSAGE_COLOR_BG%%blink_on%%@cool[%FILE_ARTIST%]%%blink_off%
        rem BRING BACK AFTER I FIX THE BANNER: call top-banner "%banner_message%"
        rem instead do this temporarily: 🐐🐐
                call important "%banner_message%"


REM actually generate the SRT file [used to be LRC but we have now coded specifically to SRT] —— start AI:
        rem Cosmetics:
            @echo.
            @call bigecho %ANSI_COLOR_BRIGHT_RED%%EMOJI_FIREWORKS% AI running! %EMOJI_FIREWORKS%%ansi_color_normal%
            title waiting: %BASE_TITLE_TEXT%

        rem One last concurrency check:
                iff "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then
                        echo %ANSI_COLOR_WARNING% Actually, it's still running! %ANSI_RESET%
                        goto :Check_If_Transcriber_Is_Running_Again
                else
                        rem One last extra random wait in case 2 different ones get here at the same time. 
                        rem (And only do this if we already had to wait before):
                                iff %CONCURRENCY_WAS_TRIGGERED% eq 1 then
                                        sleep %@random[7,29]                    
                                endiff
                endiff

        rem Determine log file name:
                set OUR_LOGFILE=%@NAME[%@UNQUOTE[%INPUT_FILE]].log

        rem Store command, run command, check for error response, and log command:
                title %EMOJI_EAR%%BASE_TITLE_TEXT%
                if %LOG_PROMPTS_USED% eq 1 (@echo %newline%%EMOJI_EAR% %_DATETIME: prompt v%PROMPT_VERSION%: %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%" >>:u8"%OUR_LOGFILE%")

        rem A 3rd concurrency check became necessary in my endeavors:
                if "%@PID[%TRANSCRIBER_PDNAME%]" != "0" goto :Check_If_Transcriber_Is_Running_Again %+ rem yes, a 3rd concurrency check at the very-very last second!

        rem ACTUALLY DO IT!!!:
                option //UnicodeOutput=yes
                rem %LAST_WHISPER_COMMAND% |:u8 copy-move-post whisper 
                rem %LAST_WHISPER_COMMAND% |:u8 copy-move-post whisper |&:u8 tee /a "%OUR_LOGFILE%"
                    %LAST_WHISPER_COMMAND% |:u8 copy-move-post whisper |&:u8 tee.exe --append "%OUR_LOGFILE%"
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                goto :Done_Transcribing            %+ rem  \____ If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                :Done_Transcribing                 %+ rem  /     If this seems ridiculous, it is because we want to make sure we don't lose our place in this script if the script has been modified during running. It's probably a hopeless endeavor to recover from that.
                option //UnicodeOutput=%UnicodeOutputDefault%
                echos %TOCK%                       %+ rem just our nickname for an extra-special ansi-reset
                call errorlevel "some sort of problem with the AI generation occurred in %0 line ~336ish {'actually generate the srt file'}"

        rem Cosmetics:
                call unlock-top                    %+ rem Disable our non-scrollable header now that we are done
                title Done: %BASE_TITLE_TEXT%

REM delete zero-byte LRC files that can be created
        call delete-zero-byte-files *.lrc silent >nul
        call delete-zero-byte-files *.srt silent >nul
        
REM Post-process the SRT file:
rem Remove periods from the end of each line in the SRT, but preserve them if at the end of a common word like "Mr.", "Ms.", or if "...":
        echos %ANSI_COLOR_IMPORTANT_LESS%%STAR% Postprocessing %italics_on%LRC%italics_off% and %italics_on%SRT%italics_off% files...
        if exist "%LRC_FILE%" (remove-period-at-ends-of-lines.pl -w "%LRC_FILE%")
        if exist "%SRT_FILE%" (remove-period-at-ends-of-lines.pl -w "%SRT_FILE%")
        echo ...%CHECK% %ANSI_COLOR_GREEN%Success%BOLD_ON%!%BOLD_OFF%%ANSI_COLOR_NORMAL%

REM did we create the LRC file?
        call validate-environment-variable EXPECTED_OUTPUT_FILE "expected output file of '%italics%%EXPECTED_OUTPUT_FILE%%italics_off%' does not exist"
        if exist "%@UNQUOTE[%EXPECTED_OUTPUT_FILE%]" (@echo %EXPECTED_OUTPUT_FILE%%::::%_DATETIME%::::%TRANSCRIBER_TO_USE% >>:u8"__ contains AI-generated SRT files __")
        title %CHECK%%BASE_TITLE_TEXT%

rem If we did, we need to rename any sidecar TXT file that might be there {from already-having-existed}, becuase 
rem MiniLyrics will default to displaying TXT over SRC
        rem NO NOT ANYMORE if exist "%TXT_FILE%" (ren /q "%TXT_FILE%" "%TXT_FILE.bak.%_datetime" )


rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////
iff 1 eq %USE_2023_LOGIC then
                        REM rename the file & delete the vocal-split wav file
                            iff "%EXPECTED_OUTPUT_FILE%" ne "%LRC_FILE%" then
                                set MOVE_DECORATOR=%ANSI_GREEN%%FAINT%%ITALICS% 
                                mv "%EXPECTED_OUTPUT_FILE%" "%LRC_FILE%"
                            endiff
                            call validate-environment-variable LRC_FILE "LRC file not found around line 123ish"
                            if exist "%LRC_FILE%" .and. "%2" ne "keep" (*del /q /r "%VOC_FILE%")
endiff
rem ///////////////////////////////////////////// OLD DEPRECATECD CODE /////////////////////////////////////////////



goto :Cleanup



            :say_if_exists [it]
                    if not defined %[it] (@call error "say_if_exists called but it of '%it%' is not defined")
                    set filename=%[%[it]]
                    iff exist %filename then
                            set BOOL_DOES=1 %+ set does_punctuation=: %+ set does=%BOLD%%UNDERLINE%%italics%does%italics_off%%UNDERLINE_OFF%%BOLD_OFF%    ``
                    else
                            set BOOL_DOES=0 %+ set does_punctuation=: %+ set does=does %FAINT%%ITALICS%%blink%not%blink_off%%ITALICS_OFF%%FAINT_OFF%
                    endiff
                    %COLOR_IMPORTANT_LESS%
                            if %BOOL_DOES eq 0 (set DECORATOR_ON=  %strikethrough% %+ set DECORATOR_OFF=%strikethrough_off%)
                            if %BOOL_DOES eq 1 (set DECORATOR_ON=%PARTY_POPPER%    %+ set DECORATOR_OFF=%PARTY_POPPER%     )
                            @echos * %it% %does% exist%does_punctuation% %FAINT%%decorator_on%%filename%%decorator_off%%FAINT_OFF%
                    %COLOR_NORMAL%
                    @echo.
            return


rem ////////////////////////////////////////////////////////////////////////////////////////////////////////////////


:Finishing_Up
:Cleanup

rem Let user know if we were NOT succesful, then skip to the end:
        iff not exist "%SRT_FILE%" then
                @call warning "Unfortunately, we could create the karaoke file %emphasis%%SRT_FILE%%deemphasis%"
                title %emoji_warning% Karaoke not generated! %emoji_warning% 
                goto :nothing_generated
        endiff


rem Cleanup:
        rem MiniLyrics will pick up a TXT file in the %lyrics% repo *instead* of a SRT file in the local folder
        rem   for sure: in the case of %lyrics%\letter\<same name as audio file>.txt  ——— MAYBE_LYRICS_2
        rem      maybe: in the case of %lyrics%\letter\artist - title.txt             ——— MAYBE_LYRICS_1
        rem So we must delete at least the first one, if it exists.  We use our get-lyrics script in SetVarsOnly mode:
        rem moved to beginning: call get-lyrics-via-multiple-sources "%SONGFILE%" SetVarsOnly
        rem ...which sets MAYBE_LYRICS_1 and MAYBE_LYRICS_2
        echo %ansi_color_debug%- DEBUG: (7) Checking if exists: '%underline_on%%MAYBE_LYRICS_2%%underline_off%' for deprecation%ansi_color_normal%
        iff exist "%MAYBE_LYRICS_2%" then
                rem call deprecate "%MAYBE_LYRICS_2%"
                set NEWNAME=%@NAME[%MAYBE_LYRICS_2%].lyr
                iff exist "%NEWNAME%" then
                        call deprecate "%MAYBE_LYRICS_2%"
                        rem  deprecate changes the extension to ".dep"/".deprecated" and is just a way of almost-deleting files
                else
                        ren "%MAYBE_LYRICS_2%" "%NEWNAME%"
                endiff
        endiff
        



rem Success SRT-generation message:
        @call divider
        @call success "Karaoke created at: %blink_on%%italics_on%%emphasis%%SRT_FILE%%deemphasis%%ANSI_RESET%"
        title %check% %BASE_TITLE_TEXT% generated successfully! %check% 
        if %SOLELY_BY_AI eq 1 (call warning "ONLY AI WAS USED. Lyrics were not used for prompting" silent)



rem A chance to edit:
        @echo.
        rem TODO don't do this *always*:
        iff "%LYRICS_ACCEPTABLE%" != "0" then
                iff not exist "%TXT_FILE%" then
                        echo %ansi_color_warning_soft%%star% Lyrics were approved but can't find '%italics_on%%TXT_FILE%%italics_on%'%ansi_reset%
                else
                        @call divider
                        @call bigecho %ANSI_COLOR_BRIGHT_GREEN%%check%  %underline_on%Lyrics%underline_off%:
                        (type "%TXT_FILE%" |:u8 unique-lines -A -L)|:u8 print-with-columns
                endiff
        endiff
        @call divider
        @call bigecho %ANSI_COLOR_BRIGHT_GREEN%%check%  %underline_on%Transcription%underline_off%:
        @echo.
        @echos %TOCK%                       %+ rem just our nickname for an extra-special ansi-reset we sometimes call after  copy-move-post.py postprocessing
        rem fast_cat fixes ansi rendering errors ins ome situations
        rem  (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line "%faint_on%%ansi_color_red%SRT:%faint_off%%ansi_color_bright_Green%        "     |:u8 fast_cat
        rem  (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line.py  "SRT:        %CHECK%" |:u8 fast_cat
        rem  (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line.py  "%check%%ansi_color_green% SRT: %@cool[-------->] %ANSI_COLOR_bright_yellow%
        rem  (grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%SRT_FILE%")  |:u8 insert-before-each-line.py  "%check%%ansi_color_green% SRT: %@cool[-------->] %ANSI_COLOR_bright_yellow%
             (grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%SRT_FILE%")  |:u8 print-with-columns 
        @echo.
        if defined TOCK (echos %TOCK%) %+ rem nickname for fancy ansi-reset

rem Full-endeavor success message:
        @call divider
        @call success "'%italics_on%%BASE_TITLE_TEXT%%italics_off%' generated successfully!"
        title %check% %BASE_TITLE_TEXT% generated successfully! %check%             
        @call askyn  "Edit SRT file [in case there were mistakes above]" no %EDIT_KRAOKE_AFTER_CREATION_WAIT_TIME% notitle
        iff "%ANSWER" == "Y" then
                @echo %ANSI_COLOR_DEBUG%%EDITOR% "%SRT_FILE%" [and maybe "%TXT_FILE%"] %ANSI_RESET%
                title %check% %BASE_TITLE_TEXT% generated successfully! %check%             
                iff not exist "%TXT_FILE%" then
                        %EDITOR% "%SRT_FILE%" 
                else
                        %EDITOR% "%TXT_FILE%" "%SRT_FILE%" 
                endiff
        endiff
        title %check% %BASE_TITLE_TEXT% generated successfully! %check%             
        if %SOLELY_BY_AI eq 1 (call warning "ONLY AI WAS USED. Lyrics were not used for prompting")

:END
:nothing_generated
echos %ansi_color_unimportant%
timer /5 off
echos %ansi_color_reset%


:Cleanup_Only
:just_do_the_cleanup
        set MAKING_KARAOKE=0
        unset /q LYRICS_ACCEPTABLE
        unset /q OKAY_THAT_WE_HAVE_SRT_ALREADY
        if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav >nul)
        if exist     *vad_original*.srt (*del /q     *vad_original*.srt >nul)

        rem This happens earlier, but we also want it to happen in cleanup, because sometimes cleanup is called from transcribed stuff *NOT* made with this script:
                iff %CLEANUP eq 1 then
                        call delete-zero-byte-files *.lrc silent >nul
                        call delete-zero-byte-files *.srt silent >nul
                endiff

:The_Very_END
        @echos %ANSI_COLOR_BLUE%%FAINT_ON%
        @echos %ANSI_RESET%%CURSOR_RESET%
