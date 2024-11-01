@Echo off

rem TODO if lyrics are approved already, don't ask about them
rem TODO maybe add NoLyrics mode to not consider lyrics?

:USAGE: lrc.bat whatever.mp3 {force|ai} {options to pass on to whisper} ... ai=force ai regeneration, force=proceed even if LRC file is there
:USAGE: set USE_LANGUAGE=jp to encode in a different language from en, like jp

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
rem CONFIG: 2024: WAIT TIMES:
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=120                 %+ rem wait time for "are these lyrics good?"-type questions
        set AI_GENERATION_ANYWAY_WAIT_TIME=45                        %+ rem wait time for "no lyrics, gen with AI anyway"-type questions
        set REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME=45      %+ rem wait time for "we already have karaoke, regen anyway?"-type questions
        set PROMPT_CONSIDERATION_TIME=15                             %+ rem wait time for "does this AI command look sane"-type questions
        set WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST=1       %+ rem wait time for "hey lyrics not found!"-type notifications/questions
        set EDIT_KRAOKE_AFTER_CREATION_WAIT_TIME=300                 %+ rem wait time for "edit it now that we've made it?"-type questions ... Have decided it should probably last longer than the average song
        rem ^^^^ TODO: automation mode where all these get shortened to quite significantly, or all to 3, or all to 1, or something 🐮

REM config: 2023:
        rem set TRANSCRIBER_TO_USE=call whisper-faster.bat 
        rem set SKIP_SEPARATION=0         
        rem SET SKIP_TEXTFILE_PROMPTING=0  

 
REM Pre-run cleanup:
        timer /5 on                     %+ rem Let's time the overall process
        @call tock                      %+ rem purely cosmetic
        unset /q LYRIC_ATTEMPT_MADE
        unset /q OKAY_THAT_WE_HAVE_SRT_ALREADY
        if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav)
        if exist     *vad_original*.srt (*del /q     *vad_original*.srt)

REM validate environment [once]:
        iff 1 ne %VALIDATED_CREATE_LRC_FF then
                rem 2023 versin: call validate-in-path whisper-faster.bat debug.bat
                @call validate-in-path               %TRANSCRIBER_TO_USE%  get-lyrics.bat  debug.bat  lyricy.exe  copy-move-post  unique-lines.pl  paste.exe  divider  less_important  insert-before-each-line  bigecho  deprecate  errorlevel  grep  isRunning fast_cat
                @call validate-environment-variables FILEMASK_AUDIO COLORS_HAVE_BEEN_SET QUOTE emphasis deemphasis ANSI_COLOR_BRIGHT_RED check ansi_color_bright_Green ansi_color_Green ANSI_COLOR_NORMAL ansi_reset cursor_reset underline_on underline_off faint_on faint_off EMOJI_FIREWORKS star check emoji_warning TRANSCRIBER_PDNAME ansi_color_warning_soft ANSI_COLOR_BLUE
                @call validate-is-function           randfg_soft
                @call checkeditor
                @set VALIDATED_CREATE_LRC_FF=1
        endiff


REM branch on certain paramters, and clean up various parameters 
        set PARAM_2=%2
        if "%1" eq "last" (goto :actually_make_the_lrc)
        set FORCE_REGEN=0
        if "%2" eq "force-regen" .or. "%2" eq "redo" (set FORCE_REGEN=1 %+ set PARAM_2=) %+ rem Any %2 that is a mode needs to get "the param_2 treatment" 
        if "%2" eq "ai" (set PARAM_2=)                                                   %+ rem Any %2 that is a mode needs to get "the param_2 treatment"
        set MAKING_KARAOKE=1
        if defined USE_LANGUAGE (set OUR_LANGUAGE=%USE_LANGUAGE%)




REM values set from parameters
        set             SONGFILE=%@UNQUOTE[%1]
        set             SONGBASE=%@NAME[%SONGFILE]
        set POTENTIAL_LYRIC_FILE=%@UNQUOTE[%2]
        set LRC_FILE=%SONGBASE%.lrc
        set SRT_FILE=%SONGBASE%.srt
        set TXT_FILE=%SONGBASE%.txt
        set JSN_FILE=%SONGBASE%.json
        rem VOC_FILE=%SONGBASE%.vocals.wav
        rem LRCFILE2=%SONGBASE%.vocals.lrc

REM our main input and output files
        set INPUT_FILE=%SONGFILE%
        rem EXPECTED_OUTPUT_FILE=%LRC_FILE%   %+ rem //This was for the 2023 version
        SET EXPECTED_OUTPUT_FILE=%SRT_FILE%



REM if 2nd parameter is lyric file, use that one:
        iff exist "%POTENTIAL_LYRIC_FILE%" then
                set TXT_FILE=%POTENTIAL_LYRIC_FILE%
                @call less_important "Using existing transcription file: %italics_on%%TXT_FILE%%italics_off%"
                goto :AI_generation
        endiff




REM display debug info
        :Retry_Point
        @call debug "%NEWLINE%    SONGFILE='%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%':%NEWLINE%    SONGFILE='%ITALICS_ON%%DOUBLE_UNDERLINE%%SONGFILE%%UNDERLINE_OFF%%ITALICS_OFF%':%NEWLINE%%TAB%%TAB%%FAINT_ON%SONGBASE='%ITALICS_ON%%SONGBASE%%ITALICS_OFF%'%NEWLINE%%TAB%%TAB%LRC_FILE='%ITALICS_ON%%LRC_FILE%%ITALICS_OFF%', %NEWLINE%%TAB%%TAB%TXT_FILE='%ITALICS_ON%%TXT_FILE%%ITALICS_OFF%'%FAINT_OFF%%NEWLINE%"
        rem @echo Hello?!?!?!
        gosub say_if_exists SONGFILE
        gosub say_if_exists SRT_FILE
        gosub say_if_exists LRC_FILE
        rem   say_if_exists LRCFILE2
        gosub say_if_exists TXT_FILE
        rem   say_if_exists VOC_FILE
        gosub say_if_exists JSN_FILE
        @echo.



REM if our input MP3/FLAC/audio file doesn't exist, we have problems:
        call validate-environment-variable INPUT_FILE
        call validate-file-extension     "%INPUT_FILE%" %FILEMASK_AUDIO%



REM if we already have a SRT file, we have a problem:
        iff exist "%SRT_FILE%" .and. %OKAY_THAT_WE_HAVE_SRT_ALREADY ne 1 then
                iff exist "%TXT_FILE%" then
                        @call divider
                        @call less_important "(5) Review the lyrics now:" 0
                        @call divider
                        @echos %ANSI_COLOR_BRIGHT_YELLOW%
                        rem unique-lines -A is a bit of a misnomer because it gives ALL lines, but with -L it gives us a preview of some of the lyric massage prior to the AI prompt
                        type "%TXT_FILE%" |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                        @call divider
                endiff
                @call bigecho %ansi_color_warning%%emoji_warning%Already have karaoke!%emoji_warning%%ansi_color_normal%
                @call warning "We already have a file created: %emphasis%%srt_file%%deemphasis%"
                @call advice "Automatically answer the next prompt as Yes by adding the parameter 'force-regen' or 'redo'"
                iff exist "%TXT_FILE%" then
                        @call AskYn "(5) Do the above lyrics look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%answer%" eq "Y" then
                                rem Proceed with process
                        else
                                ren /q "%TXT_FILE%" "%@NAME[%TXT_FILE%].txt.%_datetime.bak" >nul
                                @call less_important "Okay, let's try fetching new lyrics"
                                goto :Refetch_Lyrics
                        endiff
                endiff
                rem FORCE_REGEN is %FORCE_REGEN %+ pause
                iff %FORCE_REGEN% ne 1 then
                        @call askYN "Regenerate it anyway?" no %REGENERATE_SRT_AGAIN_EVEN_IF_IT_EXISTS_WAIT_TIME%
                endiff
                iff "%ANSWER%" eq "Y" .or. %FORCE_REGEN eq 1 then
                        iff exist "%SRT_FILE%" then
                                ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak" >nul
                        endiff
                        set OKAY_THAT_WE_HAVE_SRT_ALREADY=1
                        goto :Force_AI_Generation
                else
                        @call warning_soft "Not generating anything, then..."
                        goto :END
                endiff
        endiff





REM If we say "ai" after the command, we nuke the LRC/SRT file and go straight to AI-generating:
        iff "%2" eq "ai" then
                @call important_less "Forcing AI generation..."
                if exist "%LRC_FILE%" (ren /q "%LRC_FILE%" "%@NAME[%LRC_FILE%].lrc.%_datetime.bak")
                if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
                set SKIP_TEXTFILE_PROMPTING=1
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
                        rem if exist %LRC_FILE% (@call error   "Sorry, but %bold%LRC%bold_off% file '%italics%%LRC_FILE%%italics_off%' %underline%already%underline_off% exists!" %+ cancel)
                            if exist %LRC_FILE% (@call warning "Sorry, but %bold%LRC%bold_off% file '%italics%%LRC_FILE%%italics_off%' %underline%already%underline_off% exists!" %+ goto :END)

        endiff



:attempt_to_download_LRC
        REM FAILED: Let's NOT try downloading a LRC with lyricy first because it gets mismatches whenever none exists, which is almost always:
               rem call get-lrc-with-lyricy "%CURRENT_SONG_FILE%"
               rem if exist %LRC_FILE% (@call success "Looks like %italics_on%lyricy%italics_off% found an LRC for us!" %+ goto :END)




REM If it's an instrumental, don't bother:
        if "%@REGEX[instrumental,%INPUT_FILE%]" eq "1" (@call warning "Sorry, nothing to transcribe because this appears to be an instrumental: %INPUT_FILE%" %+ goto :END)





REM In terms of automation, as of 10/28/2024 we are only comfortable with FULLY automatic (i.e. going through a whole playlist) generation
REM in the event that a txt file also exists.  To enforce this, we will only generate with a "force" parameter if the txt file does not exist.
        :check_for_txt_file



        iff not exist "%TXT_FILE%" .and. "%2" ne "Force" .and. 1 eq %LYRIC_ATTEMPT_MADE then
                @call warning "Failed to generate %emphasis%%SRT_FILE%%deemphasis%%ansi_color_warning% because %emphasis%%TXT_FILE%%deemphasis%%ansi_color_warning% lryics do not exist and could not be downloaded! Use 'ai' option to go straight to AI generation."
                rem @call pause-for-x-seconds 20
                @call askYN "Generate AI anyway" no %AI_GENERATION_ANYWAY_WAIT_TIME%
                if "%ANSWER%" eq "Y" (goto :Force_AI_Generation)
                goto :END
        else
                @echo %ansi_color_warning_soft%%star% Not yet generating %emphasis%%SRT_FILE%%deemphasis%%ansi_color_warning_soft% because %emphasis%%TXT_FILE%%deemphasis%%ansi_color_warning_soft% does not exist!%ansi_color_normal%
                @call advice       "Use 'force' option to override."
                @call advice       "Try to get the lyrics first. SRT-generation is most accurate if we also have a TXT file of lyrics!"
                @call pause-for-x-seconds %WAIT_TIME_ON_NOTICE_OF_LYRICS_NOT_FOUND_AT_FIRST%
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
                        type "%TXT_FILE%" |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                        @call divider
                        @call AskYn "[REDUNDANT?] Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%ANSWER%" eq "N" then
                                %color_removal%
                                ren  /q "%TXT_FILE%" "%TXT_FILE%.%_datetime.bak"
                                %color_normal%
                                @call warning "Aborting because you don't find the lyrics acceptable"
                                @call advice  "To skip lyrics and transcribe using only AI: %blink_on%%0 '%1' ai %emphasis%%deeomphasis%%blink_off%"
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
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files                             --max_line_width 30 --ff_mdx_kim2 --verbose True
        rem CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files --vad_max_speech_duration 6 --max_line_width 30 --ff_mdx_kim2 --verbose True
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files                             --max_line_width 30 --ff_mdx_kim2 --verbose True
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_threshold 0.35 --max_segment_length isn't even an option! 5
        set CLI_OPS=--vad_filter false --model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_filter False   --max_segment_length isn't even an option! 5
        rem some tests with Destroy Boys - Word Salad & i threw glass at my... were done with 9 & 10
        rem 9:
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_filter False   
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --vad_filter False   -vad_threshold 0.35 --verbose True
rem     set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  -vad_threshold 0.35 --vad_max_speech_duration_s 5  --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 200
rem     rem 10v1: is better than 9 in one case, same in another
rem     set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_max_speech_duration_s 5  --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 201
rem     rem 11v2: worse than 9 or 10 definitely doesn't pick up on as many lyrics as prompt v9 prompt
rem     set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --highlight_words False --beep_off --check_files          --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --verbose True  --vad_max_speech_duration_s 5  --vad_min_speech_duration_ms 500 --vad_min_silence_duration_ms 300 --vad_speech_pad_ms 202 --vad_threshold 0.35
        rem 9v3: making vad_filter false requires taking out other vad-related args or it errors out
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --verbose True
        rem 9v4: seeing if --sentence still works with 9v3 ... may have to remove verbose?
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 2 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True
        rem 9v5:  let's experiment with maxlinecount=1
        set CLI_OPS=--model large-v2 --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True %PARAM_2% %3$
        rem THE IDEA GARBAGE CAN: 9v5:
        rem Possible improvements, but in practice missed like 2/3rds of X-Ray Spex - Oh Bondage, Up yours! (blooper live version from 2-cd set) whereas vad_filter=false did not
        rem --vad_max_speech_duration_s 5:     [default= ♾] Limits the maximum length of a speech segment to 5 seconds, forcing breaks if a segment runs too long.
        rem --vad_min_speech_duration_ms 500:  [default=250] Ensures that speech segments are at least 500ms long before considering a split.
        rem --vad_min_silence_duration_ms 300: [default=100] Splits subtitles at smaller pauses (300ms).
        rem --vad_speech_pad_ms 200:           [default= 30] Ensures a 200ms buffer around detected speech to avoid clipping.
        rem 9v6:  changing to use equals between some args
        set CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True 
        rem Alas, completely disabling VAD filter results in major major major hallucinations during silence... Let's try turning it on again, sigh.
        rem 10v2: gave "unrecognized arguments: --vad_filter_threshold=0.2" oops it should be vad_threshold not vad_filter_threshold plus we had accidentally left vad_filter=False
        set CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter False  --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_filter_threshold=0.2 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump
        rem 10v3: 
        set CLI_OPS=--model=large-v2 %PARAM_2% %3$ --language=%OUR_LANGUAGE% --output_dir "%_CWD" --output_format srt --vad_filter True   --max_line_count 1 --max_line_width 20 --ff_mdx_kim2 --highlight_words False --beep_off --check_files --sentence --verbose True --vad_filter=True --vad_threshold=0.2 --vad_min_speech_duration_ms=150 --vad_min_silence_duration_ms=200 --vad_max_speech_duration_s 5 --vad_speech_pad_ms=199 --vad_dump

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

        rem NOTE: We also have --batch_recursive - {automatically sets --output_dir}


        if not exist %TXT_FILE% .or. %SKIP_TEXTFILE_PROMPTING eq 1 (goto :No_Text)
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
                        rem OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE[%TXT_FILE]" | awk "!seen[$0]++" ]]
                        set OUR_LYRICS=%@REPLACE[%QUOTE%,',%@EXECSTR[type "%@UNQUOTE[%TXT_FILE]" |:u8 unique-lines.pl -1 -L]]

                        set WHISPER_PROMPT=--initial_prompt "%OUR_LYRICS%"
                        rem @echo %ANSI_COLOR_DEBUG%Whisper_prompt is:%newline%%tab%%tab%%faint_on%%WHISPER_PROMPT%%faint_off%%ANSI_COLOR_NORMAL%
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

REM Backup any existing SRT file, and ask if we are sure we want to generate AI right now:
        :backup any existing one
        if exist "%SRT_FILE%" (ren /q "%SRT_FILE%" "%@NAME[%SRT_FILE%].srt.%_datetime.bak")
        
        :actually_make_the_lrc
        @echos %STAR% %ANSI_COLOR_WARNING_SOFT%%blink_on%About to: %blink_off%
        @echo  %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%"%ansi_color_reset% 
        @call AskYn "Proceed with this AI generation?" yes %PROMPT_CONSIDERATION_TIME%
        iff "%answer%" eq "N" then
                @call warning "Aborting because you changed your mind..."
                sleep 1
                goto :END
        endiff


REM Concurrency Consideration: Check if the encoder is already running in the process list. Don't run more than 1 at once.
        rem slower call isRunning %TRANSCRIBER_PRNAME% silent
        rem slower if "%isRunning" != "1" (goto :no_concurrency_issues)
        rem faster:
        
        echo %ANSI_COLOR_DEBUG%- DEBUG: iff @PID[TRANSCRIBER_PDNAME=%TRANSCRIBER_PDNAME%] %@PID[%TRANSCRIBER_PDNAME%] ne 0 then%ANSI_COLOR_NORMAL%
        iff "%@PID[%TRANSCRIBER_PDNAME%]" != "0" then
                @echo %ansi_color_warning_soft%%star% %italics_on%%TRANSCRIBER_PDNAME%%italics_off is already running%ansi_color_normal%
                @echos %ANSI_COLOR_WARNING_SOFT%%STAR% Waiting for completion of %italics_on%another%italics_on% instance %italics_on%%TRANSCRIBER_PDNAME%%italics_off% to finish before starting this one...%ANSI_COLOR_NORMAL%
        else 
                goto :no_concurrency_issues
        endiff

        :Check_If_Transcriber_Is_Running_Again
                @echos %@randfg_soft[].
                rem Wait a random number of seconds to lower the odds of multiple waiting processes seeing an opening and all starting at the same time]:
                sleep %@random[7,29] 
                rem slow: call isRunning %TRANSCRIBER_PRNAME% silent
                echo 🐐%ANSI_COLOR_DEBUG%- DEBUG: if "@PID[TRANSCRIBER_PDNAME]" (which is "@PID[%transcriber_pdname]" which is "%@PID[%TRANSCRIBER_PDNAME]") ne 0 (goto :Check_If_Transcriber_Is_Running_Again)%ANSI_COLOR_NORMAL%
                echo 🐐if "@PID[%TRANSCRIBER_PDNAME%]" ne "0" (goto :Check_If_Transcriber_Is_Running_Again)
                if "%@PID[%TRANSCRIBER_PDNAME%]" ne "0" (goto :Check_If_Transcriber_Is_Running_Again)
                @echo %ansi_color_green%...%ansi_color_bright_green%Done%blink_on%!%blink_off%%ansi_reset%
        :no_concurrency_issues
        
REM actually generate the SRT file [used to be LRC but we have now coded specifically to SRT] —— start AI:
        @echo.
        @call bigecho %ANSI_COLOR_BRIGHT_RED%%EMOJI_FIREWORKS% AI running! %EMOJI_FIREWORKS%%ansi_color_normal%
        set LAST_WHISPER_COMMAND=%TRANSCRIBER_TO_USE% %CLI_OPS% "%INPUT_FILE%"    
                                 %TRANSCRIBER_TO_USE% %CLI_OPS% "%INPUT_FILE%"        |:u8  copy-move-post whisper 
        
        if %LOG_PROMPTS_USED% eq 1 (@echo %_DATETIME: %TRANSCRIBER_TO_USE% %CLI_OPS% %3$ "%INPUT_FILE%" >>"%@NAME[%INPUT_FILE].log")
        call errorlevel "some sort of problem with the AI generation occurred in %0 line ~336ish {'actually generate the srt file'}"

REM delete zero-byte LRC files that can be created
        call delete-zero-byte-files *.lrc silent
        call delete-zero-byte-files *.srt silent

REM did we create the LRC file?
        call validate-environment-variable EXPECTED_OUTPUT_FILE "expected output file of '%italics%%EXPECTED_OUTPUT_FILE%%italics_off%' does not exist"
        if exist "%@UNQUOTE[%EXPECTED_OUTPUT_FILE%]" (@echo %EXPECTED_OUTPUT_FILE%%::::%_DATETIME%::::%TRANSCRIBER_TO_USE% >>"__ contains AI-generated SRT files __")

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


:Cleanup

iff not exist "%SRT_FILE%" then
        @call warning "Unfortunately, we could create the karaoke file %emphasis%%SRT_FILE%%deemphasis%"
        title %emoji_warning% Karaoke not generated! %emoji_warning% 
else
        rem Cleanup:
                rem MiniLyrics will pick up a TXT file in the %lyrics% repo *instead* of a SRT file in the local folder
                rem   for sure: in the case of %lyrics%\letter\<same name as audio file>.txt  ——— MAYBE_LYRICS_2
                rem      maybe: in the case of %lyrics%\letter\artist - title.txt             ——— MAYBE_LYRICS_1
                rem So we must delete at least the first one, if it exists.  We use our get-lyrics script in SetVarsOnly mode:
                call get-lyrics-via-multiple-sources "%SONGFILE%" SetVarsOnly
                rem ...which sets MAYBE_LYRICS_1 and MAYBE_LYRICS_2
                @call debug "Checking if exists: '%underline_on%%MAYBE_LYRICS_2%%underline_off%' for deprecation"
                if exist "%MAYBE_LYRICS_2%" (call deprecate "%MAYBE_LYRICS_2%")

        rem Success message:
                @call divider
                @call success "Karaoke created at: %blink_on%%italics_on%%emphasis%%SRT_FILE%%deemphasis%%ANSI_RESET%"
                title %check% Karaoke generated successfully! %check% 

        rem A chance to edit:
                @call divider
                @call bigecho %ANSI_COLOR_BRIGHT_GREEN%%check%  %underline_on%SRT file contents%underline_off%:
                @echos %ANSI_COLOR_BRIGHT_GREEN%
                rem fast_cat fixes ansi rendering errors ins ome situations
                rem (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line "%faint_on%%ansi_color_red%SRT:%faint_off%%ansi_color_bright_Green%        "     |:u8 fast_cat
                rem (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line.py  "SRT:        %CHECK%" |:u8 fast_cat
                    (grep -i [a-z] "%SRT_FILE%") |:u8 insert-before-each-line.py  "%check%%ansi_color_green% SRT: %@cool[-------->] %ANSI_COLOR_bright_yellow%
                    (grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%SRT_FILE%")  |:u8 insert-before-each-line.py  "%check%%ansi_color_green% SRT: %@cool[-------->] %ANSI_COLOR_bright_yellow%
                @call divider
                @call askyn "Edit SRT file [in case there were mistakes above]" no %EDIT_KRAOKE_AFTER_CREATION_WAIT_TIME%
                iff "%ANSWER" == "Y" then
                        @echo %ANSI_COLOR_DEBUG%%EDITOR% "%SRT_FILE%" [and maybe "%TXT_FILE%"] %ANSI_RESET%
                        iff not exist "%TXT_FILE%" then
                                %EDITOR% "%SRT_FILE%" 
                        else
                                %EDITOR% "%TXT_FILE%" "%SRT_FILE%" 
                        endiff
                endiff
endiff

:END
:Cleanup
@echos %ANSI_COLOR_BLUE%%FAINT_ON%
timer /5 off
set MAKING_KARAOKE=0
unset /q OKAY_THAT_WE_HAVE_SRT_ALREADY
@echos %ANSI_RESET%%CURSOR_RESET%
if exist *collected_chunks*.wav (*del /q *collected_chunks*.wav)
if exist     *vad_original*.srt (*del /q     *vad_original*.srt)

:The_Very_END

