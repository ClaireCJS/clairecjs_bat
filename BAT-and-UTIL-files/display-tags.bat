@Echo OFF

set FILE=%@UNQUOTE[%1]
set  EXT=%@EXT["%FILE%"]

iff     "%EXT%" eq "flac" then

        call display-flac-tags %FILE% %2$

elseiff "%EXT%" eq "mp3" then

        call list-mp3-tags "%FILE%" %2$

elseiff "%@RegEX[%EXT%,%FILEMASK_IMAGE%]" eq "1" then

        call exiflist "%FILE%" %2$
else
        call warning "%BAT%\%0 —— Don't have a way to tag %italics_on%%blink_on%%EXT%%blink_off%%italics_off% files like '%italics_on%%file%%italics_off%'"
        pause /# 10
endiff

