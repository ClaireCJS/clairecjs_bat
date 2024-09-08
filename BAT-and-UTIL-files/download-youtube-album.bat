@Echo OFF



:PUBLISH:
:DESCRIPTION:  Download a "youtube album" (album posted as a youtube video) to separate mp3s (per chapter in the youtube video, if there are any), tagged, renamed, ReplayGain'ed, and moved to proper folder structure.  It can also do single songs, but that wasn't its original purpose.
:USAGE:        download-youtube-video-as-mp3-album https://www.youtube.com/watch?v=6w8dVVf6UnY
:USAGE:        download-youtube-video-as-mp3-album ingest         - re-run starting at the the python ingest script
:USAGE:        download-youtube-video-as-mp3-album after_ingest   - re-run starting AFTER  the python ingest script
:USAGE:        download-youtube-video-as-mp3-album ReplayGain     - re-run starting at the embeding of replaygain tags
:USAGE:        download-youtube-video-as-mp3-album rename         - re-run starting at renaming the downloaded file
:USAGE:        download-youtube-video-as-mp3-album img            - re-run starting at fixing the cover image
:USAGE:        download-youtube-video-as-mp3-album embed          - re-embed the current cover image
:REQUIRES:     metaflac.exe (to add ReplayGain tags to FLAC files), metaflac.mp3 (to add ReplayGain tags to MP3 files), yt-dlp.exe (to download YouTube videos), our messaging system & validator scripts
:DEPENDENCIES: set-latestfilename.bat (to determine latest/youngest file), delete-largest-file.bat (to delete full-album after splitting into chapters), set-task (but only to set the TASK and window title)


REM DEBUGGY stuff
        set URL="%*"
        :eset URL
        echo. %+ echo.
        call print-if-debug "URL is:         %URL%"
        call print-if-debug "Parameters are: %*"
        call set-task "downloading youtube albums"

REM check parameters & environment
        if "%1"    eq "" .or. "%URL%" eq "" (call error "Need URL!" %+ goto :END)
        call validate-in-path               ingest_youtube_album.py delete-zero-byte-files important important_less errorlevel delete-largest-file warning error print-if-debug set-task metamp3 metaflac yt-dlp set-latest-filename openimage get-image-dimensions askyn crop-center-square-of-image make-image-square celebration change-into-temp-folder expand-image-to-square
        call validate-environment-variables ANSI_BRIGHT_CYAN faint_on faint_off italics_on italics_off underline_on underline_off filemask_image filemask_audio %+ REM most of these are set by set-colors.bat:


REM Extensions that we may be downloading:
        set EXTENSIONS_WE_ARE_POSSIBLY_DOWNLOADING=*.opus;*.webm;*.mp3;*.flac
        pushd 


REM secret command line options
        if "%1" eq "already"                          (goto :Already_Downloaded)
        if "%1" eq        "ingest"                    (goto :befor_ingest      )
        if "%1" eq  "befor_ingest"                    (goto :befor_ingest      )
        if "%1" eq "before_ingest"                    (goto :befor_ingest      )
        if "%1" eq "before"   .and. "%2" eq "ingest"  (goto :befor_ingest      )
        if "%1" eq "after"    .and. "%2" eq "ingest"  (goto :after_ingest      )
        if "%1" eq "after_ingest"                     (goto :after_ingest      )
        if "%1" eq "replaygain"                       (goto :after_ingest      )
        if "%1" eq "rename"                           (goto :rename_files      )
        if "%1" eq "rename_files"                     (goto :rename_files      )
        if "%1" eq "rename"   .and. "%2" eq   "files" (goto :rename_files      )
        if "%1" eq "fix_image" .or. "%1" eq "fix_img" (goto :fix_image         )
        if "%1" eq  "fiximage" .or. "%1" eq  "fiximg" (goto :fix_image         )
        if "%1" eq     "image" .or. "%1" eq     "img" (goto :fix_image         )
        if "%1" eq     "embed" .or. "%1" eq "reembed" (set image_was_changed=1 %+ goto :embed_again)
       :if "%1" != ""                                 (goto :%1                )                     %+ REM goto a specific label

REM Ask where to place our downloads...
        pushd 
        set            NAME_OF_FOLDER_TO_PUT_THIS_DOWNLOAD_IN=.
        REM eset       NAME_OF_FOLDER_TO_PUT_THIS_DOWNLOAD_IN
        if not isdir "%NAME_OF_FOLDER_TO_PUT_THIS_DOWNLOAD_IN%" (md "%NAME_OF_FOLDER_TO_PUT_THIS_DOWNLOAD_IN%")
        if not isdir "%NAME_OF_FOLDER_TO_PUT_THIS_DOWNLOAD_IN%" (call error "wtf couldn't make dir" %+ goto :END)
        cd           "%NAME_OF_FOLDER_TO_PUT_THIS_DOWNLOAD_IN%" 







REM do everything in a temp folder!
        call change-into-temp-folder youtube-music-download










    REM ***************** Download each chapter as a separate file in the best audio format and write thumbnail ***************** 

    REM -o '%(id)s.%(ext)s' To save as the video title change to '%(title)s.%(ext)s' to save. 
    REM For a custom filename songname.%(ext)s.

    REM would like these i think --compat-options embed-metadata 
    call warning "About to download a youtube video of a song, or chapter-separated album, to mp3 format!"
    call warning "yt-dlp %italics_on%%URL%%italics_off% (with extra steps)"  %+ pause %+ %COLOR_RUN% 
    %COLOR_RUN%
    @echo on
    yt-dlp --verbose --write-info-json --write-description --extractor-args   "youtube:player_client=android" --split-chapters %URL% -f bestaudio --extract-audio --audio-format mp3 --audio-quality 0 --embed-metadata   --write-thumbnail  --embed-thumbnail 
    @echo off

    REM -o "%%(album_artist,artist,creator,uploader|)s/%%(release_year,release_date,upload_date|)s%%(release_year,release_date,upload_date& - |)s%%(album,title|)s/%%{id&FULL ALBUM|}s%%{title|}s
    REM GOLD: "%%(album_artist,artist,creator,uploader|)s/%%(release_year,release_date,upload_date|)s%%(release_year,release_date,upload_date& - |)s%%(album,title|)s"

    REM template won't affect chapters, may as well make it "full album"
    REM --parse-metadata "album:goat"
    rem --postprocessor-args "-metadata album='%%(title)s'" definitely set it! to the string %(title)s haha
    rem --postprocessor-args "-metadata album=%(title)s"  did not work with 1-4,8 slashes - and isn't even supported (chatgpt hallucination)
    REM --replace-in-metadata FIELDS REGEX REPLACE
    rem one % = "0s" two % = "%(title)s"  three % = "0s" four % = 0s eight %=
    REM bad for chapter splitting, no way to get chapter number or title -o "chapter:%%(autonumber)s_%%(title)s.%%(ext)s"  
    REM yt-dlp -x --audio-format mp3 " "https://www.youtube.com/watch?v=..."


    REM -O  %(name[.keys][addition][>strf][,alternate][&replacement][|default])[flags][width][.precision][length]type

            REM default: %(title)s-%(id)s.%(ext)s
            REM wanted!: %(album_artist|uploader)s/%(release_year|release_date)s - %(title)s/%(chapter_number)s_%(chapter)s

    REM # Prefix playlist index with " - " separator, but only if it is available
    REM $ yt-dlp -o '%(playlist_index|)s%(playlist_index& - |)s%(title)s.%(ext)s' BaW_jenozKc "https://www.youtube.com/user/TheLinuxFoundation/playlists"

    REM (chapters&has chapters|no chapters)s, %(title&TITLE={:>20}|NO TITLE)s
    REM --parse-metadata "description:Artist: (?P<artist>.*?)\nAlbum: (?P<album>.*)"
    REM try in a minute --parse-metadata "title:%(artist)s - %(album)s
    REM removed: --embed-info-json             only for video files
    REM removed: --embed-subs --sub-langs en   [EmbedSubtitle] Subtitles can only be embedded in mp4, mov, m4a, webm, mkv, mka files



    REM        :: %(title)s: The video title.
    REM        :: %(id)s: The video identifier.
    REM        :: %(uploader)s: The uploader's name.
    REM        :: %(uploader_id)s: The uploader's identifier.
    REM        :: %(uploader_url)s: The URL to the uploader's YouTube channel.
    REM        :: %(channel)s: The full name of the channel.
    REM        :: %(channel_id)s: The channel identifier.
    REM        :: %(upload_date)s: The date when the video was uploaded in the format YYYYMMDD.
    REM        :: %(extractor)s: The extractor key (youtube, vimeo, etc.)
    REM        :: %(playlist)s: The playlist title.
    REM        :: %(playlist_id)s: The playlist identifier.
    REM        :: %(playlist_index)s: The index of the video in the playlist padded with zeros.
    REM        :: %(age_limit)s: The age restriction of the video (usually 0 or 18).
    REM        :: %(autonumber)s: An automatically incremented number that is unique for every video (starts at 00000).
    REM        :: %(epoch)s: Unix timestamp when creating the file.
    REM        :: %(duration)s: Length of the video in seconds.
    REM        :: %(format)s: A human-readable description of the format.
    REM        :: %(format_id)s: The unique id of the format.
    REM        :: %(view_count)s: The number of views of the video.
    REM        :: %(like_count)s: Number of likes.
    REM        :: %(dislike_count)s: Number of dislikes.
    REM        :: %(average_rating)s: Average rating (likes vs dislikes).
    REM        :: %(comment_count)s: Number of comments.
    REM        :: %(category)s: Category or genre of the video.
    REM        :: %(ext)s: The file extension.
    REM        :: %(filesize)s: The file size.
    REM        :: %(format)s: The name of the format.
    REM        :: %(height)s and %(width)s: The resolution of the video.
    REM        :: %(resolution)s: The video resolution.
    REM        :: %(fps)s: The frame rate.


REM Let's capture the filename as it is after downloading, to remind us later
        call set-latest-filename %EXTENSIONS_WE_ARE_POSSIBLY_DOWNLOADING%
        set FILENAME_AFTER_DOWNLOADING=%latestFilename%



REM Chapters are split, so we can delete the unsplit, which will be the largest file
        set NUM_DOWNLOADED=%@FILES[%EXTENSIONS_WE_ARE_POSSIBLY_DOWNLOADING]
        if %NUM_DOWNLOADED% GT 1 (call delete-largest-file)


REM rename files to the filenames we like
        :rename_files
        set TEXT_INFO=README.txt
        set JSON_INFO=info.json
        echo. %+ echo. %+ echo. %+ echo. 
        call important_less "%EMOJI_CHECK_BOX_WITH_CHECK%Successfully downloaded %NUM_DOWNLOADED% files matching extensions '%EXTENSIONS_WE_ARE_POSSIBLY_DOWNLOADING%'"
        if %NUM_DOWNLOADED% GT 1 (
            set DOWNLOADS=many
            if exist *.description (ren *.description    %TEXT_INFO%)           %+ REM typically README.txt
            if exist *.json        (ren *.json           %JSON_INFO%)           %+ REM typically info.json
            for %%G in (%filemask_image%) do (if exist "*%%G" set COVER_ART=cover.%@LOWER[%@EXT[%%G]] %+ %COLOR_RUN %+ ren "%%G" "%COVER_ART%" %+ %COLOR_IMPORTANT %+ call less_important "%EMOJI_ARTIST_PALETTE%Cover art renamed to '%COVER_ART%'" )
            call validate-environment-variables TEXT_INFO JSON_INFO COVER_ART
        )
        if %NUM_DOWNLOADED% EQ 1 (
            set DOWNLOADS=one
            call set-latestfilename %EXTENSIONS_WE_ARE_POSSIBLY_DOWNLOADING%
            set LATESTFILENAME_BASE=%@NAME[%LATEST_FILENAME]
            call unimportant "%EMOJI_STOPWATCH%Latest filename is: %LATESTFILENAME_BASE%"
            %COLOR_SUCCESS% 
            if exist *.description (ren *.description "%LATESTFILENAME_BASE%.txt" )
            if exist *.json        (ren *.json        "%LATESTFILENAME_BASE%.json")
            REM %file in (%FILEMASK_IMAGE%) do echo if exist "%file%" ren "%file%" "%LATESTFILENAME_BASE%.%@EXT[%FILE]"
            echos %FAINT_ON%
            for %file in (%FILEMASK_IMAGE%) do      if exist "%file%" (echos %FAINT_ON% %+ ren "%file%" "%LATESTFILENAME_BASE%.%@EXT[%FILE]")
            echos %FAINT_OFF%
        )





REM Fix cover image - before running the ingest script that may move it elsewhere and make future changes a bit more confusing
REM                 \-- it may need cropping of just-the-center-square (720x720 square image  centered across a 1280x720 canvas with black sidebars)
REM                 \-- it may need resized  in order to become square (720x720 square image stretched across a 1280x720 canvas)
        :fix_image

        REM get image name
            call   set-latest-filename %filemask_image%
            set image=%latest_filename%

        REM let user know what's going on
            echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. 
            call bigecho %EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%
            set NEWLINE_REPLACEMENT=1
            call warning_soft "About to open image - %italics_on%Remember%italics_off%: our goal is to make it %underline_on%%italics_on%square%italics_off%%underline_off% for album cover embedding\nBut first, just take a look at the image"
            call bigecho %EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%%EMOJI_STOP_SIGN%
            call unimportant "Image filename = '%italics%%image%%italics_off%', CWP='%italics%%_CWP%%italics_off%'"
            pause %+ REM this pause is important to keep buffered keystrokes from answering the next questions

        REM display image
            call openimage "%image%"

        REM prompt/correct image
            set action_taken=
            set image_was_changed=0
            set         Q1="Does this need to be %EMOJI_LEFT_RIGHT_ARROW%%EMOJI_UP_DOWN_ARROW% %italics%%underline%expanded%italics_off%%underline_off% %EMOJI_LEFT_RIGHT_ARROW%%EMOJI_UP_DOWN_ARROW% to square? (i.e. what we have is a rectangle, so add black boxes at the top & bottom to make it square)?"
            set         Q2="Does this need to be %EMOJI_SCISSORS% %italics%%underline%cropped%italics_off%%underline_off% %EMOJI_SCISSORS% to square? (i.e. crop out %faint%[black?]%faint_off% boxes on sides)"
            set         Q3="Does this need to be %EMOJI_RIGHT_ARROW%%EMOJI_LEFT_ARROW% %italics%%underline%squished%italics_off%%underline_off% %EMOJI_RIGHT_ARROW%%EMOJI_LEFT_ARROW% to square? (i.e. what we have is obviously a square incorrectly stretched out to rectangle)" 
            call askyn %Q1% yes 0 %+ if %do_it eq 1 (set image_was_changed=1 %+ call expand-image-to-square      "%image%" %+ goto :done_with_questions)
            call askyn %Q2% yes 0 %+ if %do_it eq 1 (set image_was_changed=1 %+ call crop-center-square-of-image "%image%" %+ goto :done_with_questions)
            call askyn %Q3% no  0 %+ if %do_it eq 1 (set image_was_changed=1 %+ call make-image-square           "%image%" %+ goto :done_with_questions)
            :done_with_questions

            :embed_again
            if %image_was_changed eq 1 (
                if %auto_embed ne 1    (call openimage  "%image%")
                if not exist "%image%" (call error       "image of '%image%' doesn't exist")
                call askyn "Are we satisfied with the new image?" yes 0
                if %DO_IT eq 0 (call warning "Returning to command line..." %+ call advice "Run '%0 img' to return to this point" %+ cancel)
                set DONT_DELETE_ART_AFTER_EMBEDDING=1

                call important "%EMOJI_INPUT_NUMBERS%Embedding..."
                for %song in (%filemask_audio%) (
                    call randfg
                    echos .
                    call add-art-to-song "%IMAGE%" "%song%" 
                )

            )

        :done_fixing_image




REM Tag and move the files with our assistant python script:
        set AUTOMATIC_UNICODE_CLEANING=1 %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ REM \_____the environment variable didn't seem to work 
        :Redo_fuf
        echo. %+ echo. %+ echo. 
        call important "%EMOJI_HAMMER% About to run %italics_on%fix-unicode-filenames%italics_off% %faint_on%(to cleanse files of any unicode/bad characters)%faint_off%..."
        call fix-unicode-filenames auto  %+ call errorlevel "uh oh spaghettios!!!!!!" %+ echo. %+ REM /     so we used the "auto" parameter instead
        if %REDO eq 1 goto :Redo_fuf
        set AUTOMATIC_UNICODE_CLEANING=0 %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. 
        call important "%EMOJI_HAMMER_AND_PICK% About to run youtube-album ingest script (%italics_on%ingest_youtube_album.py%italics_off%)..."
        :ingest
        :befor_ingest
        :before_ingest
        REM tag our files, move them into a properly-named folder, fix their filenames
            ingest_youtube_album.py
            call errorlevel "youtube ingest failed in folder %_CWD [called by %0]"
            if %redo eq 1 goto :ingest
        :after_ingest


REM Add replaygain tags
        echo.
        echo.
        call warning "%EMOJI_HAMMER% About to add %italics_on%ReplayGain%italics_off% tags in: %faint%%italics%%_CWP%%italics_off%%faint_off%"
        REM pause
        :add_replaygain_tags
        pushd 
            REM ingest-youtube-album.py creates go-to-album.bat as a return value to change into the folder it created to moves the album into   
            if "%DOWNLOADS%" eq "many" (
                set                                INGEST_RETURN_SCRIPT=go-to-album.bat
                call validate-environment-variable INGEST_RETURN_SCRIPT "ingest return script not found in %0"
                call                              %INGEST_RETURN_SCRIPT%
            )               
            echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo.          
            REM call warning "About to add replaygain tags in %_CWP" 
            call pause-if-debug "force" 
            call add-ReplayGain-tags  
            call errorlevel "replaygain tag add problem in %0 line 276ish"
        popd  
        if exist go-to-album.bat (*del go-to-album.bat)             %+ REM now that we've used it, we don't need it  [TODO maybe change to *del]
        *del /q _ingest.log >nul                                    %+ REM ingest log is actually copied into our target folder but a copy remains here, which we do not want
        call fix-unicode-filenames.bat delete_log                   %+ REM ingest can also create a fix_unicode_filenames.log file if filenames end up getting scrubbed


REM Allow us to manually adjust the filename 
        echos %FAINT_ON%
        call delete-zero-byte-files
        echos %FAINT_OFF%
        echo. %+ echo. %+ echo. %+ echo. %+ echo. 
        call set-latest-filename
        echo.
        echo.
        echo.
        echo %ANSI_COLOR_IMPORTANT%EMOJI_FILE_FOLDER% Original filename was: %FAINT_ON%%ITALICS_ON%%FILENAME_AFTER_DOWNLOADING%%FAINT_OFF%%ITALICS_OFF%
        echo.
        call important "Fix your filename here %faint_on%(if you need to)%faint_off%:"
        echo.
        call rn "%latest_file%"










REM Change out of temp folder and move things back to where we started
        cd ..
        call validate-env-var TEMP_FOLDER WHERE_WE_STARTED
        echo. %+ echo. %+ echo. 
        %COLOR_IMPORTANT_LESS% %+ echo * Current folder = %EMOJI_OPEN_FILE_FOLDER% %_CWD %EMOJI_OPEN_FILE_FOLDER% %+ echo. 
        %COLOR_WARNING%        %+ echos %EMOJI_WARNING% About to move everything out of our TEMP_FOLDER:``
        %COLOR_WARNING_SOFT%   %+ echos  %overstrike%%TEMP_FOLDER%%overstrike_off% ``
        %COLOR_NORMAL%         %+ echo. 
        %COLOR_NORMAL%         %+ echos   ``
        %COLOR_WARNING%        %+ echos  and back to:``
        %COLOR_NORMAL%         %+ echos                                      ``
        %COLOR_WARNING_SOFT%   %+ echos %italics%%WHERE_WE_STARTED%%italics_off%
        %COLOR_NORMAL%         %+ echo.
                                  pause
                                  set MOVE_DECORATOR=%ANSI_COLOR_SUCCESS%%FAINT_ON%%ITALICS%%@ANSI_RGB_BG[0,32,0]
        %COLOR_SUCCESS%        %+ mv /ds "%TEMP_FOLDER%" .




:END
        echo. %+ echo. %+ echo. 
        call celebration "%EMOJI_CHECK_MARK%Download complete!!!%EMOJI_CHECK_MARK%"
        REM  celebration.bat->print-message.bat does titles automatically now so we don't need to do this anymore: title Completed:  Youtube album download
        popd
        dir


