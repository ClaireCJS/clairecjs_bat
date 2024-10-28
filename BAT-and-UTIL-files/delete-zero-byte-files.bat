@echo off

:USAGE: delete-zero-byte-files           - deletes all zero byte files
:USAGE: delete-zero-byte-files *.lrc     - deletes all zero byte files with the LRC extension


               set FILES=*.*
if "%1" ne "" (set FILES=%1)

:: Loop through all files in the target directory
for %%TmpFileForZeroByteCheck in (%FILES%) do (
    :: Check if the file size is zero bytes
    if %%~zf==0 (
        :: Delete the zero-byte file
        %COLOR_REMOVAL%
        *del  "%%TmpFileForZeroByteCheck"
        :echo * Deleted zero-byte file: %%TmpFileForZeroByteCheck
    )
)

rem %COLOR_SUCCESS%
rem echo.
if "%1" ne "silent" .and. "%2" ne "silent" .and. "%3" ne "silent" (call success "All zero-byte files have been deleted.")


