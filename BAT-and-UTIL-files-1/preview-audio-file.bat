@loadBTM on
@Echo OFF

rem CONFIG:
        rem ⓿ Whether to pause after running our previewer:
                set PAUSE_AFTER_RUNNING_PLAYER=0


        rem ❶ The default player we use to preview audio files:
                set DEFAULT_PAF_PLAYER=call mpc32 
                set DEFAULT_PAF_PLAYER=call vlc
                set DEFAULT_PAF_PLAYER=vlc.exe --volume 200


        rem ❷ Whether WinAmp integration is active or not:
        rem     You can pre-set PAF_WINAMP_INTEGRATION=1 or 0 to control WinAmp integration prior to invocation
        rem             ...which is whether WinAmp will be paused/unpaused before/after previewing
        rem     Or you can let it use the defualt value here:
                set DEFAULT_PAF_WINAMP_INTEGRATION=1                            %+ rem 1=pause WinAmp while previewing, 0=don’t


        rem ❸ The “start” command that we use to launch our preview:
        rem             You can pre-set PAF_START to control how our file-previewer is launched
        rem             Typically, this would only mean setting it to “start /min” or to nothing
        rem             For VLC player, setting it to nothing makes the script pause until VLC player is closed
                set DEFAULT_PAF_START=


        rem ❹ The “show_karaoke” and “do_not_show_karaoke” flags only ever override this default behavior:
                set DEFAULT_SHOW_KARAOKE=1                                      %+ rem 1=show any existing LRC/SRT karaoke sidecars prior to preview


                                           

rem USAGE:
        iff "%1" == "" then
                echo.
                echo %ansi_color_advice%* USAGE: optional:   set     PAF_WINAMP_INTEGRATION=%DEFAULT_PAF_WINAMP_INTEGRATION%               [defines whether we pause WinAmp: 1=yes,2=no]   [default value=“%DEFAULT_PAF_WINAMP_INTEGRATION%”]%ansi_color_normal%
                echo %ansi_color_advice%* USAGE: optional:   set PAUSE_AFTER_RUNNING_PLAYER=1               %zzzzzzzzzzzzzzzzzzzzzzzzzzzzz%[pauses for any key to be pressed after we play, 1=yes,2=no]
                echo %ansi_color_advice%* USAGE: optional:   set                  PAF_START=start /min      %zzzzzzzzzzzzzzzzzzzzzzzzzzzzz%[defines how we start our previewer]            [default value=“%DEFAULT_PAF_START%”]%ansi_color_normal%
                echo %ansi_color_advice%* USAGE: optional:   set                 PAF_PLAYER={command}       %zzzzzzzzzzzzzzzzzzzzzzzzzzzzz%[to set command to use as player]               [default value=“%DEFAULT_PAF_PLAYER%”]
                echo %ansi_color_advice%* USAGE: optional:   set               PAF_LRC_FILE=whatever.lrc    %zzzzzzzzzzzzzzzzzzzzzzzzzzzzz%[“show_karaoke” parameter uses this LRC instead of searching for a sidecar LRC]
                echo %ansi_color_advice%* USAGE: optional:   set               PAF_SRT_FILE=whatever.srt    %zzzzzzzzzzzzzzzzzzzzzzzzzzzzz%[“show_karaoke” parameter uses this SRT instead of searching for a sidecar SRT]

                echo.
                echo %ansi_color_advice%* USAGE: call preview-audio-file {filename} {parameters}
                echo %ansi_color_advice%* USAGE:        EX: call preview-audio-file whatever.mp3
                echo %ansi_color_advice%* USAGE:            ⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰  Default/Normal invocation
                echo.
                echo %ansi_color_advice%* USAGE: call preview-audio-file {filename} {“show_karaoke”} [default behavior, use “do_not_show_karaoke” to disable]
                echo %ansi_color_advice%* USAGE:        EX: call preview-audio-file whatever.mp3 show_karaoke
                echo %ansi_color_advice%* USAGE:                                                 ⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰⟰ “show_karaoke” = show sidecar SRT/LRC file [if they exist]

                goto /i END
        endiff

rem Validate environment:
        iff "1" != "%validated_previewaudiofile%" then
                call validate-environment-variable emojis_have_been_set ansi_colors_have_been_set
                call validate-in-path vlc print-with-columns.bat print_with_columns.py winamp-pause error.bat print-message.bat divider subtle.bat
                set  validated_previewaudiofile=1
        endiff


rem Capture parameters:
        rem Process  environment variable parameters:
                rem ❶ If settings are not ‘passed’ via environment variable, use the defaults we define in our ‘config’ section above:
                        if not defined PAF_START              set  PAF_START=%DEFAULT_PAF_START%
                        if not defined PAF_WINAMP_INTEGRATION set  PAF_WINAMP_INTEGRATION=%PAF_WINAMP_INTEGRATION%
                        if not defined PAF_PLAYER             set  PAF_PLAYER=%DEFAULT_PAF_PLAYER%
                        if not defined PAF_LRC_FILE           echo Don’t worry about it, PAF_LRC_FILE is dealt with below 😊 >nul
                        if not defined PAF_SRT_FILE           echo Don’t worry about it, PAF_SRT_FILE is dealt with below 😊 >nul

                rem ❷ Override settings if we inherit any other WinAmp integration flags from other systems:
                        if "1" == "%WINAMP_INTEGRATION_GETLYRICS%" set PAF_WINAMP_INTEGRATION=1 %+ rem WINAMP_INTEGRATION_GETLYRICS is used by our AI-music-transcription system’s   lyric  component
                        if "1" == "%WINAMP_INTEGRATION_GENERAL%"   set PAF_WINAMP_INTEGRATION=1 %+ rem WINAMP_INTEGRATION_GENERAL   is used by our AI-music-transcription system’s subtitle component

        rem Capture filename parameter:
                unset /q audio_file_to_preview
                set param_1=%@UNQUOTE["%1"]
                shift
                iff exist "%param_1%" then
                        call validate-is-extension "%param_1%" %FILEMASK_AUDIO%                                        
                        set audio_file_to_preview=%@UNQUOTE["%param_1%"]
                else
                        call validate-environment-variable param_1 "1ˢᵗ parameter to preview-audio-file must be a file that actually exists"
                endiff
        rem Capture “show_karaoke” or any additional parameters:
                set SHOW_KARAOKE=%DEFAULT_SHOW_KARAOKE%
                iff "%1" != "" then
                        iff "%1" == "show_karaoke" then
                                set SHOW_KARAOKE=1
                                shift
                        elseiff "%1" == "do_not_show_karaoke" .or. "%1" == "dont_show_karaoke" then
                                set SHOW_KARAOKE=0
                                shift
                        else
                                call error "Unknown 2ⁿᵈ parameter of “%1” given to preview-audio-file"
                                goto /i END
                        endiff
                endiff



rem Actions to take BEFORE preview (pausing music):
        iff "1" == "%PAF_WINAMP_INTEGRATION%" then
                echos %italics_off%%emoji_pause_button%%emoji_llama%   Pausing ⚡WinAmp⚡%ANSI_EOL%%@ANSI_MOVE_TO_COL[1]
                ((call winamp-pause quick)>&>nul) >&>nul
        endiff

rem Are PAF_LRC_FILE / PAF_SRT_FILE even defined?
        set potential_preview_lrc=%@NAME[%@UNQUOTE["%audio_file_to_preview%"]].lrc
        set potential_preview_srt=%@NAME[%@UNQUOTE["%audio_file_to_preview%"]].srt
        iff not defined PAF_LRC_FILE if exist "%potential_preview_lrc%" set PAF_LRC_FILE=%potential_preview_lrc%
        iff not defined PAF_SRT_FILE if exist "%potential_preview_srt%" set PAF_LRC_FILE=%potential_preview_srt%

rem Show raw karaoke:
        iff "1" == "%SHOW_KARAOKE%" then
                set printed_something=0
                iff exist "%PAF_LRC_FILE%" then
                        call print-with-columns -cw %_COLUMNS "%PAF_LRC_FILE%" 
                        set printed_something=1
                endiff
                iff exist "%PAF_SRT_FILE%" then
                        if "1" == "%printed_something%" call divider
                        call print-with-columns -cw %_COLUMNS "%PAF_SRT_FILE%"  
                        set printed_something=1
                endiff
                if "1" == "%printed_something%" call divider

        endiff
        

rem OLD: Announce the preview: Outer-script should be responsible for saying this, but if none exists, say it ourselves: 
        if "%_PBATCHNAME" == "" echo %ansi_color_bright_green%%emoji_play_button%Previewing file: %ansi_color_green%%italics_on%“%audio_file_to_preview%”%italics_off%%ansi_color_normal%

rem NEW: Announce the preview no matter what:
        echo %ANSI_COLOR_IMPORTANT%%EMOJI_PLAY_BUTTON% %blink_on%Playing file: %blink_on%“%ansi_color_important_less%%blink_on%%@UNQUOTE["%FILE_TO_USE%"]%ansi_color_important%%blink_on%”%blink_off% %EMOJI_PLAY_BUTTON%%ansi_color_normal%%ANSI_EOL%

rem Do the actual preview:
        set      PAF_COMMAND=%PAF_START% %PAF_PLAYER% %param_1% %1$
        set LAST_PAF_COMMAND=%PAF_COMMAND%
        call subtle "Playback command is: %faint_on%%PAF_COMMAND%%ansi_color_normal%%faint_off%"
        echos %ANSI_MOVE_UP_1%%ANSI_MOVE_UP_1%
        %PAF_COMMAND%

rem NEW: Announce that we’ve played it, overwriting the announcement that we were *playing* it:
        echo %ANSI_COLOR_REMOVAL%%EMOJI_STOP_BUTTON% Played file: “%ansi_color_bright_pink%%@UNQUOTE["%FILE_TO_USE%"]%ansi_color_removal%” %EMOJI_STOP_BUTTON%%ansi_color_normal%

rem If we have an environment option to pause, do so:
        if "1" == "%PAUSE_AFTER_RUNNING_PLAYER%" pause

rem Actions to take AFTER preview (unpausing music):
        iff "1" == "%PAF_WINAMP_INTEGRATION%" then
                echos %italics_off%%emoji_pause_button%%emoji_llama% Unpausing ⚡WinAmp⚡%ANSI_EOL%%@ANSI_MOVE_TO_COL[1]
                ((call winamp-unpause quick)>&>nul) >&>nul
        endiff

rem Cleanup:
        :END
        unset /q PAF_COMMAND PAF_START PAF_WINAMP_INTEGRATION PAF_PLAYER PAF_LRC_FILE PAF_SRT_FILE    %+ rem Because this can be an env-var parameter, unset it so internally-set values don’t become env-var-parameters of future invocations



