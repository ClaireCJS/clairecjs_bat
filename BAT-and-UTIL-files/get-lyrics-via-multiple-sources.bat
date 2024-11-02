@Echo Off

:USAGE: USAGE: <this> {audio_filename} [optional mode]
:USAGE:                                 ^^^^^^^^^^^^^^
:USAGE:                                   \__ mode can be: 
:USAGE:                                           1) SetVarsOnly to just set the MAYBE_LYRICS_1/2/BROAD_SEARCH environment variables
:USAGE: Forms of automation:
:USAGE:     if CONSIDER_ALL_LYRICS_APPROVED=1     //automatically approves lyrics at first prompt and reduces prompt from %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME% to %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME_AUTO% seconds


rem TODO check if lyric file is approved [somehow--see create-lyrics for ideas]
rem ——————————————————————————————————————————————————————————————————————————————————————————



rem call bigecho CONSIDER_ALL_LYRICS_APPROVED is %CONSIDER_ALL_LYRICS_APPROVED% 
rem set SKIP_MANUAL_SELECTION=1 to skip the manual select part

rem CONFIG: PROBER:
        set PROBER=ffprobe.exe                                     

rem CONFIG: DOWNLOADER:
        set LYRIC_DOWNLOADER_1=lyricsgenius.exe                       %+ rem LyricsGenius.exe is a Python package from github —— https://github.com/johnwmillr/LyricsGenius  ... There's also this website, though I'm not sure if it's the same thing: https://lyricsgenius.readthedocs.io/en/master/
        SET LYRIC_DOWNLOADER_1_EXPECTED_EXT=JSON                      %+ rem LyricsGenius.exe downloads files in JSON format. And the output filename isn't really specifiable, which creates issues. (Solution: Create temp file, run, see if latest file date-wise is the temp file you created or not, if not, then that's the output file)
        set LYRIC_DOWNLOADER_1_SOURCE=Genius                          %+ rem Where the LYRIC_DOWNLOADER gets its stuff from — Genius, SongText, etc
        set MOST_BYTES_THAT_LYRICS_COULD_BE=10000                     %+ rem due to HTML, this is rather useless. Originally thought it was a chracter count of just the lyrics themselves.            

rem CONFIG: LYRIC-GOOGLE'ING BEHAVIOR:
        set AUTOMATIC_HAND_EDITING_IF_GOOGLING=0                      %+ rem It turns out that it's annoying to have an empty TXT file opened up, Google and find no lyrics, then have the file be auto-deleted for being 0-bytes, then have the text editor complain that the file you have open no longer exists. It may make more sense to ask for hand editing AFTER googling... If we have results, yes to hand edit so we can paste them in. Otherwise, no.

rem CONFIG: WAIT TIMES:                                      
        SET ADDITIONAL_HAND_EDIT_WAIT_TIME_IF_THEY_GOOGLED=75         %+ rem Additional wait time to add on to last value in the event that they Googled the lyrics [to give time to check out the google resuls before the Yes/No prompt expires]
        set LARGE_DOWNLOAD_WARNING_WAIT_TIME=1                        %+ rem Wait time after announcing that the lyrics downloaded seemed larger than expected [pretty uselessi n practice]
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=180                  %+ rem How long to show lyrics on the screen for them to get approval or not —— was 60 but running this while playing games made me miss the prompt so increased to 180
        set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME_AUTO=5               %+ rem How long to show lyrics on the screen for them to get approval or not —— if the environment variable says they are already pre-approved
        set LYRIC_SELECT_FROM_FILELIST_WAIT_TIME=120                  %+ rem how long to get an affirmative response on selecting a file from multilpe files [which can't be done in automatic mode], before proceeding on 
        set WAIT_AFTER_ANNOUNCING_MASSAGED_SEARCH=0                   %+ rem How long to wait after displaying the massaged artist/title prior to searching for the (if the 1st search with non-massaged failed). If set to 0, there will be no notice at all
        set HAND_EDIT_ARTIST_AND_SONG_AND_LYRICS_PROMPT_WAIT_TIME=30  %+ rem how long to wait for "hand edit these lyrics?"-type questions
        set GOOGLE_FOR_LYRICS_PROMPT_WAIT_TIME=15                     %+ rem how long to pause on "do you want to google the lyrics?"-type questions
        set LONGEST_POSSIBLE_HAND_EDIT_TIME_IN_SECONDS=900            %+ rem give us 15 minutes to hand edit in case we get distracted
        set PAUSED_DEBUG_WAIT_TIME=5                                  %+ rem how long to pause on debug statements we're particularly focusing on

rem CONFIG: WAIT TIMES: IF LYRICS ARE PRE-APPROVED:
iff 1 eq %CONSIDER_ALL_LYRICS_APPROVED% then
        set LARGE_DOWNLOAD_WARNING_WAIT_TIME=0                        %+ rem Wait time after announcing that the lyrics downloaded seemed larger than expected [pretty uselessi n practice]
        set LYRIC_SELECT_FROM_FILELIST_WAIT_TIME=1                    %+ rem how long to get an affirmative response on selecting a file from multilpe files [which can't be done in automatic mode], before proceeding on 
        set WAIT_AFTER_ANNOUNCING_MASSAGED_SEARCH=0                   %+ rem How long to wait after displaying the massaged artist/title prior to searching for the (if the 1st search with non-massaged failed)
        set HAND_EDIT_ARTIST_AND_SONG_AND_LYRICS_PROMPT_WAIT_TIME=1   %+ rem how long to wait for "hand edit these lyrics?"-type questions
        set GOOGLE_FOR_LYRICS_PROMPT_WAIT_TIME=1                      %+ rem how long to pause on "do you want to google the lyrics?"-type questions
        SET ADDITIONAL_HAND_EDIT_WAIT_TIME_IF_THEY_GOOGLED=1          %+ rem Additional wait time to add on to last value in the event that they Googled the lyrics [to give time to check out the google resuls before the Yes/No prompt expires]
endiff

rem Remove any trash environment variables left over from a previously-aborted run which might interfere with the current run:
        unset /q LYRIC_RETRIEVAL_1_FAILED
        unset /q LD1_MASSAGED_ATTEMPT_1
        unset /q WE_GOOGLED
        unset /q TRY_SELECTION_AGAIN

rem VALIDATE ENVIRONMENT [once per session]:
        iff 1 ne %VALIDATED_GLVMS_ENV then
                call validate-in-path              %LYRIC_DOWNLOADER_1% %PROBER% delete-zero-byte-files get-lyrics-with-lyricsgenius-json-processor.pl tail echos  divider unimportant success alarm unimportant debug warning error fatal_error advice  important important_less celebrate eset insert-before-each-line.pl insert-before-each-line.py pause-alias google.bat google.py google.pl insert-before-each-line.py
                call unimportant        "Validated: lyric downloader, audio file prober"
                call validate-environment-variables TEMP LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME LYRIC_SELECT_FROM_FILELIST_WAIT_TIME FILEMASK_AUDIO cool_question_mark ANSI_COLOR_BRIGHT_RED italics_on italics_off ANSI_COLOR_BRIGHT_YELLOW blink_on blink_off star ANSI_COLOR_GREEN  ansi_reset bright_on bright_off   underline_on underline_off    emoji_warning check EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT EMOJI_red_QUESTION_MARK LONGEST_POSSIBLE_HAND_EDIT_TIME_IN_SECONDS ANSI_COLOR_WARNING_SOFT LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME_AUTO ANSI_COLOR_DEBUG
                call validate-is-function           cool_text
                call checkeditor
                set  VALIDATED_GLVMS_ENV=1
        endiff

rem USAGE:
        iff "%1" == "" then
                echo.
                call divider
                %color_advice%
                echo USAGE: %0 {audio_file}
                echo                 ...where audio_file is the audio file who's tags will be examined to obtain the artist name and song title
                echo.
                echo ALTERNATE USAGE: %0 {audio_file} SetVarsOnly —— sets the FILE_SONG and FILE_ARTIST / album / orig_artist environment variables for this song, but does nothing else
                call divider
                goto :END
        endiff

rem VALIDATE PARAMETERS [every time]:
        set  AUDIO_FILE=%@UNQUOTE[%1]
        call validate-environment-variable   AUDIO_FILE   "First parameter must be an audio file that exists!"
        call validate-file-extension       "%AUDIO_FILE%" %FILEMASK_AUDIO%

rem ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem Get artist and song so we can use them to download lyrics:
        if %DEBUG gt 0 call unimportant "Probing file"
        set       FILE_ALBUM=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=album  -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set      FILE_ARTIST=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set        FILE_SONG=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=title  -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set FILE_ORIG_ARTIST=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=TOPE   -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set       FILE_TITLE=%FILE_SONG%
        if %DEBUG gt 0 call unimportant "Probing done" 
        rem "Title" is better than "Song", but we are doing both for ease of remembrance

rem Update window title:
        if %DEBUG gt 0 call unimportant "setting window title to %FILE_ARTIST% – %FILE_SONG%"
        set title=%FILE_ARTIST% – %FILE_SONG%
        title %title%
        if %vebose gt 0 call unimportant "Title set" 

rem Back up original values of these variables because we change them as we try various different ways of searching:
        set      FILE_ARTIST_ORIGINAL=%FILE_ARTIST%
        set FILE_ORIG_ARTIST_ORIGINAL=%FILE_ORIG_ARTIST%
        set       FILE_ALBUM_ORIGINAL=%FILE_ALBUM%
        set        FILE_SONG_ORIGINAL=%FILE_SONG%
        set       FILE_TITLE_ORIGINAL=%FILE_SONG%
        if %vebose gt 0 call unimportant "Original values saved" 

rem First things first——If it's a cover song, and we know the original artist, we should search for lyrics by the original artist
        if "%FILE_ARTIST%" ne "%FILE_ORIG_ARTIST%" .and. "" ne "%FILE_ORIG_ARTIST%" (set FILE_ARTIST=%FILE_ORIG_ARTIST%)

rem If we are in the special mode where we ONLY set environment variables, go to that section:
        if "%2" eq "SetVarsOnly" (goto :SetVarsOnly_skip_to_1)

rem ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


rem Debug info:
        call unimportant                    "input file exists: %1"
        call debug "Retrieved:%TAB%   artist=%FILE_ARTIST%%newline%%TAB%%tab%%tab%%tab%        title=%FILE_SONG%%newline%%TAB%%tab%%tab%%tab%        album=%FILE_ALBUM%%newline%%TAB%%tab%%tab%%tab%  orig artist=%FILE_ORIG_ARTIST%"
        if %vebose gt 0 call unimportant "Debug info printed" 

rem ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem Set our preferred filename for our result:
        set PREFERRED_TEXT_FILE_NAME=%@NAME[%AUDIO_FILE].txt

rem ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Set potential filenames in our %LYRICS% repository, which can be matched 2 different ways: 
rem NOTE: This code is copied in create-lrc-from-file so we must update it there too
        :SetVarsOnly_skip_to_1
        set MAYBE_SUBDIR_LETTER=%@LEFT[1,%file_artist]
        set              MAYBE_LYRICS_1=%lyrics\%MAYBE_SUBDIR_LETTER%\%file_artist% - %zzzzzzz%%@ReReplace[',_,%file_song%].txt
        set MAYBE_LYRICS_1_BROAD_SEARCH=%lyrics\%MAYBE_SUBDIR_LETTER%\%file_artist% - %@LEFT[3,%@ReReplace[',_,%file_song]]*.txt
        set              MAYBE_LYRICS_2=%lyrics\%MAYBE_SUBDIR_LETTER%\%@NAME[%AUDIO_FILE].txt
        if "%2" eq "SetVarsOnly" (goto :SetVarsOnly_skip_to_2)
        if %vebose gt 0 call unimportant "Broad serach parameters generated" 


rem If we have set CONSIDER_ALL_LYRICS_APPROVED=1, then auto-approve lyrics at this first prompt, and reduce the time-wait on that prompt:
        iff "1" == "%CONSIDER_ALL_LYRICS_APPROVED%" then
                echo %ANSI_COLOR_WARNING_SOFT%%STAR% %italics_on%Automatic%italics_off% acceptance of lyrics at prompt#1 turned %blink_on%on%blink_off% %ANSI_COLOR_NORMAL%
                set DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1=yes
                set LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME=%LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME_AUTO%
        else
                echo %ANSI_COLOR_DEBUG%%STAR% %italics_on%Automatic%italics_off% acceptance of lyrics at prompt#1 turned %blink_on%off%blink_off% %ANSI_COLOR_NORMAL%
                set DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1=no
        endiff


rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Check if we already have a TXT file in the same folder and shouldn't even be running this:
        iff exist "%PREFERRED_TEXT_FILE_NAME%" then
                @call warning "Lyrics already exist for %emphasis%%audio_file%%deemphasis%"
                @call divider
                @call bigecho %ansi_color_bright_white%%star% %underline_on%Current lyrics%underline_off%:
                echos %ANSI_COLOR_GREEN%
                type "%PREFERRED_TEXT_FILE_NAME%" |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                @call divider

                call AskYn "(1) Do these lyrics %italics_on%we already have%italics_off% look acceptable" %DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1%  %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then                        
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        echo %ansi_color_warning_soft%%star% Not using them, so let's remove them and try downloading...%ansi_color_normal%
                        if exist "%PREFERRED_TEXT_FILE_NAME%" (ren  /q "%PREFERRED_TEXT_FILE_NAME%" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak")
                        goto :End_Of_Check_To_See_If_We_Already_Had_Them
                endiff
        endiff
        :End_Of_Check_To_See_If_We_Already_Had_Them
        if %vebose gt 0 call unimportant ":End_Of_Check_To_See_If_We_Already_Had_Them" 
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Check if we have one in our lyric repository already, via 2 different filenames, and then manual selection:
        call debug "(10) Checking for %MAYBE_LYRICS_1%" 
        iff exist "%MAYBE_LYRICS_1%" then
                @call divider
                @call less_important "Found possible lyrics at %emphasis%%maybe_lyrics_1%%emphasis%!"
                @call less_important "Let's review them:"
                @call divider
                @call bigecho %ANSI_COLOR_IMPORTANT_LESS%Let's review:%ANSI_RESET%
                type "%MAYBE_LYRICS_1%" |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                call divider
                call AskYn "(2) Do these look acceptable" %DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1%  %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%

                iff "%ANSWER%" eq "Y" then
                        *copy "%MAYBE_LYRICS_1%" "%PREFERRED_TEXT_FILE_NAME%" >nul
                        if not exist "%PREFERRED_TEXT_FILE_NAME%" (call error "Well. This shouldn't happen. #9234092340" %+ beep %+ pause %+ call exit-maybe)
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, then..."
                        goto :MaybeLyrics2
                endiff
        endiff

        :MaybeLyrics2
        call debug "(11) Checking for %MAYBE_LYRICS_2%" 
        iff exist "%MAYBE_LYRICS_2%" then
                call less_important "Found possible lyrics at %emphasis%%maybe_lyrics_2%%emphasis%!"
                call less_important "Let's review them:"
                call divider
                type "%MAYBE_LYRICS_2%" |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                call divider
                call AskYn "(3) Do these look acceptable" %DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1%  %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then
                        *copy "%MAYBE_LYRICS_2%" "%PREFERRED_TEXT_FILE_NAME%"
                        goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                else
                        call warning_soft "Not using them, then..."
                        rem not necessary because we simply continue down the script:
                        rem goto :TrySelectingSomethingFromOurLyricsArchive
                endiff
        endiff

rem If we still didn't find anything acceptable, but have potentially matching files in our lyric repository, let us select one manually:
        :TrySelectingSomethingFromOurLyricsArchive
        set TRY_SELECTION_AGAIN=0
        iff exist "%MAYBE_LYRICS_1_BROAD_SEARCH%" .and. %SKIP_MANUAL_SELECTION ne 1 then
                rem call debug "(12) Checking for %MAYBE_LYRICS_1_BROAD_SEARCH%" 
                repeat 3 echo.
                call divider
                set  file_count=%@files["%MAYBE_LYRICS_1_BROAD_SEARCH%"]
                iff %file_count eq 1 then
                        call important_less "Copying file from our %italics_on%LYRIC%italics_off% repository..."
                        *copy /Ns %@expand["%MAYBE_LYRICS_1_BROAD_SEARCH%"] %TMPREVIEWFILE% >nul
                else
                        set tmptitle=%_title
                        call bigecho %ANSI_COLOR_SUCCESS%%STAR% %underline_on%Choose %italics_on%one%italics_off%%underline_off%?:
                        echo         %star%%star%song is %FILE_SONG% by %FILE_ARTIST%
                        dir /b "%MAYBE_LYRICS_1_BROAD_SEARCH%" |:u8 insert-before-each-line.py "        %@REPEAT[%EMOJI_red_QUESTION_MARK,2] "
                        call AskYn "%underline_on%Select%underline_off% from %file_count% of these files, for '%italics_on%%blink_on%%FILE_SONG%%blink_off%%italics_off%' by '%italics_on%%FILE_ARTIST%%italics_off%'" no %LYRIC_SELECT_FROM_FILELIST_WAIT_TIME% 
                        iff "%answer%" eq "N" then
                                call less_important "Skipping selecting from potential files..."
                                goto :End_Of_Local_Lyric_Archive_Selection
                        else
                                set TMPREVIEWFILE=%temp%\review-file.%_datetime.%_PID.txt
                                cls
                                echos %@RANDFG_SOFT[]
                                title %file_song% - %file_artist%
                                select *copy /Ns  ("%MAYBE_LYRICS_1_BROAD_SEARCH%") %TMPREVIEWFILE%
                        endiff
                        title %tmptitle%
                endiff
        endiff

        iff exist %TMPREVIEWFILE% then
                call divider
                call bigecho %ansi_color_bright_white%%star% %underline_on%Selected lyrics%underline_off%:
                echos %ANSI_COLOR_YELLOW%
                type %TMPREVIEWFILE% |:u8 unique-lines -A -L |:u8 insert-before-each-line "        "
                call divider
                call AskYn "(4) Do these lyrics %italics_on%from our lyrics repository%italics_off% look acceptable" %DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1%  %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                iff "%ANSWER%" eq "Y" then
                        *copy /q "%TMPREVIEWFILE%" "%PREFERRED_TEXT_FILE_NAME%" >nul
                        iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                                call error "PREFERRED_TEXT_FILE_NAME of %PREFERRED_TEXT_FILE_NAME% doesn't exist and should"
                        endiff
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
        else
                rem It seems we did not select/copy a file and must move on to the next step
        endiff

        iff "%TRY_SELECTION_AGAIN%" == "1" then
                set TRY_SELECTION_AGAIN=2                               %+ rem Recursion stopgap
                goto :TrySelectingSomethingFromOurLyricsArchive
        endiff
        :End_Of_Local_Lyric_Archive_Selection
rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem Set the values that we will use when using LYRIC_DOWNLOADER_1 the first time [they get changed during subsequent download attempts]:
        set        FILE_SONG_TO_USE=%FILE_SONG%
        set       FILE_TITLE_TO_USE=%FILE_SONG%          
        set      FILE_ARTIST_TO_USE=%FILE_ARTIST%
        set FILE_ORIG_ARTIST_TO_USE=%FILE_ORIG_ARTIST%
        set       FILE_ALBUM_TO_USE=%FILE_ALBUM%

rem Download the lyrics using LYRIC_DOWNLOADER_1: BEGIN: ————————————————————————————————————————————————————————————————————————————————————
        :download_with_lyric_downloader_1
        rem Create a tiny file so we don't accidentally do anything latest-file based with any pre-existing files in the folder,
        rem Because later we are doing things with the latest file, but if a failure happens, the latest file could be something
        rem already in the folder.  To prevent that, *this* will be the latest file:
                 >"__"

        rem Create our command:
                set                               LYRIC_RETRIEVAL_COMMAND=%LYRIC_DOWNLOADER_1% song "%FILE_SONG_TO_USE%" "%FILE_ARTIST_TO_USE%" --save
                rem  %ANSI_COLOR_DEBUG- COMMAND: %LYRIC_RETRIEVAL_COMMAND%%ANSI_COLOR_NORMAL%
                call divider
                echo %ANSI_COLOR_IMPORTANT_LESS%%STAR% Searching %italics_on%%LYRIC_DOWNLOADER_1_SOURCE%%italics_off% for '%italics_on%%FILE_SONG_TO_USE%%italics_off%' by '%italics_on%%FILE_ARTIST_TO_USE%%italics_off%'%ANSI_RESET%

        rem Store original environment variable value for PYTHONIOENCODING:            
                if defined PYTHONIOENCODING (set PYTHONIOENCODING_OLD=%PYTHONIOENCODING%)
                set PYTHONIOENCODING=utf-8

        rem Run our command, with a 'y' answer to overwrite:
                echos %ANSI_COLOR_RUN%
                rem ((echo y | %LYRIC_RETRIEVAL_COMMAND%) |:u8 insert-before-each-line.py "            " |:u8 copy-move-post.py whisper)    %+ rem temporarily disabling this until we get that leak fixed
                ((echo y | %LYRIC_RETRIEVAL_COMMAND%) |:u8 insert-before-each-line.py "            ")
                call errorlevel "Problem retrieving lyrics in %0"

        rem Restore original environment variable value for PYTHONIOENCODING:            
                iff defined PYTHONIOENCODING_OLD then
                        set PYTHONIOENCODING=%PYTHONIOENCODING_OLD%
                else
                        unset /q PYTHONIOENCODING
                endiff

        rem Get the most latest file:
                set LATEST_FILE=%@EXECSTR[dir /b /odt | tail -1]

        rem Generate the proper filename for our freshly-downloaded lyrics, and if it already exists, back it up:
                set PREFERRED_LATEST_FILE_NAME=%@NAME[%AUDIO_FILE].%@EXT[%LATEST_FILE]
                if exist "%PREFERRED_LATEST_FILE_NAME%" (ren /q "%PREFERRED_LATEST_FILE_NAME%" "%PREFERRED_LATEST_FILE_NAME%.%_datetime.bak">nul)

        rem See if our latest file is the expected extension [which would indicate download sucess] or not:
                set  MYSIZEY=%@FILESIZE[%LATEST_FILE]
                iff %MYSIZEY% gt %MOST_BYTES_THAT_LYRICS_COULD_BE% then  
                        rem annoying because this situation ended up not as urgent as originall thought: beep 40 40
                        echos             ``
                        call warning "Caution! Download is %MYSIZEY%b, larger than threshold of %MOST_BYTES_THAT_LYRICS_COULD_BE%b"
                        if 0 lt %LARGE_DOWNLOAD_WARNING_WAIT_TIME (call pause-for-x-seconds %LARGE_DOWNLOAD_WARNING_WAIT_TIME%)
                endiff
                iff "%@EXT[%LATEST_FILE]" == "%LYRIC_DOWNLOADER_1_EXPECTED_EXT%" then
                        echos %ANSI_COLOR_GREEN%
                        *ren /q "%LATEST_FILE%" "%PREFERRED_LATEST_FILE_NAME%" >nul
                else
                        rem (It should be the "__" file if nothing generated)
                        rem call warning "The latest file is not a JSON? It is %LATEST_FILE% .. Does this mean lyrics didn't download?"
                        @echos             ``
                        @call warning "(A) No lyrics downloaded."
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
                call delete-zero-byte-files *.txt silent >nul

        rem At this point, our SONG.txt should exist!  If it doesn't, then we rejected all our downloads.
                iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                        @echos             ``
                        @call warning "(B) No lyrics downloaded."
                        set LYRIC_RETRIEVAL_1_FAILED=1
                else
                        @call divider
                        call bigecho %star% %ansi_color_bright_white%%underline_on%Downloaded lyrics%underline_off%:
                        @echo %ANSI_COLOR_BRIGHT_YELLOW%
                        type "%PREFERRED_TEXT_FILE_NAME%" |:u8 unique-lines -A -L |:u8 insert-before-each-line.py "        "
                        @call divider
                        @call AskYn "%faint_on%(6)%faint_off% Do these %italics_on%downloaded%italics_off% lyrics for '%italics_on%%FILE_song_TO_USE%%italics_off%' by '%italics_on%%FILE_artist_TO_USE%%italics_off%' look acceptable" %DEFAULT_LYRIC_ACCEPTANCE_PROMPT_1%   %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME%
                        iff "%ANSWER%" eq "Y" then
                                rem oops this waqsn't happening and it turns out we don't need it: *del /q "%PREFERRED_TEXT_FILE_NAME%" >nul
                                goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done
                        else
                                rem Continue on but delete the file to indicate its rejection
                                ren  /q "%PREFERRED_TEXT_FILE_NAME%" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak"
                        endiff
                endiff
                :end_of_massage_attempt

                :skip_from_nothing_downloaded


rem Get massaged names for next section's check:
        rem Massage some problematic subsets of these fields:
        rem 1) Remove things in parenthesis
        rem 2) remove "The "
                set      FILE_ARTIST_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_ARTIST%]]
                set FILE_ORIG_ARTIST_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_ORIG_ARTIST%]]
                set       FILE_ALBUM_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_ALBUM%]]
                set        FILE_SONG_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_SONG%]]
                set       FILE_TITLE_MASSAGED=%@ReReplace["\([^\)]*\)",,%@ReReplace[^The ,,%FILE_SONG%]]
                rem call debug "(13) Massaged: %TAB%   artist=%italics_on%%FILE_ARTIST_MASSAGED%=%italics_off%%newline%%TAB%%tab%%tab%%tab%         title=%italics_on%%FILE_SONG_MASSAGED%=%italics_off%%newline%%TAB%%tab%%tab%%tab%         album=%italics_on%%FILE_album_MASSAGED%=%italics_off%"


rem try again if massaged names exist (that is, if the massaged names are different than the original names):        
        rem DEBUG_MASSAGED_FILENAME_CHECK: echo %ANSI_COLOR_DEBUG%- DEBUG: (1) iff 1 ne %LD1_MASSAGED_ATTEMPT_1% .and. ("%FILE_SONG_MASSAGED%" != "%FILE_SONG_TO_USE%" .or. "%FILE_artist_MASSAGED%" != "%FILE_artist_TO_USE%") then %+ call pause-for-x-seconds %paused_debug_wait_time%
        if 1 eq LD1_MASSAGED_ATTEMPT_1 (goto :Already_Did_Massaged)
        iff "1" ne "%LD1_MASSAGED_ATTEMPT_1%" .and. ("%FILE_SONG_MASSAGED%" != "%FILE_SONG%" .or. "%FILE_artist_MASSAGED%" != "%FILE_artist%") then 
                call divider
                echo %ANSI_COLOR_WARNING_SOFT%%STAR% Let's try downloading with the massaged names (%ansi_color_bright_green%%italics_on%%FILE_ARTIST_MASSAGED%%italics_off%%ansi_reset% - %ansi_color_bright_cyan%%italics_on%%FILE_SONG_MASSAGED%%italics_off%%ANSI_COLOR_WARNING_SOFT%)...%ANSI_RESET%
                if 0 lt %WAIT_AFTER_ANNOUNCING_MASSAGED_SEARCH (call pause-for-x-seconds %WAIT_AFTER_ANNOUNCING_MASSAGED_SEARCH%)
                set FILE_SONG_TO_USE=%FILE_SONG_MASSAGED%
                set FILE_ARTIST_TO_USE=%FILE_ARTIST_MASSAGED%
                set LD1_MASSAGED_ATTEMPT_1=1
                rem   %ANSI_COLOR_DEBUG%- DEBUG: (14) set LD1_MASSAGED_ATTEMPT_1 to %LD1_MASSAGED_ATTEMPT_1%
                goto :download_with_lyric_downloader_1
        endiff
        :Already_Did_Massaged
        if exist "%PREFERRED_TEXT_FILE_NAME" (ren /q "%PREFERRED_TEXT_FILE_NAME" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak">nul)
        rem call important_less "These non-exlyrics have been rejected as well"
        call divider
        rem no! goto :end_of_massage_attempt
        rem Continue on... We have failed so far.



rem If we still don't have anything, let us manually edit the song and artist name if we want
        iff exist "%PREFERRED_TEXT_FILE_NAME%" (goto :have_acceptable_lyrics_now_or_at_the_very_least_are_done)

        rem rainbow divider here?
        call AskYN "Want to try hand-editing the artist & song name" no %HAND_EDIT_ARTIST_AND_SONG_AND_LYRICS_PROMPT_WAIT_TIME%
        if "%answer%" == "N" (goto :Skip_Hand_Editing)

        eset FILE_ARTIST
        eset FILE_SONG
        rem  FILE_ALBUM

        set        FILE_SONG_TO_USE=%FILE_SONG%
        set       FILE_TITLE_TO_USE=%FILE_SONG%
        set      FILE_ARTIST_TO_USE=%FILE_ARTIST%
        set FILE_ORIG_ARTIST_TO_USE=%FILE_ORIG_ARTIST%
        set       FILE_ALBUM_TO_USE=%FILE_ALBUM%

        goto :download_with_lyric_downloader_1
        :Skip_Hand_Editing







        :end_of_lyric_downloader_1
rem Download the lyrics using LYRIC_DOWNLOADER_1: END: —————————————————————————————————————————————————————————————————————————————————————



rem Final chance to hand-edit the lyrics if we haven't approved them yet:
        :ask_to_hand_edit_lyrics
        call AskYN "%italics_on%Google%italics_off% for lyrics" no %GOOGLE_FOR_LYRICS_PROMPT_WAIT_TIME%
        iff "%answer%" eq "Y" then
                rem These are current values: google %FILE_ARTIST_TO_USE% %FILE_SONG_TO_USE% lyrics
                rem https://www.google.com/search?q=+Freezepop+Uncanny+Valley+lyrics
                rem https://www.google.com/search?q="Freezepop"+"Uncanny+Valley"+lyrics

                rem TODO: remove (live).*$ from as well!
                set      FILE_ARTIST_ORIGINAL_FOR_GOOGLE=%@ReReplace[ *\(live\).*$,,%@ReReplace[[\+\?&],,%FILE_ARTIST_ORIGINAL%]]
                set FILE_ORIG_ARTIST_ORIGINAL_FOR_GOOGLE=%@ReReplace[ *\(live\).*$,,%@ReReplace[[\+\?&],,%FILE_ORIG_ARTIST_ORIGINAL%]]
                set        FILE_SONG_ORIGINAL_FOR_GOOGLE=%@ReReplace[ *\(live\).*$,,%@ReReplace[[\+\?&],,%FILE_SONG_ORIGINAL%]]
                set       FILE_ALBUM_ORIGINAL_FOR_GOOGLE=%@ReReplace[ *\(live\).*$,,%@ReReplace[[\+\?&],,%FILE_ALBUM_ORIGINAL%]]
                rem These are original values:
                        rem TODO: we might want to do more than 1 search, or an albums search
                        echo %ANSI_COLOR_DEBUG%- DEBUG: (2) google.py "%FILE_ARTIST_ORIGINAL_FOR_GOOGLE%" "%FILE_SONG_ORIGINAL_FOR_GOOGLE%" +lyrics
                                                            google.py "%FILE_ARTIST_ORIGINAL_FOR_GOOGLE%" "%FILE_SONG_ORIGINAL_FOR_GOOGLE%" +lyrics                                                                

                set WE_GOOGLED=1

                rem Increase wait time if we googled:
                        set HAND_EDIT_ARTIST_AND_SONG_AND_LYRICS_PROMPT_WAIT_TIME=%@EVAL[%HAND_EDIT_ARTIST_AND_SONG_AND_LYRICS_PROMPT_WAIT_TIME + %ADDITIONAL_HAND_EDIT_WAIT_TIME_IF_THEY_GOOGLED%]
        else
                set WE_GOOGLED=0
        endiff



:have_acceptable_lyrics_now_or_at_the_very_least_are_done

rem Final change to hand-edit the lyrics, but skip it if we already opted to search Google to save us the hassle:
        if "%WE_GOOGLED%" == "1" .and. "%AUTOMATIC_HAND_EDITING_IF_GOOGLING%" == "1" (goto :reject_hand_editing_question_and_go_straight_to_hand_editing)
        call AskYN "Hand-edit the lyrics" no %HAND_EDIT_ARTIST_AND_SONG_AND_LYRICS_PROMPT_WAIT_TIME%
        :reject_hand_editing_question_and_go_straight_to_hand_editing
        iff "%answer%" eq "Y" .or. ("%WE_GOOGLED%" == "1" .and. "%AUTOMATIC_HAND_EDITING_IF_GOOGLING%" == "1") then
                if not exist "%PREFERRED_TEXT_FILE_NAME%" >"%PREFERRED_TEXT_FILE_NAME%"
                %EDITOR%     "%PREFERRED_TEXT_FILE_NAME%"
                @input /c /w0 %%This_Line_Clears_The_Character_Buffer
                call pause-for-x-seconds %LONGEST_POSSIBLE_HAND_EDIT_TIME_IN_SECONDS% "%ansi_color_bright_yellow%%pencil% Hit a key when done editing lyrics... %faint_on%(leave blank if none found)%faint_off% %pencil% %ansi_color_normal%"
        endiff

rem TODO: Perhaps a prompt to reject the lyrics here {and delete the file}, i needed that in at least 1 case. it would have to default to o

rem Start our cleanup:
        :Cleanup
        rem (moved to very end)

rem Validate we did something:
        if %DEBUG gt 0 echo %ANSI_COLOR_DEBUG%- DEBUG: (30) iff not exist "%PREFERRED_TEXT_FILE_NAME%" 
        iff not exist "%PREFERRED_TEXT_FILE_NAME%" then
                call divider
                rem      call nn "%emoji_warning% %ansi_color_alarm%LYRIC FAIL%ansi_color_normal% %emoji_warning%"
                repeat 3 call bigecho " %emoji_warning% %ansi_color_alarm% LYRIC FAIL %ansi_color_normal% %emoji_warning%"
                call divider
                call warning "Unfortunately, we could not find lyrics for %ANSI_COLOR_BRIGHT_RED%%ITALICS_On%%FILE_ARTIST% - %FILE_SONG%%ITALICS_OFF%" 
                title %emoji_warning% Lyrics not fetched %emoji_warning%
        else
                rem  celebrate "%check% LYRIC SUCCESS %check%" 2
                rem  celebrate "%ansi_background_black% %check%  %@cool[LYRIC SUCCESS] %check% %@randfg[]" 2
                call celebrate "%ansi_background_black% %check% %@cool[LYRIC SUCCESS] %check%  %@randfg[]" 2
                call important_less "Lyrics downloaded: %blink_on%%italics_on%%PREFERRED_TEXT_FILE_NAME%%ANSI_RESET%"
                title %check% Lyrics fetched successfully! %check% 
        endiff



:END
:SetVarsOnly_skip_to_2
:The_VERY_End

if exist "__" (*del /q "__">nul)
unset /q WE_GOOGLED
unset /q LYRIC_RETRIEVAL_1_FAILED
unset /q LD1_MASSAGED_ATTEMPT_1
unset /q TRY_SELECTION_AGAIN

