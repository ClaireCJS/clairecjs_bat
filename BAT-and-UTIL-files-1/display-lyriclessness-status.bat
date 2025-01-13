@loadbtm on
@Echo OFF
@on break cancel


if not defined FILEMASK_AUDIO set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.dtshd


iff "1" != "%@RegEx[[\*\?],%1]" then
        @call display-lyriclessness-status-for-file.bat %*
else
        set MASKS=%DEFAULT_MASKS%
        for %%tmpfile in (%MASKS%) do (
                set BASENAME=%@UNQUOTE[%@name["%tmpFile%"]]
                set EXT=%@EXT[%tmpfile%]
                iff "%ext%" != "" then
                        if "%@Regex[%ext%,"%FILEMASK_AUDIO%"]" == "1" (call display-lyriclessness-status-for-file "%@UNQUOTE[%tmpfile]")
                endiff
        )
endiff

