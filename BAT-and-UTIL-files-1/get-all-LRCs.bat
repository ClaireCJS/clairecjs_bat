@Echo OFF

rem Validate environment:
        if not defined filemask_audio call validate-environment-variable filemask_audio
        iff "1" != "%validated_getalllrcs%" then
                call validate-in-path get-lrc.bat
                set validated_getalllrcs=1
        endiff


rem Run Get-LRC on all audio files:
        for %getalllrcstmpfile in (%FILEMASK_AUDIO%) do call get-lrc getalllrcstmpfile

