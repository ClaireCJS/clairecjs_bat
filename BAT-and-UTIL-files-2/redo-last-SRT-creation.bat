@loadbtm on
@Echo OFF
@on break cancel


call validate-in-path              create-srt
call validate-environment-variable AUDIO_FILE

create-srt "%AUDIO_FILE%" last

