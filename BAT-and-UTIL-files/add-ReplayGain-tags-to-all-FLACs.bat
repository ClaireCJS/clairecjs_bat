@echo off 

call randcolor
if not exist *.flac (%COLOR_IMPORTANT_LESS% %+ echo 🚫 No flacs exist here. %+ goto :END)
if     exist *.flac (goto :FlacExists_YES)
                     goto :FlacExists_NO



:FlacExists_YES
%COLOR_RUN% %+ echo %EMOJI_INPUT_NUMBERS% Adding ReplayGain tags to flac files...
for %%flac in (*.flac) (
    %COLOR_LESS_IMPORTANT% 
    echo     %EMOJI_CHECK_BOX_WITH_CHECK% %flac%
    metaflac --add-replay-gain "%flac"
    call errorlevel "something went wrong with adding replaygain tags to %flac in %0"
)






:FlacExists_NO
:END
color bright red on black


