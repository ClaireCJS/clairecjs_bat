@loadbtm on
@Echo OFF
@on break cancel

rem Config:
        set PLAYER_COMMAND=call preview-audio-file

rem Validate environment (once):
        iff "1" != "validated_unmarkallfilenamesadstagsasinstrumental" then
                call validate-in-path preview-audio-file advice get-lyrics-for-file.btm
                set  validated_unmarkallfilenamesadstagsasinstrumental=1
        endiff

rem Advice:
        rem call advice "Run with “ask” parameter to prompt for each file!"


rem Call sub-part of lyric-AI-transcription system where this is coded:
        gosub "%BAT%\get-lyrics-for-file.btm" unmark_every_file_as_an_instrumental_ADS_tag_only %*


rem Success stuffs (if any):
        rem dir


