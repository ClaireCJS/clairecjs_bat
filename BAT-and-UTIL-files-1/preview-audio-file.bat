@Echo OFF
@loadBTM on

rem CONFIG:
	set PAF_WINAMP_INTEGRATION=1


rem USAGE:
        rem             call preview-audio-file whatever.mp3
        rem             call preview-audio-file whatever.mp3 show_karaoke


rem Validate environment:
        iff "1" != "%validated_previewaudiofile%" then
                call validate-in-path vlc.exe print-with-columns.bat print_with_columns.py
                set validated_previewaudiofile=1
        endiff


rem Actions to take BEFORE preview (pausing music):
        (if "1" == "%PAF_WINAMP_INTEGRATION%" call winamp-pause quick) >&>nul

rem Show raw karaoke:
        iff "%2" == "show_karaoke" then
                if exist "%LRC_FILE%" call print_with_columns "%LRC_FILE%"
                if exist "%SRT_FILE%" call print_with_columns "%SRT_FILE%"
        endiff
        

rem Do the actual preview:
        vlc.exe --volume 200 %*


rem Actions to take AFTER preview (unpausing music):
        (if "1" == "%PAF_WINAMP_INTEGRATION%" (call winamp-unpause quick)>&>nul) >&>nul

