@Echo off
@loadbtm on
@on break cancel

rem ║═════════════════════════════════════════════════════════════════════║ 
rem ║                                                                     ║
rem ║ WHAT DOES THIS DO DIFFERENTLY FROM CALLING ytp-dl / ydl DIRECTLY??? ║
rem ║                                                                     ║
rem ║     External unicode/emoji filename scrubber run                    ║
rem ║     Chance to interactively rename file when done                   ║
rem ║     Description/caption of video saved as sidecar txt               ║
rem ║     Subtitles, Metadata, Chapsters, English Subtitles embedded      ║
rem ║     JSON metadata saved                                             ║
rem ║     Zero-byte files deleted                                         ║
rem ║                                                                     ║
rem ║═════════════════════════════════════════════════════════════════════║ 

:USAGE: set UNATTENDED_YOUTUBE_DOWNLOADS=1   to skip the RN part


set DEBUG=0
set OUR_LOGGING_LEVEL=None




REM     2022 removing but maybe this should just be a DEMONA thing: setdos /X-56789A



rem CONFIG: WHICH DOWNLOADER TO USE:
        rem YDL=youtube-dl —— stopped being developed / as good, replaced by “yt-dlp”
        set YDL=yt-dlp

rem Validate environment:
        iff "1" != "%validated_ydl_bat%" then
                call validate-in-path               %YDL% set-cursor print-if-debug  rn-latest-for-youtube-dl errorlevel fix-unicode-filenames error print-message warning success rn title divider rn pause-for-x-seconds
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET check
                set  validated_ydl_bat=1
        endiff

rem INIT:
        call set-cursor

rem PROCESS PARAMETERS:
        REM set OUTPUTNAME=%1
        if %@COUNT[%@char[34],%1] ne 2 (call error "first argument must have quotes around it")
        SET URL=%@UNQUOTE[%1]
        SET ALL="%*"
        set NOEXT=0 
        set YOUTUBE_MODE=1 
        call print-if-debug "URL is “%URL%”"
        
        REM this can never happen if "" == "%1" .and. "" != "%1" (set URL=%*    %+ unset /q OUTPUTNAME)
        REM this seemed wrong     if "" == "%2" .or.  "" == "%1" (call FATAL_ERROR "NEED FILENAME AND URL PARAMETERS!" %+ goto :END)
        if "%2" == "NOEXT" (set NOEXT=1) 


rem EXECUTION:
        rem call dl                                                                                          %+ REM moves us to the folder we typically download youtube videos into
        set TMPDIR=oh.%_DATETIME.%_PID
        REM REDOCOMMAND=call %YDL%     -o "%@UNQUOTE[%OUTPUTNAME%]"     "%URL%"
        set REDOCOMMAND=call %YDL%                                      "%URL%"
        *md %TMPDIR%
        if not exist %TMPDIR% (call warning "tmpdir “%TMPDIR%” doesn’t seem to exist" %+ pause %+ pause %+ pause %+ pause %+ goto :No_Temp_Dir)
                *cd %TMPDIR%
        :No_Temp_Dir

        rem :: how to stop unicode b.s. characters though?  
        rem :: --no-restrict-filenames - allow unicode characters, &, and spaces ---
        rem :: --windows-filenames doesn’t stop them
        rem :: --restrict-filenames stops too much, makes every space a nunderscore, etc
        rem :: -o without any other options - "yt-dlp.exe: err;or: you must provide at least one URL"
        rem :: --replace-in-metadata '“:'':”:'':‘:' <video-url>
        rem :: someone says --compat-options filename-sanitization
        rem :: Alternatively you can use --compat-options filename-sanitization to mimic youtube-dl’s behavior which doesn’t do this
        
        rem ::: OKAY HERE IS THE SOLUTION! But also add each newly fixed item to allfileunicode.pl too!
        rem :: yt-dlp --replace-in-metadata '“:":”:":‘:' <video-url>

        rem :call %YDL% --no-check-certificate                    "%URL%"
        rem :call %YDL% --write-description --windows-filenames   "%URL%"
        rem :call %YDL% --write-description --windows-filenames   "%URL%"
        %COLOR_RUN%
        rem ━━ BACKUP 20230526 WHILE BUGESTING: ━━
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization -f bestaudio --audio-quality best --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description                                                                                           --add-metadata --embed-metadata                                --sub-langs en "%URL%"
        rem @echo on
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies c:\cookies.txt         --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies-from-browser opera     --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies-from-browser edge      --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies-from-browser chrome    --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies-from-browser firefox   --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization                                   --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies-from-browser firefox   --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"

        rem Good:
            rem call %YDL% -vU --verbose --write-description --compat-options filename-sanitization  --cookies-from-browser firefox   --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en --write-thumbnail --embed-thumbnail "%URL%"
        
        rem Testing:
            call %YDL% -vU --verbose --write-description --compat-options filename-sanitization                                   --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en --write-thumbnail --embed-thumbnail "%URL%"
        @Echo off
        title YouTube D/L complete!                                                                                                
        rem was suggested that one could scrub unicode chars with this command: --replace-in-metadata "video:title" " ?[\U000002AF-\U0010ffff]+" ""
        rem we don’t call errorlevel because %YDL% returns an errorlevel even when successful
        rem removed --embed-thumbnail: messes up workflow this that extra file: PLUS it made: ERROR: Postprocessing: Supported filetypes for thumbnail embedding are: mp3, mkv/mka, ogg/opus/flac, m4a/mp4/mov 





rem VALIDATION:
        REM we don’t track output names anymore....: if defined OUTPUTNAME if not exist %OUTPUTNAME% (call WARNING "Output file does not exist: “%OUTPUTNAME%”")
        

:END


:2022 removing but maybe this should just be a DEMONA thing: setdos /X0

rem CLEANUP:
        if exist *.description (ren *.description *.txt)
        if "%UNATTENDED_YOUTUBE_DOWNLOADS%" == "1" goto :Unattended
                call set-latest-filename *.txt
                call debug "LATEST_FILENAME is “%LATEST_FILENAME%”" %+ call pause-for-x-seconds 5
                if not defined LATEST_FILENAME goto :no_latest_filename
                        call divider
                        type "%LATEST_FILENAME%"
                        echo.
                        call divider        
                :no_latest_filename
                call rn-latest-for-youtube-dl %FILEMASK_VIDEO%
                :^^^^^^^^^^^^^^^^^^^^^^^^^^^^ side-effect: sets %FILENAME_NEW%, which we use later  ...TODO:possible bug in that it tries to rename the JSON now. same effcet but more confusing
                call errorlevel "problem with rn-latest-for-youtube-dl"
        :Unattended



    rem fix filenames
        REM this can be run in unattended mode, but we’re not ready for that yet:
        call fix-unicode-filenames no_trace
        if exist fix-unicode-filenames.log *del fix-unicode-filenames.log
        call errorlevel "problem with fix-unicode-filenames"

    rem get json file - do this *AFTER* we do our renaming so that we can use our post-rename filename for the JSON file
        echos %ANSI_COLOR_IMPORTANT_LESS%%STAR% Fetching json description...
        set JSON_WANTED=%@NAME[%FILENAME_NEW%].json
        call %YDL% --dump-json "%URL%" >"%JSON_WANTED%"
        if not exist "%JSON_WANTED%" call validate-environment-variable JSON_WANTED "can’t find JSON_WANTED file of “%JSON_WANTED%”"
        call success "Succcess!"

    rem rn again?
        rem seemed to cause our mkv to not get renamed when we stared to do this....
        rem not sure if we need to switch this: call rn "%FILENAME_NEW%"
        rem to this:
        REM maybe not actually:
        rem call rn-latest-for-youtube-dl %FILEMASK_VIDEO%

    rem clean-up 0-byte description txt file
        for %%tmpZeroByteFile in (*.txt;*.description) do (
            if %%~zf==0 (
                echo. 
                rem  warning "Deleting %italics_on%zero-byte              file:             %%tmpZeroByteFile ????"
                call warning "Deleting %italics_on%zero-byte%italics_off% file: “%italics_on%%tmpZeroByteFile%%italics_off%” ????"

                %COLOR_REMOVAL% %+ echo. %+ del /p "%%tmpZeroByteFile"
            )
        )

    rem multiple-file downloads is janky and .description files don’t all get turned into .txt correctly
        if exist *.description (ren *.description *.txt)

    rem move files back into original folder we started in
        :dangerous: mv * ..
        *cd ..
        if isdir %TMPDIR% (%COLOR_SUBTLE% %+ mv/ds %TMPDIR% .)
        if isdir %TMPDIR% (call ERROR "Couldn’t remove “%TMPDIR%”! Are you sure you aren’t in this folder in another window?")

unset /q YOUTUBE_MODE
title %CHECK% Completed youtube download!
call set-cursor
