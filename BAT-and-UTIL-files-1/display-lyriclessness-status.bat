@loadbtm on
@Echo OFF
@on break cancel


rem Validate environment (once):
        iff "%1" == "" then
                echo.
                echo USAGE: display-lyriclessness-status filename.mp3
                echo USAGE: display-lyriclessness-status *.mp3
                echo USAGE: display-lyriclessness-status %%FILEMASK_AUDIO%% (if that env var is defined. If it isn’t, running this will define it)
                goto :END
        endiff


rem This should already be defined, but just in case it isn’t:
        if not defined FILEMASK_AUDIO set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.dtshd


rem If it’s an individual file, use our script to display individual file statuses:
        iff "1" != "%@RegEx[[\*\?],%1]" then
                @call display-lyriclessness-status-for-file.bat %*

rem And if it’s a wildcard, go through each file in the fildcard, and if 
rem it’s an audio file, use our script to display individual file statues:
        else
                set MASKS=%1
                for %%tmpfile in (%MASKS%) do (
                        set BASENAME=%@UNQUOTE[%@name["%tmpFile%"]]
                        set EXT=%@EXT[%tmpfile%]
                        iff "%ext%" != "" then
                                if "%@Regex[%ext%,"%FILEMASK_AUDIO%"]" == "1" (call display-lyriclessness-status-for-file "%@UNQUOTE[%tmpfile]")
                        endiff
                )
        endiff

:END

