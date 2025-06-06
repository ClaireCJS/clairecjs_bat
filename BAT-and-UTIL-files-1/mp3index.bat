@Echo off
rem  ---------------------- MP3INDEX.BAT ----------------------
rem  ---------------------- MP3INDEX.BAT ----------------------
rem  ---------------------- MP3INDEX.BAT ----------------------
@on break cancel

:DESCRIPTION: This is more or less a glorified "dir /b *.mp3", execpt it works for all audio file types
:USAGE:       call mp3index
:USAGE:       call mp3index /s

iff %FILEMASK_AUDIO_VALIDATED ne 1 then
        call validate-environment-variable FILEMASK_AUDIO         skip_validation_existence
        call validate-environment-variable ANSI_COLORS_HAVE_BEEN_SET
        set FILEMASK_AUDIO_VALIDATED=1
endiff

rem THIS SHOULD WORK IN A PERFECT WORLD:
    iff "%1" ne "/s" then
        rem 🐈🐈🐈🐈🐈🐈 We did NOT chose /s
        iff exist %FILEMASK_AUDIO% .or. %@FILES[/s/h,%FILEMASK_AUDIO] gt 0 then
                iff exist %FILEMASK_AUDIO% then
                        rem if exist these.m3u (*del /q these.m3u >nul)
                        (*dir /b /a:-d    %* %FILEMASK_AUDIO%) >:u8these.m3u
                        rem call handles
                else
                        if exist these.m3u (*del /q these.m3u >nul)
                endiff
                *dir /b /a:-d /s %* %FILEMASK_AUDIO% >:u8all.m3u
        else
                call warning_soft "No audio files in: %faint_on%%_CWD%%faint_off% or subfolders"
                if exist all.m3u (*del /q all.m3u >nul)
        endiff
    elseiff "%1" eq "/s" then
        rem 🐈🐈🐈🐈🐈🐈 We chose /s
        iff %@FILES[/s/h,%FILEMASK_AUDIO] gt 0 then
                *dir /b /a:-d /s %* %FILEMASK_AUDIO%
                call advice "call mp3index without any arguments to create all.m3u and these.m3u automatically"
        else
                call warning_soft "No audio files in: %faint_on%%_CWD%%faint_off%, or any of its subfolders"
                rem if exist these.m3u (*del /q these.m3u >nul)
                rem if exist   all.m3u (*del /q   all.m3u >nul)
        endiff
    endiff
    goto :END


                            rem but in older versions of our command line, the maximum environment variable length was shorter, so we USED to have to split it into 4 separate ones
                            rem so it used to unfortunately look like this:
                                call validate-environment-variable FILEMASK_AUDIO_SPLIT_1 skip_validation_existence
                                call validate-environment-variable FILEMASK_AUDIO_SPLIT_2 skip_validation_existence
                                call validate-environment-variable FILEMASK_AUDIO_SPLIT_3 skip_validation_existence
                                call validate-environment-variable FILEMASK_AUDIO_SPLIT_4 skip_validation_existence
                                (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_1|:u8strip-ansi )%>&>nul
                                (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_2|:u8strip-ansi )%>&>nul
                                (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_3|:u8strip-ansi )%>&>nul
                                (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_4|:u8strip-ansi )%>&>nul


:END