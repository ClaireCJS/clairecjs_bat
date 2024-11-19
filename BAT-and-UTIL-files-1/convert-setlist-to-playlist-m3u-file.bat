@Echo OFF
 on break cancel

:DESCRIPTION: A *very very very* experimental script to change a playlist pasted from setlist.fm into a playlist in our internal system.

:DESCRIPTION: This is a task performed so rarely that this script was never fully completed.



::     #from setlist.fm, a copy-pasted playlist looks like this:
::     I'm Gonna Strangle You 
::     Slogans 
::     Queen Kong 
::     Dingbat 
::     Guest List 
::     Supermarket Fantasy 
::     My Right 

::     I Wrote Holden Caulfield 
::     Totally 
::     Friday Night Nation 
::     Things Aren't So Bad After All 
::     Second Floor East 
::     Don't Turn Out The Lights 
::     My Brain Hurts 
::     So Long, Mojo 
::     Cindy's on Methadone 
::     Hey Suburbia 
::     99 
::     This Ain't Hawaii 
::     I Can See Clearly Now 
::     (Johnny Nash cover)
::     Cool Kids 


:goto :TestPoint

rem ENVIRONMENT VALIDATION:
        call validate-environment-variable COLOR_DEBUG COLOR_IMPORTANT COLOR_NORMAL  COLOR_UNIMPORTANT COLOR_WARNING EDITOR
        call valdiate-in-path              insert-before-each-line mchk get-meat-from-mp3-filename.pl vlc set-tmp-file save-clipboard-to-temp-file

rem WARNING:
        cls
        %COLOR_IMPORTANT% %+ echo * This will convert a playlist IN THE CLIPBOARD into an mp3 file.
                          %+ echo   If you don't have a playlist in the clipboard from setlist.fm, this won't work. %+ echo.
        %COLOR_WARNING%   %+ echo Ctrl-Break now if you don't have a playlist in your clipboard!      %+ pause >nul %+ %COLOR_NORMAL%

rem SAVE CLIPBOARD TO FILE:
        call save-clipboard-to-temp-file playlist-conversion-clipboard %+ REM sets & validates %CLIPBOARD_SAVED_TO%

rem LET USER SEE IF FILE IS RIGHT:
        %COLOR_IMPORTANT% %+ cls %+ type "%CLIPBOARD_SAVED_TO%"                                       %+ echo.      %+ echo.
        %COLOR_WARNING%   %+ echo Ctrl-Break now if this does not appear to be a playlist...          %+ pause >nul %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ echo.

rem LET USER HAND-EDIT FILE:
        %EDITOR% "%CLIPBOARD_SAVED_TO%"
        %COLOR_IMPORTANT% %+ cls %+ type "%CLIPBOARD_SAVED_TO%"                                       %+ echo.      %+ echo.
        %COLOR_WARNING%   %+ echo Ctrl-Break now if this still does not seem like something workable. %+ pause >nul %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ echo.

rem CHOOSE OUTPUT FILES:
        call set-tmp-file %+ SET    OUTPUT_PLAYLIST=%TMPFILE_DIR%\playlist-%TMPFILE_FILE.m3u                %+ >:u8"%OUTPUT_PLAYLIST%" %+ REM zero out new file
                             SET PUBLISHED_PLAYLIST=%MP3OFFICIAL%\LISTS\setlist-converted-to-playlist.m3u
        call set-tmp-file %+ SET     TRUE_TEMP_FILE=%TMPFILE%

rem ASK FOR OPTIONAL BAND NAME:
        %COLOR_WARNING%                             %+ cls %+ echo * Enter optional band name, to pair down results: %+ %COLOR_NORMAL%
        if "%BANDNAME%" eq "" set BANDNAME=.*       %+ rem  ".*" is convenient because if they hit enter & don't change it, regex results are the same
        eset BANDNAME


rem GO THROUGH EACH SONG AND ADD TO THE PLAYLIST:
        :TestPoint
        for /f "tokens=1-9999" %mp in (%CLIPBOARD_SAVED_TO%) gosub ProcessSong "%mp%"

rem PUBLISH THE PLAYLIST, OPEN IT IN TEXT EDITOR:
        (type "%OUTPUT_PLAYLIST%" |:u8 sort -u )>:u8 "%PUBLISHED_PLAYLIST%"
        %EDITOR% "%PUBLISHED_PLAYLIST%"


rem START THE PLAYLIST WITH VLCP_LAYER:
        %COLOR_WARNING%   %+ echo Ctrl-Break now if you don't have a playlist in your clipboard!      %+ pause >nul %+ %COLOR_NORMAL%
        call vlc --loop "%PUBLISHED_PLAYLIST%"


goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :ProcessSong [song]
            :: tell
                    %COLOR_NORMAL %+ echo.
                    %COLOR_ALARM% %+ echos * Processing song: %song% ...               %+ %COLOR_NORMAL%    %+ echo  ``

            :: reduce b.s. out of title to get a real song title
                    set MEAT=%@EXECSTR[get-meat-from-mp3-filename.pl "%song%"]         %+ %COLOR_DEBUG%     %+ echo     MP3_NAME_MEAT=[%MEAT%] 

            :: determine the command to check the catalog for this song:
                    set CHECK_FOR_MP3=call mchk %[BANDNAME].*%MEAT%                    %+ %COLOR_IMPORTANT% %+ echo     CHECK_FOR_MP3=[%CHECK_FOR_MP3%] %+ %COLOR_SUBTLE%

            :: perform the actual check, but only to a temp file:
                                    >:u8"%TRUE_TEMP_FILE%"                                %+ REM zero temp file out so results are 0 in the case of %CHECK_FOR_MP3% failing
                    %CHECK_FOR_MP3% >:u8"%TRUE_TEMP_FILE%"

            :: display the results, along with a line count:
                    type "%TRUE_TEMP_FILE%" |:u8 insert-before-each-line "        " |:u8 80  
                    set LINES=%@EVAL[%@LINES["%TRUE_TEMP_FILE%"]+1]                    %+ %COLOR_DEBUG      %+ echo     LINES=[%LINES%]

            :: concatenate the results to our output playlist:
                    type %TRUE_TEMP_FILE%>>:u8"%OUTPUT_PLAYLIST%"
    return
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END


