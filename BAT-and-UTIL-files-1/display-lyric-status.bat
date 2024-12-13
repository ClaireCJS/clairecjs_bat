@Echo Off
@on break cancel

rem Set our lyric filemask:
        rem FILEMASK_LYRICS_TEMP=*.txt
        set FILEMASK_LYRICS_TEMP=*.txt;*.lrc;*.srt;%FILEMASK_AUDIO%

rem If we passed a parameter, we are operating on a single file:
        iff "%1" eq "/?"  .or. "%1" eq "" then
                %color_advice%
                echo %ansi_color_advice%
                echo    display-lyric-status {lyric_file.txt} - displays lyric status for 1 file
                echo                                            `^^^^^^^^^^^^^^^^^^^^^` sets LYRIC_STATUS={status value} as a return value
                echo    display-lyric-status     {*frog*.txt} - displays lyric status for files matching filecard
                echo    display-lyric-status     all          - displays lyric status for allllllll files
                echo    display-lyric-status     audio        - displays lyric status for all audio files
                echo.
                echo  NOTE: Can also be run on an audiofile to display its lyric%italics_on%lessness%italics_off% status
                %color_normal%
                echos %ansi_reset%
                goto :END
        endiff
        iff "%1" ne "" .and. "%1" ne "all" .and. "%1" ne "audio" .and. "1" ne "%@RegEx[[\*\?],%1]"  then
                rem When operating on a single file, make sure it is the correct extension prior to displaying the lyrics:
                        if "%2" ne "skip_validations" call validate-is-extension "%@UNQUOTE[%1]" %FILEMASK_LYRICS_TEMP% "Slow down, partner! The 1ˢᵗ arg must be a file that matches “%italics_on%%FILEMASK_LYRICS_TEMP%%italics_off%”"
                        call display-lyric-status-for-file %*
                        goto :END
        endiff

rem Make sure some important environment variables actually exist:
        if not defined FILEMASK_AUDIO set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        if not defined RED_X          set RED_X=%@CHAR[10060]%@CHAR[0]

rem Validate environment once per session:
        iff 1 ne %VALIDATED_DLS% then
                call validate-in-path display-lyric-status-for-file validate-environment-variable warning get-lyric-status get-lyriclessness-status
                call validate-environment-variable filemask_audio
                set  VALIDATED_DLS=1
        endiff

rem Don’t do anything if any potential lyric files do not exist
        iff not exist %FILEMASK_LYRICS_TEMP%;%FILEMASK_AUDIO% then
                echo.
                call warning "No lyric or audio files here." silent
                goto :END
        endiff                

rem Count how many files we will be displaying the status of:
        set USE_SPACER=1
        set NUM_LYRICS_FOUND=0
        rem %%tmpfile in (%FILEMASK_LYRICS_TEMP%                ) do 
        set DEFAULT_MASKS=%FILEMASK_LYRICS_TEMP%;%FILEMASK_AUDIO
        set DEFAULT_MASKS=%FILEMASK_LYRICS_TEMP%;*.srt;*.lrc;%FILEMASK_AUDIO
        set DEFAULT_MASKS=*.*

        iff "1" eq "%@RegEx[[\*\?],%1]" then
                set MASKS=%1
        else
                set MASKS=%DEFAULT_MASKS%
        endiff
        rem DEBUG: echo masks=%masks% %+ *pause
        for %%tmpfile in (%MASKS%) do (
                rem echo ...doing %tmpfile...
                rem Check if it has a sidecar audio file:                
                        set BASENAME=%@name[%tmpFile%]
                        set FOUND=0
                        for %%E in (%FILEMASK_AUDIO%) do (if exist "%BASENAME%%%~xE" (set FOUND=1))
                rem If it does, then increase our file count by 1:
                        if %FOUND% != 0 (set NUM_LYRICS_FOUND=%@EVAL[%NUM_LYRICS_FOUND + 1])       
        )

rem If we will be displaying more than 1 file, use justification so the values line up nicely:
        rem num_lyrics_found=%num_lyrics_found
        iff 1 eq %NUM_LYRICS_FOUND then
                set USE_SPACER=0
        else
                set USE_SPACER=1
        endiff
        if %NUM_LYRICS_FOUND gt 0 (echo.)

rem Go through each file, displaying it’s lyric status:
        iff "1" ne "%@RegEx[[\*\?],%1]" then
                set masks=%FILEMASK_AUDIO%;*.srt;*.lrc;*.txt
                set masks=*
                if "%1" eq "audio" (
                        set masks=%filemask_audio%
                ) else (
                        if "%1" ne "all" set masks=%1
                )                        
        endiff
        
        rem call debug "🎭 masks=%masks%" %+ pause
        for %%tmptmpfile in (%masks%) do gosub process "%tmptmpfile%"

        goto    :process_done
                :process [tmptmpfile]
                        rem DEBUG: 🐐 call divider %+ call debug "gosub :process %tmptmpfile%" silent
                        
                        rem Subroutine parameters:
                                set tmpfile=%@unquote[%tmptmpfile%]
                                set BASENAME=%@name[%tmpFile%]
                                set ext=%@ext[%tmpfile%]
                                
                        rem Skip if the file has no extension, or if the extension is not valid:
                                if ""  eq         "%@ext[%tmpfile]"                                     goto :nevermind_on_the_processing
                                if "0" eq "%@regex[%@ext[%tmpfile],%filemask_audio%;*.srt;*.lrc;*.txt]" goto :nevermind_on_the_processing
                                if "%@LEFT[21,%tmpfile%]" eq "normalization-report-"                    goto :nevermind_on_the_processing %+ rem Skip our internal normalization reports
                                if "%@LEFT[ 6,%tmpfile%]" eq "README"                                   goto :nevermind_on_the_processing %+ rem Skip README files
        
                        rem Determine statuses based on parameters:
                                set NOT_LYRICS=0          %+ if "%EXT%" ne "txt"                         (set NOT_LYRICS=1         )
                                set  IS_LYRICS=0          %+ if "%EXT%" eq "txt"                         (set  IS_LYRICS=1         )
                                set  IS_KARAOKE=0         %+ if "%EXT%" eq "srt" .or.  "%EXT%" eq "lrc"  (set  IS_KARAOKE=1        )
                                set NOT_KARAOKE=0         %+ if "%EXT%" ne "srt" .and. "%EXT%" ne "lrc"  (set NOT_KARAOKE=1        )
                                set PROBABLY_AUDIO_FILE=0 %+ if 1 eq %NOT_LYRICS .and. 1 eq %NOT_KARAOKE (set PROBABLY_AUDIO_FILE=1)

                        rem Debug info:
                                rem  echo %emoji_cat% ext=%ext% - %ansi_color_bright_yellow% tmpfile is %tmpfile% %ansi_color_yellow%... ext = %ext ... %ansi_color_orange% not_lyrics=%NOT_LYRICS% is_lyrics=%IS_LYRICS% not_karaoke=%NOT_KARAOKE is_karaoke=%IS_KARAOKE prob_audio_file=%PROBABLY_AUDIO_FILE%%ansi_reset% 
                        
                        rem Store that we’ve processed the file:
                                set "dls_processed_%tmpfile%=1" 
                        
                        rem Check if it has a sidecar lyric file:                
                                set TMP_LYRIC_OR_SONG_SIDECAR_FILE=
                                set SIDECAR_FOUND=0
                                set MASK_TO_CHECK=%FILEMASK_LYRICS_TEMP%
                                for %%E in (%MASK_TO_CHECK%) do (
                                    if exist "%BASENAME%%%~xE" (
                                        set comment=echo Found sidecar file: %BASENAME%%%~xE
                                        set TMP_LYRIC_OR_SONG_SIDECAR_FILE=%@UNQUOTE[%BASENAME%%%~xE]
                                        set SIDECAR_FOUND=1
                                    )
                                )
                                rem call debug "     is_karaoke=%is_karaoke% 🍤 tmpfile=%tmpfile% 🍟 SIDECAR_FOUND=%SIDECAR_FOUND% and is %TMP_LYRIC_OR_SONG_SIDECAR_FILE%" silent

                        rem Display the lyric status if a sidecar file was found, or another message if one was not:
                                if 1 eq %IS_KARAOKE (
                                                rem echos is_karaoke: ``
                                                call display-lyric-status-for-file "%tmpfile%" skip_validations
                                ) else (
                                        rem if 1 eq %SIDECAR_FOUND%  (
                                        rem         call display-lyric-status-for-file "%TMP_LYRIC_OR_SONG_SIDECAR_FILE%" skip_validations
                                        rem ) else (                                
                                        rem         rem The old way, before lyriclessness was approveable: if 1 eq %USE_SPACER% ( echo %@CHAR[55357]%@CHAR[56590] %@CHAR[27][38;2;98;108;22m%red_x% No corresponding lyric file for: %@CHAR[27][38;2;68;78;15m%italics_on%%@FULL[%tmpFile%]%italics_off%%faint_off% ) else ( echo %@CHAR[55357]%@CHAR[56590] %@CHAR[27][38;2;98;108;22mNo corresponding lyric for: %@CHAR[27][38;2;68;78;15m%italics_on%%@FULL[%tmpFile%]%italics_off%%faint_off% )
                                        rem         call display-lyric-status-for-file "%tmpfile%" lyriclessness skip_validations
                                        rem )       
                                        if 1 eq %IS_LYRICS% (
                                                call display-lyric-status-for-file "%tmpfile%" lyrics        skip_validations
                                        ) else (
                                                call display-lyric-status-for-file "%tmpfile%" lyriclessness skip_validations
                                        )
                                )
                                
                        :nevermind_on_the_processing                                
                return                                
        :process_done

:END

unset /q USE_SPACER
