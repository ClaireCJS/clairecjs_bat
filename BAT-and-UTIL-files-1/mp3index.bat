@Echo off
@on break cancel

:DESCRIPTION: This is more or less a glorified "dir /b *.mp3", execpt it works for all audio file types
:USAGE:       call mp3index
:USAGE:       call mp3index /s


iff %FILEMASK_AUDIO_VALIDATED ne 1 then
        call validate-environment-variable FILEMASK_AUDIO         skip_validation_existence
        call validate-environment-variable FILEMASK_AUDIO_SPLIT_1 skip_validation_existence
        call validate-environment-variable FILEMASK_AUDIO_SPLIT_2 skip_validation_existence
        call validate-environment-variable FILEMASK_AUDIO_SPLIT_3 skip_validation_existence
        call validate-environment-variable FILEMASK_AUDIO_SPLIT_4 skip_validation_existence
        set FILEMASK_AUDIO_VALIDATED=1
endiff


rem THIS SHOULD WORK IN A PERFECT WORLD:
    *dir /b /a:-d %* %FILEMASK_AUDIO
    goto :END


            rem but in older versions of our command line, the maximum environment variable legnth was shorter, so we USED to have to split it into 4 separate ones
            rem so it used to unfortunately look like this:
              (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_1|:u8strip-ansi )%>&>nul
              (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_2|:u8strip-ansi )%>&>nul
              (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_3|:u8strip-ansi )%>&>nul
              (dir /b   /a:-d %* %FILEMASK_AUDIO_SPLIT_4|:u8strip-ansi )%>&>nul


:END