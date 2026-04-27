@on break cancel
@Echo OFF

for /o:a %%tmpmp3 in (%FILEMASK_AUDIO%) (
    call display-audio-file-length "%tmpmp3"
    call errorlevel
)
