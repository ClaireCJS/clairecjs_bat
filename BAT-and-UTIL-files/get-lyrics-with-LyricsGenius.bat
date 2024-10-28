@Echo Off


rem CONFIG:
        set PROBER=ffprobe.exe
        set LYRIC_DOWNLOADER=lyricsgenius.exe


rem VALIDATE ENVIRONMENT:
        call validate-in-path %LYRIC_DOWNLOADER% %PROBER% tail get-lyrics-with-lyricsgenius-json-processor.pl delete-zero-byte-files unimportant
        call validate-environment-variables FILEMASK_AUDIO
        call unimportant "validated: lyric downloader, audio file prober"

rem VALIDATE PARAMETERS:
        set AUDIO_FILE=%@UNQUOTE[%1]
        call validate-environment-variable   AUDIO_FILE   "First parameter must be an audio file that exists!"
        call validate-file-extension       "%AUDIO_FILE%" %FILEMASK_AUDIO%
        call unimportant "input file exists: %1"


rem Get artist and song so we can use them to download lyrics:
        set FILE_ARTIST=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        set   FILE_SONG=%@EXECSTR[%PROBER% -v quiet -show_entries format_tags=title  -of default=noprint_wrappers=1:nokey=1 "%AUDIO_FILE%"]
        call debug "Retrieved:%TAB%   artist=%FILE_ARTIST%%newline%%TAB%%tab%%tab%%tab%    title=%FILE_SONG%"


rem Download the lyrics:
        set                              LYRIC_RETRIEVAL_COMMAND=%LYRIC_DOWNLOADER% song "%FILE_SONG%" "%FILE_ARTIST%" --save
        echo %ANSI_COLOR_DEBUG- COMMAND: %LYRIC_RETRIEVAL_COMMAND%%ANSI_COLOR_NORMAL%
                           echo y  |    %LYRIC_RETRIEVAL_COMMAND%

rem Rename the downloaded lyrics to the right name:
        set   LATEST_FILE=%@EXECSTR[dir /b /odt | tail -1]
        set                   PREFERRED_LATEST_FILE_NAME=%@NAME[%AUDIO_FILE].%@EXT[%LATEST_FILE]
        set                     PREFERRED_TEXT_FILE_NAME=%@NAME[%AUDIO_FILE].txt
        echos %ANSI_COLOR_GREEN%
        if exist "%PREFERRED_LATEST_FILE_NAME%" (ren /q "%PREFERRED_LATEST_FILE_NAME%" "%PREFERRED_LATEST_FILE_NAME%.%_datetime.bak">nul)
        ren /q "%LATEST_FILE%" "%PREFERRED_LATEST_FILE_NAME%" >nul
        echos %ANSI_RESET%

        if exist "%PREFERRED_TEXT_FILE_NAME%" (ren /q "%PREFERRED_TEXT_FILE_NAME" "%PREFERRED_TEXT_FILE_NAME%.%_datetime.bak">nul)
        echos %ANSI_COLOR_RUN%
        (get-lyrics-with-lyricsgenius-json-processor.pl <"%PREFERRED_LATEST_FILE_NAME%" >"%PREFERRED_TEXT_FILE_NAME%" )| copy-move-post nomoji

rem If we ended up with a zero result, don't leave a blank file:
        call delete-zero-byte-files *.txt silent


rem Validate we did something:
        if exist "%PREFERRED_TEXT_FILE_NAME%" (call success "Lyrics downloaded to: %blink_on%%italics_on%%PREFERRED_TEXT_FILE_NAME%%ANSI_RESET%")
