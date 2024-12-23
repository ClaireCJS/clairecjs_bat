@Echo off
 on break cancel

:USAGE: set UNATTENDED_YOUTUBE_DOWNLOADS=1   to skip the RN part


set DEBUG=0
set OUR_LOGGING_LEVEL=None
call set-cursor




REM     2022 removing but maybe this should just be a DEMONA thing: setdos /X-56789A



	::::: WHICH DOWNLOADER TO USE:
		:set YDL=youtube-dl
		set YDL=yt-dlp


    ::::: PARAMETERS:
        REM set OUTPUTNAME=%1
        if %@COUNT[%@char[34],%1] ne 2 (call error "first argument must have quotes around it")
        SET URL=%@UNQUOTE[%1]
        SET ALL="%*"
        set NOEXT=0 
        set YOUTUBE_MODE=1 
        call print-if-debug "URL is “%URL%”"
        


        REM this can never happen if "" eq "%1" .and. "" ne "%1" (set URL=%*    %+ unset /q OUTPUTNAME)
        REM this seemed wrong     if "" eq "%2" .or.  "" eq "%1" (call FATAL_ERROR "NEED FILENAME AND URL PARAMETERS!" %+ goto :END)
        if "%2" eq "NOEXT" (set NOEXT=1) 

    ::::: EXECUTION:
        call validate-in-path %YDL %
        :call dl                                                                                          %+ REM moves us to the folder we typically download youtube videos into
        set TMPDIR=oh.%_DATETIME.%_PID
        REM REDOCOMMAND=call %YDL%     -o "%@UNQUOTE[%OUTPUTNAME%]"     "%URL%"
        set REDOCOMMAND=call %YDL%                                      "%URL%"
        *md %TMPDIR%
        if not exist %TMPDIR% (call warning "tmpdir “%TMPDIR%” doesn’t seem to exist" %+ pause %+ pause %+ pause %+ pause)
        *cd %TMPDIR%

        :: how to stop unicode b.s. characters though?  
        :: --no-restrict-filenames - allow unicode characters, &, and spaces ---
        :: --windows-filenames doesn’t stop them
        :: --restrict-filenames stops too much, makes every space a nunderscore, etc
        :: -o without any other options - "yt-dlp.exe: err;or: you must provide at least one URL"
        :: --replace-in-metadata '“:'':”:'':‘:' <video-url>
        :: someone says --compat-options filename-sanitization
        :: Alternatively you can use --compat-options filename-sanitization to mimic youtube-dl’s behavior which doesn’t do this
        
        ::: OKAY HERE IS THE SOLUTION! But also add each newly fixed item to allfileunicode.pl too!
        :: yt-dlp --replace-in-metadata '“:":”:":‘:' <video-url>


        :call %YDL% --no-check-certificate                    "%URL%"
        :call %YDL% --write-description --windows-filenames   "%URL%"
        :call %YDL% --write-description --windows-filenames   "%URL%"
        %COLOR_RUN%
     REM BACKUP 20230526 WHILE BUGESTING:
     REM call %YDL% -vU --verbose --write-description --compat-options filename-sanitization -f bestaudio --audio-quality best --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
     REM call %YDL% -vU --verbose --write-description                                                                                           --add-metadata --embed-metadata                                --sub-langs en "%URL%"
        @echo on
         call %YDL% -vU --verbose --write-description --compat-options filename-sanitization                                   --embed-chapters --add-metadata --embed-metadata --embed-subs --embed-info-json --sub-langs en "%URL%"
        @Echo off
         rem we don’t call errorlevel because %YDL% returns an errorlevel even when successful
         REM removed --embed-thumbnail: messes up workflow this that extra file: PLUS it made: ERROR: Postprocessing: Supported filetypes for thumbnail embedding are: mp3, mkv/mka, ogg/opus/flac, m4a/mp4/mov 





    ::::: VALIDATION:
        REM we don’t track output names anymore....: if defined OUTPUTNAME if not exist %OUTPUTNAME% (call WARNING "Output file does not exist: “%OUTPUTNAME%”")
        

:END


:2022 removing but maybe this should just be a DEMONA thing: setdos /X0

::::: CLEANUP:
    :: fix filenames
        REM this can be run in unattended mode, but we’re not ready for that yet:
        call fix-unicode-filenames       
        call errorlevel

    :: manual rename opportunity - also covers companion files
        if "%UNATTENDED_YOUTUBE_DOWNLOADS%" eq "1" goto :Unattended
            call rn-latest-for-youtube-dl %FILEMASK_VIDEO%
            :^^^^^^^^^^^^^^^^^^^^^^^^^^^^ side-effect: sets %FILENAME_NEW%, which we use later  ...TODO:possible bug in that it tries to rename the JSON now. same effcet but more confusing
            call errorlevel
        :Unattended

    :: get json file - do this *AFTER* we do our renaming so that we can use our post-rename filename for the JSON file
        echos %ANSI_COLOR_IMPORTANT_LESS%%STAR% Fetching json description...
            set JSON_WANTED=%@NAME[%FILENAME_NEW%].json
            call %YDL% --dump-json "%URL%" >"%JSON_WANTED%"
            call validate-environment-variable JSON_WANTED
        call success "Succcess!"

    :: clean-up 0-byte description txt file
        for %%tmpZeroByteFile in (*.txt;*.description) do (
            if %%~zf==0 (
                echo. 
                rem  warning "Deleting %italics_on%zero-byte              file:             %%tmpZeroByteFile ????"
                call warning "Deleting %italics_on%zero-byte%italics_off% file: “%italics_on%%tmpZeroByteFile%%italics_off%” ????"

                %COLOR_REMOVAL% %+ echo. %+ del /p "%%tmpZeroByteFile"
            )
        )

    :: multiple-file downloads is janky and .description files don’t all get turned into .txt correctly
        if exist *.description (ren *.description *.txt)

    :: move files back into original folder we started in
        :dangerous: mv * ..
        cd ..
        if isdir %TMPDIR% (%COLOR_SUBTLE% %+ mv/ds %TMPDIR% .)
        if isdir %TMPDIR% (call ERROR "Couldn’t remove “%TMPDIR%”! Are you sure you aren’t in this folder in another window?")

unset /q YOUTUBE_MODE
title Completed: youtube download
call set-cursor
