@echo off

:USAGE: delete-zero-byte-files           - deletes all zero byte files
:USAGE: delete-zero-byte-files *.lrc     - deletes all zero byte files with the LRC extension


               set FILES=*.*
if "%1" ne "" (set FILES=%1)

:: Loop through all files in the target directory
for %%f in (%FILES%) do (
    :: Check if the file size is zero bytes
    if %%~zf==0 (
        :: Delete the zero-byte file
        %COLOR_REMOVAL%
        *del  "%%f"
        :echo * Deleted zero-byte file: %%f
    )
)

%COLOR_SUCCESS%
echo.
echo * All zero-byte files have been deleted.

