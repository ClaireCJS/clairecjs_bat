@Echo Off


rem CONFIG:
        set PROBER=ffprobe.exe
        set LYRIC_DOWNLOADER=lyricsgenius.exe
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=60


rem VALIDATE ENVIRONMENT:
        unset /q LYRIC_RETRIEVAL_1_FAILED
        call validate-in-path %LYRIC_DOWNLOADER% %PROBER% tail get-lyrics-with-lyricsgenius-json-processor.pl delete-zero-byte-files unimportant get-lyrics-with-lyricsgenius-json-processor.pl  echos success alarm
        call validate-environment-variables FILEMASK_AUDIO
        call unimportant "validated: lyric downloader, audio file prober"

rem VALIDATE PARAMETERS:
        set AUDIO_FILE=%@UNQUOTE[%1]
        call validate-environment-variable   AUDIO_FILE   "First parameter must be an audio file that exists!"
        call validate-file-extension       "%AUDIO_FILE%" %FILEMASK_AUDIO%
        call validate-in-path               %prober% %lyric_downloader% less_important divider debug  delete-zero-byte-files 
        call unimportant                    "input file exists: %1"


rem Get artist and song so we can use them to download lyrics:
        set FILE_ARTIST=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set   FILE_SONG=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=title  -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        call debug "Retrieved:%TAB%   artist=%FILE_ARTIST%%newline%%TAB%%tab%%tab%%tab%    title=%FILE_SONG%"


rem Set our preferred filename for our result:
        set PREFERRED_TEXT_FILE_NAME=%@NAME[%AUDIO_FILE].txt


rem Check if we have one in our lyric repository already:
        set MAYBE_LYRICS=%lyrics\%@LEFT[1,%file_artist]\%file_artist% - *file_song%.txt
        iff exist "%MAYBE_LYRICS%" then
                call less_important "We found possible lyrics at %emphasis%%maybe_lyrics%%emphasis%!"
                call less_important "Let's review them:"
                call divider
                type "%MAYBE_LYRICS%" | insert-before-each-line "        "
                echo.
                call divider
                echo.
                call AskYn "Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then
                        *copy "%MAYBE_LYRICS%" "%PREFERRED_TEXT_FILE_NAME%"
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, then..."
                        goto :Cleanup
                endiff
        endiff
        set MAYBE_GLOB=%lyrics\%@LEFT[1,%file_artist]\%file_artist% - *.txt
        set TMPREVIEWFILE=%temp%\review-file.%_datetime.%_PID.txt
        iff exist "%MAYBE_GLOB%" then
                repeat 5 echo.
                echo %ANSI_COLOR_SUCCESS%%STAR% Potential lyric files found:
                call pause-for-x-seconds 60 "%underline_on%Select%underline_off% the proper lyrics for '%FILE_SONG%' by '%FILE_ARTIST%' from the %italics_on%next screen%italics_off%, %underline_on%if%underline_off% any are there"
                cls
                echos %@RANDFG_SOFT[]
                select *copy /Ns  ("%MAYBE_GLOB%") %TMPREVIEWFILE%
                iff exist %TMPREVIEWFILE% then
                        echo.
                        call divider
                        echos %ANSI_COLOR_YELLOW%
                        type %TMPREVIEWFILE% | insert-before-each-line "        "
                        echo.
                        call divider
                        echo.
                        call AskYn "Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%ANSWER%" eq "Y" then
                                *copy "%%TMPREVIEWFILE%%" "%PREFERRED_TEXT_FILE_NAME%"
                                goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                        else
                                call warning_soft "Not using them, so let's try downloading..."
                                goto :End_Of_Local_Lyric_Archive_Selection
                        endiff
                endiff
        endiff
        :End_Of_Local_Lyric_Archive_Selection

rem Create a tiny file so we don't accidentally do anything latest-file based with any pre-existing files in the folder,
rem Because later we are doing things with the latest file, but if a failure happens, the latest file could be something
rem already in the folder.  To prevent that, *this* will be the latest file:
        >"__"


rem Download the lyrics:
        set                               LYRIC_RETRIEVAL_COMMAND=%LYRIC_DOWNLOADER% song "%FILE_SONG%" "%FILE_ARTIST%" --save
        echo %ANSI_COLOR_DEBUG- COMMAND: %LYRIC_RETRIEVAL_COMMAND%%ANSI_COLOR_NORMAL%
                           echo y  |     %LYRIC_RETRIEVAL_COMMAND%

rem Rename the downloaded lyrics to the right name:
        echos %ANSI_COLOR_GREEN%
        set LATEST_FILE=%@EXECSTR[dir /b /odt | tail -1]
        set        PREFERRED_LATEST_FILE_NAME=%@NAME[%AUDIO_FILE].%@EXT[%LATEST_FILE]
        if exist "%PREFERRED_LATEST_FILE_NAME%" (ren /q "%PREFERRED_LATEST_FILE_NAME%" "%PREFERRED_LATEST_FILE_NAME%.%_datetime.bak">nul)
        iff "%@EXT[%LATEST_FILE]" == "JSON" then
                ren /q "%LATEST_FILE%" "%PREFERRED_LATEST_FILE_NAME%" >nul
        else
                rem (It should be the "__" file if nothing generated)
                rem call warning "The latest file is not a JSON? It is %LATEST_FILE% .. Does this mean lyrics didn't download?"
                call warning "No lyrics downloaded."
                set LYRIC_RETRIEVAL_1_FAILED=1
                goto :Cleanup
        endiff
        echos %ANSI_RESET%

        if exist "%PREFERRED_TEXT_FILE_NAME%" (ren /q "%PREFERRED_TEXT_FILE_NAME" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak">nul)
        echos %ANSI_COLOR_RUN%
        (get-lyrics-with-lyricsgenius-json-processor.pl <"%PREFERRED_LATEST_FILE_NAME%" >"%PREFERRED_TEXT_FILE_NAME%" )| copy-move-post nomoji
        call delete-zero-byte-files *.txt silent
        iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                call warning "No lyrics downloaded."
                set LYRIC_RETRIEVAL_1_FAILED=1
                goto :Cleanup
        endiff


rem If we ended up with a zero result, don't leave a blank file:
        :Cleanup
        call delete-zero-byte-files *.txt silent


rem Validate we did something:
        :have_acceptable_lyrics_now_or_at_the_very_least_are_done
        if     exist "%PREFERRED_TEXT_FILE_NAME%" (call success "Lyrics downloaded to: %blink_on%%italics_on%%PREFERRED_TEXT_FILE_NAME%%ANSI_RESET%")
        if not exist "%PREFERRED_TEXT_FILE_NAME%" (call warning "Unfortunately, we could not find lyrics for %FILE_ARTIST% - %FILE_SONG%")
        if exist "__" (*del /q "__">nul)
