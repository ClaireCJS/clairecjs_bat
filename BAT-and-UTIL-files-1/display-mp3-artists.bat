@on break cancel
@Echo off

for %song in (%filemask_audio) do (echos %ANSI_COLOR_MAGENTA%%song%: %+ (call display-mp3-tags "%song%"|:u8gr artist))