@LoadBTM on
@Echo off 
@on break cancel



rem Validate environment (once):
        iff "1" != "%validated_addreplaygaintagstoallflags%" then
                call validate-in-path randcolor metaflac.exe errorlevel
                call validate-environment-variable ansi_colors_have_been_set
                set  validated_addreplaygaintagstoallflags=1
        endiff



rem Validate folder:
        if not exist *.flac (%COLOR_IMPORTANT_LESS% %+ echo 🚫 No flacs exist here. %+ goto :END)
        if     exist *.flac (goto :FlacExists_YES)
                             goto :FlacExists_NO




rem Add ReplayGain tags to all FLAC files:
        :FlacExists_YES
        %COLOR_RUN% %+ echo %EMOJI_INPUT_NUMBERS% Adding ReplayGain tags to flac files...
        for %%flac in (*.flac) (
                call randcolor
                %COLOR_LESS_IMPORTANT% 
                echo     %EMOJI_CHECK_BOX_WITH_CHECK% %flac%
                metaflac --add-replay-gain "%flac"
                call errorlevel "something went wrong with adding replaygain tags to %flac in %0"
        )


rem End out:
        :FlacExists_NO
        :END
        color bright red on black


