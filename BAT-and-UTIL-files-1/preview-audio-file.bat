@Echo OFF
@loadBTM on

rem CONFIG:
	rem You can set PAF_WINAMP_INTEGRATION=1 or 0 to control WinAmp integration, or you can let it inhere this value from other flags [preferred]


rem USAGE:
        rem             call preview-audio-file whatever.mp3
        rem             call preview-audio-file whatever.mp3 show_karaoke


rem Validate environment:
        iff "1" != "%validated_previewaudiofile%" then
                call validate-environment-variable emojis_have_been_set ansi_colors_have_been_set
                call validate-in-path vlc print-with-columns.bat print_with_columns.py
                set  validated_previewaudiofile=1
        endiff

rem Inherit any winamp integration flags, just in case the flag in this file is turned off and really should not be:
        if  "1" == "%WINAMP_INTEGRATION_GETLYRICS%" set PAF_WINAMP_INTEGRATION=1
        if  "1" == "%WINAMP_INTEGRATION_GENERAL%"   set PAF_WINAMP_INTEGRATION=1

rem Actions to take BEFORE preview (pausing music):
        iff "1" == "%PAF_WINAMP_INTEGRATION%" then
                echo %italics_off%%emoji_pause_button%%emoji_llama% Pausing ⚡WinAmp⚡
                ((call winamp-pause   quick)>&>nul) >&>nul
        endiff

rem Show raw karaoke:
        iff "%2" == "show_karaoke" then
                if exist "%LRC_FILE%" call print_with_columns "%LRC_FILE%"
                if exist "%SRT_FILE%" call print_with_columns "%SRT_FILE%"
        endiff
        

rem Do the actual preview:
        rem Outer-script should be responsible for this: echo %emoji_play_button% Previewing file: %italics_on%%*%italics_off%
        vlc.exe --volume 200 %*


rem Actions to take AFTER preview (unpausing music):
        iff "1" == "%PAF_WINAMP_INTEGRATION%" then
                echo %italics_off%%emoji_pause_button%%emoji_llama% Unpausing ⚡WinAmp⚡
                ((call winamp-unpause quick)>&>nul) >&>nul
        endiff

