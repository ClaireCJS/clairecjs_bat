@Echo Off
 on break cancel





REM environment validation
        REm can't validate if filename exits because it could be anyhere in the command tail, but don't worry, whisper will error out if it doesn't exist, and errorlevel.bat will catch that error if thrown in a batch situation
        call validate-in-path whisper-faster.exe askyn.bat warning.bat errorlevel.bat
        


REM parameter validation
        set                                OUR_INPUT_FILE=%1
        call validate-environment-variable OUR_INPUT_FILE





REM startup
        %COLOR_ADVICE%      %+ echo --`>` whisper-faster.bat
        %COLOR_UNIMPORTANT% %+ timer /7 on




REM CLI option setup
                          set DRY_RUN_TEXT=
        if %DRY_RUN eq 1 (set DRY_RUN_TEXT=@echo %ITALICS%%ANSI_RED%)
        set CLI_OPT_LANGUAGE=--language en 
        if  %NO_DEFAULT_LANGUAGE eq 1 (set CLI_OPT_LANGUAGE=)












REM run whisperx [which is a layer built on top of whisper that is more subtitle-specific]
rem but at various points i have used this whisper-faster.exe who's origins i don't remember? 
        : Key Differences
        : Word-Level Timestamps:
        : 
        : Whisper: Provides overall transcription with approximate timing for segments.
        : WhisperX: Provides detailed word-level timestamps for more precise synchronization.
        : Purpose and Use Cases:
        : 
        : Whisper: General-purpose transcription and translation.
        : WhisperX: Enhanced transcription with precise timing, useful for subtitle generation, detailed speech analysis, and other applications needing exact word timings.
        : Development and Maintenance:
        : 
        : Whisper: Officially developed and maintained by OpenAI.
        : WhisperX: Community-driven, leveraging Whisper’s models with additional processing for specific use cases.

        REM want these options but they don't apply if vad_filter False: --vad_min_silence_duration_ms 2000 --vad_speech_pad_ms 400 --vad_max_speech_duration_s 10 
        REM --vad_filter False  

        rem :POSSIBLE ADVICE: --beam_size 5 might help?
        rem    ::::: --highlight_words True - adds stuff to srt files, maybe try it


        set OUR_WHISPER=cmd.exe /c whisperx.exe
        set OUR_WHISPER=cmd.exe /c whisper-faster.exe
        %COLOR_RUN%
        @echo on
        %DRY_RUN_TEXT% %OUR_WHISPER% --verbose True %CLI_OPT_LANGUAGE% --threads 12 --device cuda --model large-v2 --output_dir "%_CWD" --output_format lrc     --beam_size 5  %OUR_INPUT_FILE%
        @call errorlevel "failure during whisper-faster.exe"
        @echo off








REM validate files were created properly
        set FILES_CREATED=1
        REM todo: this part. If the files are not created, set FILES_CREATED=0
        if (%FILES_CREATED eq 0 .or. %REDO_BECAUSE_OF_ERRORLEVEL eq 1) .and. %RECURSION_LEVEL ne 1 (
            call warning "Files were not properly created!"
            call askyn "Attempt to regenerate without english as the default language?" yes 300
            if %DOIT eq 1 (
                set RECURSION_LEVEL=1
                    set NO_DEFAULT_LANGUAGE=1
                        call %0 %*
                    set NO_DEFAULT_LANGUAGE=0
                set RECURSION_LEVEL=0
            )
        )


REM cleanup
        :END
        %COLOR_SUCCESS% 
        timer /7 off














REM extra documentation
    REM VAD stuff
            REM --vad_filter False  was *CRITICAL* to getting good results
            REM --vad_threshold               VAD_THRESHOLD               Probabilities above this value are considered as speech. (default: 0.45)
            REM --vad_max_speech_duration_s   VAD_MAX_SPEECH_DURATION_S   Maximum duration of speech chunks in seconds. Longer will be split at the timestamp of the last silence. (default: None)
            REM                                         maybe like 10s?
            REM --vad_min_silence_duration_ms VAD_MIN_SILENCE_DURATION_MS In the end of each speech chunk time to wait before separating it. (default: 3000)
            REM                                         maybe this should be shortened a little bit for music?  To like --vad_min_silence_duration_ms 2000?
            REM --vad_speech_pad_ms           VAD_SPEECH_PAD_MS           Final speech chunks are padded by speech_pad_ms each side. (default: 900)
            REM                                         maybe this should be shortened a little bit for music?  To like --vad_speech_pad_ms 400?
REM All downloads are in Releases: https://github.com/Purfview/whisper-standalone-win/releases
