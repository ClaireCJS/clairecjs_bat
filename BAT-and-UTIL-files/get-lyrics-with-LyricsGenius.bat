@Echo Off

rem set SKIP_MANUAL_SELECTION=1 to skip the manual slect part

rem CONFIG:
        set PROBER=ffprobe.exe
        set LYRIC_DOWNLOADER_1=lyricsgenius.exe
        SET LYRIC_DOWNLOADER_1_EXPECTED_EXT=JSON 
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=60


rem VALIDATE ENVIRONMENT:
        unset /q LYRIC_RETRIEVAL_1_FAILED
        call validate-in-path %LYRIC_DOWNLOADER_1% %PROBER% tail get-lyrics-with-lyricsgenius-json-processor.pl delete-zero-byte-files unimportant get-lyrics-with-lyricsgenius-json-processor.pl  echos success alarm
        call validate-environment-variables FILEMASK_AUDIO
        call unimportant "validated: lyric downloader, audio file prober"

rem VALIDATE PARAMETERS:
        set AUDIO_FILE=%@UNQUOTE[%1]
        call validate-environment-variable   AUDIO_FILE   "First parameter must be an audio file that exists!"
        call validate-file-extension       "%AUDIO_FILE%" %FILEMASK_AUDIO%
        call validate-in-path               %prober% %lyric_downloader_1% less_important divider debug  delete-zero-byte-files 
        call unimportant                    "input file exists: %1"

rem Get artist and song so we can use them to download lyrics:
        set FILE_ARTIST=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set   FILE_SONG=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=title  -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        call debug "Retrieved:%TAB%   artist=%FILE_ARTIST%%newline%%TAB%%tab%%tab%%tab%    title=%FILE_SONG%"


rem Set our preferred filename for our result:
        set PREFERRED_TEXT_FILE_NAME=%@NAME[%AUDIO_FILE].txt

rem Set potential filenames in our %LYRICS% repository, which can be matched 2 different ways: 
        set MAYBE_SUBDIR_LETTER=@LEFT[1,%file_artist]
        set              MAYBE_LYRICS_1=%lyrics\%MAYBE_SUBDIR_LETTER%\%file_artist% - %zzzzzzz%%@ReReplace[',_,%file_song%].txt
        set MAYBE_LYRICS_1_BROAD_SEARCH=%lyrics\%MAYBE_SUBDIR_LETTER%\%file_artist% - %@left[2,%@ReReplace[',_,%file_song]]*.txt
        set              MAYBE_LYRICS_2=%lyrics\%MAYBE_SUBDIR_LETTER%\%@NAME[%AUDIO_FILE].txt


rem Check if we already have a TXT file in the same folder and shoudln't even be running this:
        iff exist "%PREFERRED_TEXT_FILE_NAME%" then
                call warning "Lyrics already exist for %emphasis%%audio_file%%deemphasis%"
                echo.
                call divider
                echos %ANSI_COLOR_GREEN%
                type "%PREFERRED_TEXT_FILE_NAME%" | insert-before-each-line "        "
                echo.
                call divider
                echo.
                call AskYn "(1) Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then                        
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, so let's remove them and try downloading..."
                        ren  "%PREFERRED_TEXT_FILE_NAME%" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak"
                        goto :End_Of_Check_To_See_If_We_Already_Had_Them
                endiff
        endiff
        :End_Of_Check_To_See_If_We_Already_Had_Them



rem Check if we have one in our lyric repository already, via 2 different filenames, and then manual selection:
        iff exist "%MAYBE_LYRICS_1%" then
                call less_important "We found possible lyrics at %emphasis%%maybe_lyrics_1%%emphasis%!"
                call less_important "Let's review them:"
                call divider
                type "%MAYBE_LYRICS_1%" | insert-before-each-line "        "
                echo.
                call divider
                echo.
                call AskYn "(2) Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then
                        *copy "%MAYBE_LYRICS_1%" "%PREFERRED_TEXT_FILE_NAME%"
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, then..."
                        goto :MaybeLyrics2
                endiff
        endiff

        :MaybeLyrics2
        iff exist "%MAYBE_LYRICS_2%" then
                call less_important "We found possible lyrics at %emphasis%%maybe_lyrics_2%%emphasis%!"
                call less_important "Let's review them:"
                call divider
                type "%MAYBE_LYRICS_2%" | insert-before-each-line "        "
                echo.
                call divider
                echo.
                call AskYn "(3) Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then
                        *copy "%MAYBE_LYRICS_2%" "%PREFERRED_TEXT_FILE_NAME%"
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, then..."
                        goto :TrySelectingSomethingFromOurLyricsArcive
                endiff
        endiff

rem If we still didn't find anything acceptable, but have potentially matching files in our lyric repository, let us select them:
        :TrySelectingSomethingFromOurLyricsArcive
        set TMPREVIEWFILE=%temp%\review-file.%_datetime.%_PID.txt
        iff exist "%MAYBE_LYRICS_1_BROAD_SEARCH%" .and. %SKIP_MANUAL_SELECTION ne 1 then
                repeat 5 echo.
                echo %ANSI_COLOR_SUCCESS%%STAR% Potential lyric files found:
                call pause-for-x-seconds 60 "%underline_on%Select%underline_off% the proper lyrics for '%FILE_SONG%' by '%FILE_ARTIST%' from the %italics_on%next screen%italics_off%, %underline_on%if%underline_off% any are there"
                cls
                echos %@RANDFG_SOFT[]
                select *copy /Ns  ("%MAYBE_LYRICS_1_BROAD_SEARCH%") %TMPREVIEWFILE%
                iff exist %TMPREVIEWFILE% then
                        echo.
                        call divider
                        echos %ANSI_COLOR_YELLOW%
                        type %TMPREVIEWFILE% | insert-before-each-line "        "
                        echo.
                        call divider
                        echo.
                        call AskYn "(4) Do these look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%ANSWER%" eq "Y" then
                                *copy "%TMPREVIEWFILE%" "%PREFERRED_TEXT_FILE_NAME%"
                                goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                        else
                                call warning_soft "Not using them, so let's try downloading..."
                                goto :End_Of_Local_Lyric_Archive_Selection
                        endiff
                endiff
        endiff
        :End_Of_Local_Lyric_Archive_Selection




rem Download the lyrics using LYRIC_DOWNLAODER_1:
        rem Create a tiny file so we don't accidentally do anything latest-file based with any pre-existing files in the folder,
        rem Because later we are doing things with the latest file, but if a failure happens, the latest file could be something
        rem already in the folder.  To prevent that, *this* will be the latest file:
                 >"__"

        rem Create our command:
                set                               LYRIC_RETRIEVAL_COMMAND=%LYRIC_DOWNLOADER_1% song "%FILE_SONG%" "%FILE_ARTIST%" --save
                echo %ANSI_COLOR_DEBUG- COMMAND: %LYRIC_RETRIEVAL_COMMAND%%ANSI_COLOR_NORMAL%
        rem Run our commandit, with a 'y' answer to overwrite:
                                   echo y  |     %LYRIC_RETRIEVAL_COMMAND%

        rem Get the most latest file:
                set LATEST_FILE=%@EXECSTR[dir /b /odt | tail -1]

        rem Generate the proper filename for our freshly-downloaded lyrics, and if it already exists, back it up:
                set PREFERRED_LATEST_FILE_NAME=%@NAME[%AUDIO_FILE].%@EXT[%LATEST_FILE]
                if exist "%PREFERRED_LATEST_FILE_NAME%" (ren /q "%PREFERRED_LATEST_FILE_NAME%" "%PREFERRED_LATEST_FILE_NAME%.%_datetime.bak">nul)

        rem See if our latest file is the expected extension [which would indicate download sucess] or not:
                iff "%@EXT[%LATEST_FILE]" == "%LYRIC_DOWNLOADER_1_EXPECTED_EXT%" then
                        echos %ANSI_COLOR_GREEN%
                        ren /q "%LATEST_FILE%" "%PREFERRED_LATEST_FILE_NAME%" >nul
                else
                        rem (It should be the "__" file if nothing generated)
                        rem call warning "The latest file is not a JSON? It is %LATEST_FILE% .. Does this mean lyrics didn't download?"
                        call warning "No lyrics downloaded."
                        set LYRIC_RETRIEVAL_1_FAILED=1
                        goto :Cleanup
                endiff
                echos %ANSI_RESET%

        rem We are about to make a TXT file. If it exists, better back it up first:
                if exist "%PREFERRED_TEXT_FILE_NAME%" (ren /q "%PREFERRED_TEXT_FILE_NAME" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak">nul)

        rem Create TXT file out of the JSON we downloaded:
                echos %ANSI_COLOR_RUN%
                get-lyrics-with-lyricsgenius-json-processor.pl <"%PREFERRED_LATEST_FILE_NAME%" >"%PREFERRED_TEXT_FILE_NAME%" 

        rem Delete zero-byte txt files, so that if we created an empty file, we don't leave useless trash laying around:
                call delete-zero-byte-files *.txt silent

        rem At this point, our SONG.txt should exist!  If it doesn't, then we rejected all our downloads.
                iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                        call warning "No lyrics downloaded."
                        set LYRIC_RETRIEVAL_1_FAILED=1
                        goto :Cleanup
                endiff


rem Final cleanup
        :Cleanup
        :have_acceptable_lyrics_now_or_at_the_very_least_are_done
        if exist "__" (*del /q "__">nul)

rem Validate we did something:
        if     exist "%PREFERRED_TEXT_FILE_NAME%" (call success "Lyrics downloaded to: %blink_on%%italics_on%%PREFERRED_TEXT_FILE_NAME%%ANSI_RESET%")
        if not exist "%PREFERRED_TEXT_FILE_NAME%" (call warning "Unfortunately, we could not find lyrics for %FILE_ARTIST% - %FILE_SONG%")
