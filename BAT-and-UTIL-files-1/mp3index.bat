@loadBTM on
@Echo off
@on break cancel


rem  ---------------------- MP3INDEX.BAT ----------------------
rem  ---------------------- MP3INDEX.BAT ----------------------
rem  ---------------------- MP3INDEX.BAT ----------------------

:DESCRIPTION: This is more or less a glorified "dir /b *.mp3", execpt it works for all audio file types
:USAGE:       call mp3index                 - create these.m3u and all.m3u of all audio files
:USAGE:       call mp3index /s              - create               all.m3u of all audio files
:USAGE:       call mp3index vocal           - create these.m3u and all.m3u of only file formats that can have vocals
:USAGE:       call mp3index vocals          - create these.m3u and all.m3u of only file formats that can have vocals
:USAGE:       call mp3index vocalonly       - create these.m3u and all.m3u of only file formats that can have vocals
:USAGE:       call mp3index vocalsonly      - create these.m3u and all.m3u of only file formats that can have vocals
:USAGE:       call mp3index vocalonly /s    - create               all.m3u of only file formats that can have vocals
:USAGE:       call mp3index vocalsonly /s   - create               all.m3u of only file formats that can have vocals




iff "%FILEMASK_AUDIO_VALIDATED%" ne "2" then
        if not defined FILEMASK_AUDIO            call validate-environment-variable FILEMASK_AUDIO         skip_validation_existence
        if not defined FILEMASK_VOCAL            call validate-environment-variable FILEMASK_VOCAL         skip_validation_existence
        if not defined ANSI_COLORS_HAVE_BEEN_SET call validate-environment-variable ANSI_COLORS_HAVE_BEEN_SET
        set FILEMASK_AUDIO_VALIDATED=2
endiff



rem Determine operatoinal modes:
        unset /q vocal_mode recursive_mp3index_mode

        :slurp

        rem Vocal mode?                                                                                                      
                iff ("%1" == "vocalsonly" .or. "%1" == "vocalonly" .or. "%1" == "vocal" .or. "%2" == "vocals") then 
                        set vocal_mode=1
                        shift
                        goto /i :slurp
                else
                        if "1" != "%vocal_mode%" set vocal_mode=0
                endiff

        rem Recursive mode?
                iff ("%1" == "/s" .or. "%1" == "-s") then 
                        set recursive_mp3index_mode=1
                        shift
                        goto /i :slurp
                else
                        if "1" != "%recursive_mp3index_mode%" set recursive_mp3index_mode=0
                endiff



rem Determine filemask (vocals only mode vs all audio mode):
        set                          FILEMASK_TO_USE=%FILEMASK_AUDIO%
        if "1" == "%vocal_mode%" set FILEMASK_TO_USE=%FILEMASK_VOCAL%






rem THIS SHOULD WORK IN A PERFECT WORLD:
    iff "1" != "%recursive_mp3index_mode%" then
        rem We did NOT chose /s
        if exist these.m3u (*del /q these.m3u >nul)
        rem echo [DEBUG][GOAT] iff exist %FILEMASK_TO_USE% .or. %@FILES[/s/h,%FILEMASK_TO_USE] gt 0 then
        unset /q TMP_FILE_COUNT
        set TMP_FILE_COUNT=%@FILES[/s/h,%FILEMASK_TO_USE]
        iff exist %FILEMASK_TO_USE% .or. %TMP_FILE_COUNT% gt 0 then
                iff exist %FILEMASK_TO_USE% then
                        (*dir /b /a:-d  %1$ %FILEMASK_TO_USE%) >:u8these.m3u
                else
                        if exist these.m3u (*del /q these.m3u >nul)
                endiff
                *dir /b /a:-d /s %* %FILEMASK_TO_USE% >:u8all.m3u
        else
                call warning_soft "No audio files in: %faint_on%%_CWD%%faint_off% or subfolders"
        endiff
    elseiff "1" == "%recursive_mp3index_mode%" then
        rem We chose /s
        if exist all.m3u (*del /q   all.m3u >nul)
        iff %@FILES[/s/h,%FILEMASK_TO_USE] gt 0 then
                *dir /b /a:-d /s %1$ %FILEMASK_TO_USE%  >:u8all.m3u
                call advice "call mp3index without any arguments to create all.m3u and these.m3u automatically"
        else
                call warning_soft "No audio files in: %faint_on%%_CWD%%faint_off%, or any of its subfolders"
                if exist all.m3u (*del /q   all.m3u >nul)
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