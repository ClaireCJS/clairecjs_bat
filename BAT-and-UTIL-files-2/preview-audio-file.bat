@Echo OFF
@loadBTM on

rem CONFIG:
	set PAF_WINAMP_INTEGRATION=1


rem Validate environment:
        iff "1" != "%validated_previewaudiofile%" then
                call validate-in-path vlc.exe
                set validated_previewaudiofile=1
        endiff


rem Actions to take BEFORE preview (pausing music):
        (if "1" == "%PAF_WINAMP_INTEGRATION%" call winamp-pause quick) >&>nul


rem Do the actual preview:
        vlc.exe --volume 200 %*


rem Actions to take AFTER preview (unpausing music):
        (if "1" == "%PAF_WINAMP_INTEGRATION%" (call winamp-unpause quick)>&>nul) >&>nul

