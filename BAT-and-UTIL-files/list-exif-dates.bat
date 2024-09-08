@echo off

call validate-environment-variable FILEMASK_IMAGE
call validate-in-path exiflist grep

echo.
for %file in (%FILEMASK_IMAGE) do gosub process %file


goto :END

    :process [file]
        %COLOR_IMPORTANT%
        echos %file: ``
        %COLOR_RUN%
        rem set OUTPUT=%@EXECSTR[call exiflist "%file" |& grep -i "date.*taken"]
        REM echo OUTPUT is '%OUTPUT%'
        REM echo        if %INDEX[%OUTPUT,does not contain EXIF] ne 1 color bright yellow on black
        rem echo %OUTPUT% | gr -v echo.is.off
        call exiflist "%file" | grep -i "date.*taken"
        echo.
    return

REM this inside loop crashed TCMD28    set FNAME=%@FORMAT[%file%,25]

:END

