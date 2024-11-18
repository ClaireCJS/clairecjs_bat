@Echo Off

rem Grab parameters:
        set FILE=%@UNQUOTE[%1]
        set  EXT=%@EXT["%FILE%"]
        set FOUND=0

rem Need SOMEthing:
        iff "%1" eq "" then
                echo.
                call warning "No filename given to display tags of!"
                goto :END
        endiff

rem Validate environment:
        iff 1 ne %validated_display_tags% then
                call validate-in-path ffprobe.exe display-flac-tags list-mp3-tags exiflist insert-before-each-line
                call validate-environment-variables filemask_audio bat
                set  validated_display_tags=1
        endiff

rem Deal with wildcard parameters by expanding them and recursing through them:
        iff "%@RegEx[[\*\?],%*]" eq "1" then
                set DISPLAY_TAGS_PREFIX_NAME=1
                rem for %%tmpfile in (%*) do (if "%@RegEx[%@EXT[%tmpfile],%filemask_audio]" eq "1"  (call %0 "%tmpfile%"))
                for %%tmpfile in (%*) do (call %0 "%tmpfile%")
                set DISPLAY_TAGS_PREFIX_NAME=0
                goto :END
        endiff


rem Display depending on extension: flac vs mp3 vs image vs video
        iff     "%EXT%" eq "flac" .or. "%FILE%" eq "*" then
                set  FOUND=1
                call display-flac-tags "%FILE%" %2$
        endiff

        iff "%EXT%" eq "mp3"  .or. "%FILE%" eq "*" then
                set  FOUND=1
                call list-mp3-tags     "%FILE%" %2$
        endiff

        iff "%@RegEX[\Q%EXT%\E,%FILEMASK_IMAGE%]" eq "1" .or. "%FILE%" eq "*" then
                set  FOUND=1
                call exiflist          "%FILE%" %2$
        endiff

        iff "%@RegEX[\Q%EXT%\E,%FILEMASK_VIDEO%]" eq "1" .or. "%FILE%" eq "*" then
                set  FOUND=1
                ifF 1 EQ %DISPLAY_TAGS_PREFIX_NAME% then
                       (ffprobe.exe    "%FILE%" %2$ |&|:u8 insert-before-each-line "%ANSI_COLOR_MAGENTA%%@unquote[%file%]%@unquote[%2]:%ANSI_COLOR_NORMAL%") |:u8 fast_cat
                else                
                        ffprobe.exe    "%FILE%" %2$
                endiff
        endiff

rem Mention if it was a file extension we don't know how to display tags of:
        iff 0 eq %FOUND% then
                set silent=``
                if 1 eq %DISPLAY_TAGS_PREFIX_NAME% (set silent=silent)
                call warning           "%BAT%\%0 %EMDASH% Don't have a way to tag %italics_on%%blink_on%%EXT%%blink_off%%italics_off% files like '%italics_on%%file%%italics_off%'" %silent%
                iff 1 ne %DISPLAY_TAGS_PREFIX_NAME% then
                        pause /# 10
                endiff                
        endiff

:END

