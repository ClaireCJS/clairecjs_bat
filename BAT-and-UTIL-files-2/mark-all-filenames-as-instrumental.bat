@loadbtm on
@Echo OFF
@on break cancel

rem Config:
        set PLAYER_COMMAND=call preview-audio-file

rem Validate environment (once):
        iff "1" != "validated_markallfilenamesasinstrumental" then
                call validate-in-path preview-audio-file advice get-lyrics-for-file.btm
                set  validated_markallfilenamesasinstrumental=1
        endiff

rem Advice:
        call advice "Run with “ask” parameter to prompt for each file!"


rem Call sub-part of lyric-AI-transcription system where this is coded:
        gosub "%BAT%\get-lyrics-for-file.btm" actually_rename_every_file_as_an_instrumental_or_whatever %*


rem Success stuffs (if any):
        rem dir


