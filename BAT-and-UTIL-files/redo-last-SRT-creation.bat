@Echo OFF


call validate-in-path              create-srt
call validate-environment-variable AUDIO_FILE

create-srt "%AUDIO_FILE%"

