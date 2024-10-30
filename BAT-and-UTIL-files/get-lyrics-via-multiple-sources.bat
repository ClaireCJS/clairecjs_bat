@Echo Off

REM USAGE: <this> {audio_filename} [optional mode]
rem                                 ^^^^^^^^^^^^^^
rem                                   \__ mode can be: 
rem                                           1) SetVarsOnly to just set the MAYBE_LYRICS_1/2/BROAD_SEARCH environment variables


rem set SKIP_MANUAL_SELECTION=1 to skip the manual select part

rem CONFIG:
        set PROBER=ffprobe.exe
        set LYRIC_DOWNLOADER_1=lyricsgenius.exe               %+ rem LyricsGenius.exe is a Python package from github —— https://github.com/johnwmillr/LyricsGenius  ... There's also this website, though I'm not sure if it's the same thing: https://lyricsgenius.readthedocs.io/en/master/
        SET LYRIC_DOWNLOADER_1_EXPECTED_EXT=JSON              %+ rem LyricsGenius.exe downloads files in JSON format. And the output filename isn't really specifiable, which creates issues. (Solution: Create temp file, run, see if latest file date-wise is the temp file you created or not, if not, then that's the output file)
        set MOST_BYTES_THAT_LYRICS_COULD_BE=7500             
rem CONFIG: WAIT TIMES:                                      
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=60           %+ rem How long to show lyrics on the screen for them to get approval or not
        set LYRIC_SELECT_FROM_FILELIST_WAIT_TIME=120          %+ rem how long to get an affirmative response on selecting a file from multilpe files [which can't be done in automatic mode], before proceeding on 
        set PAUSED_DEBUG_WAIT_TIME=5                          %+ rem how long to pause on debug statements we're particularly focusing on
        set HAND_EDIT_ARTIST_AND_SONG_PROMPT_WAIT_TIME=30


rem Remove any trash environment variables left over from a previously-aborted run which might interfere with the current run:
        unset /q LYRIC_RETRIEVAL_1_FAILED
        unset /q LD1_MASSAGED_ATTEMPT_1

rem VALIDATE ENVIRONMENT [once per session]:
        iff 1 ne %VALIDATED_GLVMS_ENV then
                call validate-in-path              %LYRIC_DOWNLOADER_1% %PROBER% delete-zero-byte-files get-lyrics-with-lyricsgenius-json-processor.pl tail echos  divider unimportant success alarm unimportant debug warning error fatal_error advice  important important_less celebrate eset
                call unimportant        "Validated: lyric downloader, audio file prober"
                call validate-environment-variables TEMP LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME LYRIC_SELECT_FROM_FILELIST_WAIT_TIME FILEMASK_AUDIO cool_question_mark ANSI_COLOR_BRIGHT_RED italics_on italics_off ANSI_COLOR_BRIGHT_YELLOW blink_on blink_off star ANSI_COLOR_GREEN  ansi_reset bright_on bright_off   underline_on underline_off    emoji_warning check EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT
                call validate-is-function           cool_text

                set VALIDATED_GLVMS_ENV=1
        endiff

rem VALIDATE PARAMETERS [every time]:
        set AUDIO_FILE=%@UNQUOTE[%1]
        call validate-environment-variable   AUDIO_FILE   "First parameter must be an audio file that exists!"
        call validate-file-extension       "%AUDIO_FILE%" %FILEMASK_AUDIO%
        call unimportant                    "input file exists: %1"

rem Get artist and song so we can use them to download lyrics:
        set FILE_ARTIST=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set   FILE_SONG=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=title  -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]

        if "%2" eq "SetVarsOnly" (goto :SetVarsOnly_skip_to_1)

        call debug "Retrieved:%TAB%   artist=%FILE_ARTIST%%newline%%TAB%%tab%%tab%%tab%        title=%FILE_SONG%"


rem Set our preferred filename for our result:
        set PREFERRED_TEXT_FILE_NAME=%@NAME[%AUDIO_FILE].txt

rem Set potential filenames in our %LYRICS% repository, which can be matched 2 different ways: 
rem NOTE: This code is copied in create-lrc-from-file so we must update it there too
        :SetVarsOnly_skip_to_1
        set MAYBE_SUBDIR_LETTER=%@LEFT[1,%file_artist]
        set              MAYBE_LYRICS_1=%lyrics\%MAYBE_SUBDIR_LETTER%\%file_artist% - %zzzzzzz%%@ReReplace[',_,%file_song%].txt
        set MAYBE_LYRICS_1_BROAD_SEARCH=%lyrics\%MAYBE_SUBDIR_LETTER%\%file_artist% - %@LEFT[2,%@ReReplace[',_,%file_song]]*.txt
        set              MAYBE_LYRICS_2=%lyrics\%MAYBE_SUBDIR_LETTER%\%@NAME[%AUDIO_FILE].txt
        if "%2" eq "SetVarsOnly" (goto :SetVarsOnly_skip_to_2)



rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Check if we already have a TXT file in the same folder and shouldn't even be running this:
        iff exist "%PREFERRED_TEXT_FILE_NAME%" then
                call warning "Lyrics already exist for %emphasis%%audio_file%%deemphasis%"
                echo.
                call divider
                echos %ANSI_COLOR_GREEN%
                type "%PREFERRED_TEXT_FILE_NAME%" |:u8 insert-before-each-line "        "
                echo.
                call divider
                echo.
                call AskYn "(1) Do these lyrics %italics_on%we already have%italics_off% look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then                        
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, so let's remove them and try downloading..."
                        ren  /q "%PREFERRED_TEXT_FILE_NAME%" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak"
                        goto :End_Of_Check_To_See_If_We_Already_Had_Them
                endiff
        endiff
        :End_Of_Check_To_See_If_We_Already_Had_Them
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Check if we have one in our lyric repository already, via 2 different filenames, and then manual selection:
        call debug "Checking for %MAYBE_LYRICS_1%" 
        iff exist "%MAYBE_LYRICS_1%" then
                call less_important "We found possible lyrics at %emphasis%%maybe_lyrics_1%%emphasis%!"
                call less_important "Let's review them:"
                call divider
                type "%MAYBE_LYRICS_1%" |:u8 insert-before-each-line "        "
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
        call debug "Checking for %MAYBE_LYRICS_2%" 
        iff exist "%MAYBE_LYRICS_2%" then
                call less_important "We found possible lyrics at %emphasis%%maybe_lyrics_2%%emphasis%!"
                call less_important "Let's review them:"
                call divider
                type "%MAYBE_LYRICS_2%" |:u8 insert-before-each-line "        "
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
        :TrySelectingSomethingFromOurLyricsArchive
        set TRY_SELECTION_AGAIN=0
        iff exist "%MAYBE_LYRICS_1_BROAD_SEARCH%" .and. %SKIP_MANUAL_SELECTION ne 1 then
                call debug "Checking for %MAYBE_LYRICS_1_BROAD_SEARCH%" 
                repeat 5 echo.
                call divider
                echo.
                echo %ANSI_COLOR_SUCCESS%%STAR% Potential lyric files found:
                dir /b "%MAYBE_LYRICS_1_BROAD_SEARCH%" |:u8 insert-before-each-line "        %cool_question_mark%%cool_question_mark% " 
                call AskYn "%underline_on%Select%underline_off% from one of these files, for '%italics_on%%FILE_SONG%%italics_off%' by '%italics_on%%FILE_ARTIST%%italics_off%'" no %LYRIC_SELECT_FROM_FILELIST_WAIT_TIME% 
                iff "%answer%" ne "Y" then
                        call less_important "Skipping selecting from potential files..."
                else
                        set TMPREVIEWFILE=%temp%\review-file.%_datetime.%_PID.txt
                        cls
                        echos %@RANDFG_SOFT[]
                        set tmptitle=%_title
                        title %file_song% - %file_artist%
                        select *copy /Ns  ("%MAYBE_LYRICS_1_BROAD_SEARCH%") %TMPREVIEWFILE%
                        title %_title
                        iff exist %TMPREVIEWFILE% then
                                echo.
                                call divider
                                echos %ANSI_COLOR_YELLOW%
                                type %TMPREVIEWFILE% |:u8 insert-before-each-line "        "
                                echo.
                                call divider
                                echo.
                                call AskYn "(4) Do these lyrics %italics_on%from our lyrics repository%italics_off% look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                                iff "%ANSWER%" eq "Y" then
                                        *copy "%TMPREVIEWFILE%" "%PREFERRED_TEXT_FILE_NAME%"
                                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                                else
                                        call important_less "We have rejected this set of lyrics"
                                        echo.
                                        rem instead of this: goto :End_Of_Local_Lyric_Archive_Selection
                                        rem if we go back to the beginning, we can allow trying of multiple 
                                        rem                                 files before finally giving up
                                        rem This seemed to not workgoto: TrySelectingSomethingFromOurLyricsArchive
                                        set TRY_SELECTION_AGAIN=1
                                endiff
                        endiff
                endiff
        endiff
        if "%TRY_SELECTION_AGAIN%" == "1" (goto :TrySelectingSomethingFromOurLyricsArchive)
        :End_Of_Local_Lyric_Archive_Selection
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Set the values that we will use when using LYRIC_DOWNLOADER_1 the first time [they get changed during subsequent download attempts]:
        set FILE_SONG_TO_USE=%FILE_SONG%
        set FILE_ARTIST_TO_USE=%FILE_ARTIST%

rem Download the lyrics using LYRIC_DOWNLOADER_1: BEGIN: ————————————————————————————————————————————————————————————————————————————————————
        :download_with_lyric_downloader_1
        rem Create a tiny file so we don't accidentally do anything latest-file based with any pre-existing files in the folder,
        rem Because later we are doing things with the latest file, but if a failure happens, the latest file could be something
        rem already in the folder.  To prevent that, *this* will be the latest file:
                 >"__"

        rem Create our command:
                set                               LYRIC_RETRIEVAL_COMMAND=%LYRIC_DOWNLOADER_1% song "%FILE_SONG_TO_USE%" "%FILE_ARTIST_TO_USE%" --save
                rem  %ANSI_COLOR_DEBUG- COMMAND: %LYRIC_RETRIEVAL_COMMAND%%ANSI_COLOR_NORMAL%
                echo.
                call divider
                echo.
                echo %ANSI_COLOR_IMPORTANT_LESS%%STAR% Searching lyrics for '%italics_on%%FILE_SONG_TO_USE%%italics_off%' by '%italics_on%%FILE_ARTIST_TO_USE%%italics_off%'%ANSI_RESET%
        rem Run our command, with a 'y' answer to overwrite:
                echos %ANSI_COLOR_RUN%
                echo y  |  %LYRIC_RETRIEVAL_COMMAND%  |:u8 insert-before-each-line "            "
                call errorlevel "Problem retrieving lyrics in %0"

        rem Get the most latest file:
                set LATEST_FILE=%@EXECSTR[dir /b /odt | tail -1]

        rem Generate the proper filename for our freshly-downloaded lyrics, and if it already exists, back it up:
                set PREFERRED_LATEST_FILE_NAME=%@NAME[%AUDIO_FILE].%@EXT[%LATEST_FILE]
                if exist "%PREFERRED_LATEST_FILE_NAME%" (ren /q "%PREFERRED_LATEST_FILE_NAME%" "%PREFERRED_LATEST_FILE_NAME%.%_datetime.bak">nul)

        rem See if our latest file is the expected extension [which would indicate download sucess] or not:
                set  MYSIZEY=%@FILESIZE[%LATEST_FILE]
                iff %MYSIZEY% gt %MOST_BYTES_THAT_LYRICS_COULD_BE% then  
                        call warning "Caution! Download is %MYSIZEY%b, larger than threshold of %MOST_BYTES_THAT_LYRICS_COULD_BE%b"
                        call pause-for-x-seconds 8 %+ rem 🐐goat hardcode
                endiff
                iff "%@EXT[%LATEST_FILE]" == "%LYRIC_DOWNLOADER_1_EXPECTED_EXT%" then
                        echos %ANSI_COLOR_GREEN%
                        ren /q "%LATEST_FILE%" "%PREFERRED_LATEST_FILE_NAME%" >nul
                else
                        rem (It should be the "__" file if nothing generated)
                        rem call warning "The latest file is not a JSON? It is %LATEST_FILE% .. Does this mean lyrics didn't download?"
                        call warning "(A) No lyrics downloaded."
                        set LYRIC_RETRIEVAL_1_FAILED=1
                        rem goto :Cleanup
                        rem Actually, just continue... We will try again with different values
                        rem Actually, skip forward, but not to cleanup
                        goto :skip_from_nothing_downloaded
                endiff
                echos %ANSI_RESET%

        rem We are about to make a TXT file. If it exists, better back it up first:
                if exist "%PREFERRED_TEXT_FILE_NAME%" (ren /q "%PREFERRED_TEXT_FILE_NAME" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak">nul)

        rem Create TXT file out of the JSON we downloaded, using our Perl postprocessor:
                echos %ANSI_COLOR_RUN%
                get-lyrics-with-lyricsgenius-json-processor.pl <"%PREFERRED_LATEST_FILE_NAME%" >"%PREFERRED_TEXT_FILE_NAME%" 

        rem Delete zero-byte txt files, so that if we created an empty file, we don't leave useless trash laying around:
                call delete-zero-byte-files *.txt silent

        rem At this point, our SONG.txt should exist!  If it doesn't, then we rejected all our downloads.
                iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                        call warning "(B) No lyrics downloaded."
                        set LYRIC_RETRIEVAL_1_FAILED=1
                else
                        echo.
                        call divider
                        echo %ANSI_COLOR_BRIGHT_YELLOW%"
                        type "%PREFERRED_TEXT_FILE_NAME%" |:u8 insert-before-each-line "        "
                        call AskYn "(6) Do these %italics_on%downloaded%italics_off% lyrics for '%italics_on%%FILE_song_TO_USE%%italics_off%' by '%italics_on%%FILE_artist_TO_USE%%italics_off%' look acceptable" yes %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%ANSWER%" eq "Y" then
                                goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                                *del /q "%PREFERRED_TEXT_FILE_NAME%" >nul
                        else
                                rem Continue on but delete the file to indicate its rejection
                                ren  "%PREFERRED_TEXT_FILE_NAME%" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak"
                        endiff
                        rem no? call important "TODO: INSERT LYRIC REVIEW HERE TO SUPLICATE THE REDUNDANT ONE IN CALLING SCRIPT 🐐🐐🐐"
                endiff
                :end_of_massage_attempt

                :skip_from_nothing_downloaded


rem Get massaged names for next section's check:
        rem Massage some problematic subsets of these fields:
        rem 1) Remove things in parenthesis
        rem 2) remove "The "
                set FILE_ARTIST_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_ARTIST%]]
                set   FILE_SONG_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_SONG%]]
                call debug "Massaged: %TAB%   artist=%FILE_ARTIST_MASSAGED%%newline%%TAB%%tab%%tab%%tab%        title=%FILE_SONG_MASSAGED%"


rem try again if massaged names exist (that is, if the massaged names are different than the original names):        
        echo %ANSI_COLOR_DEBUG%- DEBUG: iff 1 ne %LD1_MASSAGED_ATTEMPT_1% .and. ("%FILE_SONG_MASSAGED%" != "%FILE_SONG_TO_USE%" .or. "%FILE_artist_MASSAGED%" != "%FILE_artist_TO_USE%") then
        call pause-for-x-seconds %paused_debug_wait_time%
        if 1 eq LD1_MASSAGED_ATTEMPT_1 (goto :Already_Did_Massaged)
        iff "1" ne "%LD1_MASSAGED_ATTEMPT_1%" .and. ("%FILE_SONG_MASSAGED%" != "%FILE_SONG%" .or. "%FILE_artist_MASSAGED%" != "%FILE_artist%") then
                call warning_soft "Let's try downloading with the massaged names (%FILE_ARTIST_MASSAGED% - %FILE_SONG_MASSAGED%)..."
                call pause-for-x-seconds 8                                                                %+ rem 🐐hardcoded value🐐
                set FILE_SONG_TO_USE=%FILE_SONG_MASSAGED%
                set FILE_ARTIST_TO_USE=%FILE_ARTIST_MASSAGED%
                set LD1_MASSAGED_ATTEMPT_1=1
                echos %ANSI_COLOR_DEBUG%- DEBUG set LD1_MASSAGED_ATTEMPT_1 to %LD1_MASSAGED_ATTEMPT_1%
                goto :download_with_lyric_downloader_1
        endiff
        :Already_Did_Massaged
        ren /q "%PREFERRED_TEXT_FILE_NAME" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak">nul
        call important_less "These lyrics have been rejected as well"
        rem no! goto :end_of_massage_attempt
        rem Continue on... We have failed so far.



rem If we still don't have anything, let us manually edit the song and artist name if we want
        iff exist "%PREFERRED_TEXT_FILE_NAME%" (goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done)

        rem rainbow divider here?
        call AskYN "Want to try hand-editing the artist & song name" no %HAND_EDIT_ARTIST_AND_SONG_PROMPT_WAIT_TIME%
        if "%answer%" == "N" (goto :Skip_Hand_Editing)

        eset FILE_ARTIST
        eset FILE_SONG

        set FILE_SONG_TO_USE=%FILE_SONG%
        set FILE_ARTIST_TO_USE=%FILE_ARTIST%

        goto :download_with_lyric_downloader_1
        :Skip_Hand_Editing







                :end_of_lyric_downloader_1
rem Download the lyrics using LYRIC_DOWNLOADER_1: END: —————————————————————————————————————————————————————————————————————————————————————


rem Final cleanup
        :have_acceptable_lyrics_now_or_at_the_very_least_are_done
        :Cleanup
        if exist "__" (*del /q "__">nul)
        unset /q LYRIC_RETRIEVAL_1_FAILED
        unset /q LD1_MASSAGED_ATTEMPT_1

rem Validate we did something:
        echo %ANSI_COLOR_DEBUG%- DEBUG: iff not exist "%PREFERRED_TEXT_FILE_NAME%" 
        iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                echo.
                call divider
                echo.
                call bigecho "%emoji_warning% LYRIC FAIL %emoji_warning%"
                call warning "Unfortunately, we could not find lyrics for %ANSI_COLOR_BRIGHT_RED%%ITALICS_On%%FILE_ARTIST% - %FILE_SONG%%ITALICS_OFF%")
                title %emoji_warning% Lyrics not fetched %emoji_warning%
        else
                rem  celebrate "%check% LYRIC SUCCESS %check%" 2
                call celebrate "%ansi_background_black% %check% %@cool[LYRIC SUCCESS] %check% %@randfg[]" 2
                call success "Lyrics downloaded to: %blink_on%%italics_on%%PREFERRED_TEXT_FILE_NAME%%ANSI_RESET%"
                title %check% Lyrics fetched successfully! %check% 
        endiff



:SetVarsOnly_skip_to_2
:The_VERY_End

