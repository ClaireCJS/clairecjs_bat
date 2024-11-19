@on break cancel
@Echo OFF

for /o:a %%tmpmp3 in (*.mp3) (
    call display-mp3-length "%tmpmp3"
    call errorlevel
)
