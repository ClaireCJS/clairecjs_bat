@Echo Off
@on break cancel

rem Set our lyric filemask:
        set FILEMASK_LYRICS_TEMP=*.txt

rem If we passed a parameter, we are operating on a single file:
        iff "%1" eq "/?" then
                %color_advice%
                echo %ansi_color_advice%
                echo    display-lyric-status {lyric_file.txt} - displays lyric status for 1 file
                echo                                            `^^^^^^^^^^^^^^^^^^^^^` sets LYRIC_STATUS={status value} as a return value
                echo    display-lyric-status     {*frog*.txt} - displays lyric status for files matching filecard
                echo    display-lyric-status                  - displays lyric status for all files
                echo
                echo
                echo  NOTE: Can also be run on an audiofile to display its lyric%italics_on%lessness%italics_off% status
                
                %color_normal%
                echos %ansi_reset%
                goto :END
        endiff
        iff "%1" ne "" then
                rem When operating on a single file, make sure it is the correct extension prior to displaying the lyrics:
                        call validate-is-extension %1 %FILEMASK_LYRICS_TEMP% "1ˢᵗ arg must be a file that matches “%italics_on%%FILEMASK_LYRICS_TEMP%%italics_off%”"
                        call display-lyric-status-for-file %*
                        goto :END
        endiff

rem Make sure some important environment variables actually exist:
       if not defined FILEMASK_AUDIO set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        if not defined RED_X          set RED_X=%@CHAR[10060]%@CHAR[0]

rem Validate environment once per session:
        iff 1 ne %VALIDATED_DLS% then
                call validate-in-path display-lyric-status-for-file validate-environment-variable warning 
                call validate-environment-variable filemask_audio
                set  VALIDATED_DLS=1
        endiff

rem Don’t do anything if any potential lyric files do not exist
        iff not exist %FILEMASK_LYRICS_TEMP% then
                echo.
                call warning "No lyric files here." silent
                goto :END
        endiff                

rem Count how many files we will be displaying the status of:
        set USE_SPACER=1
        set NUM_LYRICS_FOUND=0
        for %%tmpfile in (%FILEMASK_LYRICS_TEMP%) do (
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
        
rem Go through each file, displaying it’s lyric status *if* it is a sidecar file to an audio file:       
        for %%tmptmpfile in (%FILEMASK_AUDIO%) do gosub process "%tmptmpfile%"
        goto    :process_done
                :process [tmptmpfile]
                        set tmpfile=%@unquote[%tmptmpfile%]
                        set "dls_processed_%tmpfile%=1"
                        set BASENAME=%@name[%tmpFile%]
                        set TMP_LYRIC_OR_SONG_FILE=
                        
                        rem Check if it has a sidecar audio file:                
                                set FOUND=0
                                for %%E in (%FILEMASK_LYRICS_TEMP%) do (
                                    if exist "%BASENAME%%%~xE" (
                                        set comment=echo Found sidecar file: %BASENAME%%%~xE
                                        set TMP_LYRIC_OR_SONG_FILE=%@UNQUOTE[%BASENAME%%%~xE]
                                        set FOUND=1
                                    )
                                )

                        rem Display the lyric status if a sidecar file was found, or another message if one was not:
                                if 1 eq %FOUND% (
                                        call display-lyric-status-for-file "%TMP_LYRIC_OR_SONG_FILE%"
                                ) else (                                
                                        rem The old way, before lyriclessness was approveable:
                                        rem if 1 eq %USE_SPACER% (
                                        rem        echo %@CHAR[55357]%@CHAR[56590] %@CHAR[27][38;2;98;108;22m%red_x% No corresponding lyric file for: %@CHAR[27][38;2;68;78;15m%italics_on%%@FULL[%tmpFile%]%italics_off%%faint_off%
                                        rem  else (
                                        rem        echo %@CHAR[55357]%@CHAR[56590] %@CHAR[27][38;2;98;108;22mNo corresponding lyric for: %@CHAR[27][38;2;68;78;15m%italics_on%%@FULL[%tmpFile%]%italics_off%%faint_off%
                                        rem )
                                        
                                        rem at this point, the songfile “%tmpfile%” ’‘’"“”“”does not have a lyric file,
                                        rem so we need to see if it’s lyriclessness has been approved or not
                                )       
                return                                
        :process_done

:END

unset /q USE_SPACER
