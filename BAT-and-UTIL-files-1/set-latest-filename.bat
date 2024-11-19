@Echo OFF
@on break cancel

set FOR_OPTIONS=
set DIR_MODE=0
set latestMatchingName=
set latestMatchingDate=0
set ENTITY_FOR_PRINT=File
set VERBOSE=0                  %+ REM 0=silent, 1=conclusions printed, 2=each age printed

set MASK=*.*

if "%1" ne "" (set MASK=%1)
if "%1" eq "dir" (
    set ENTITY_FOR_PRINT=Directory
    set FOR_OPTIONS=/a:d /h
    set MASK=*
    set DIR_MODE=1
)

for %FOR_OPTIONS% %filename in (%MASK%) do (
    set fileAge=%@FILEAGE["%filename%", W] 
    if %VERBOSE GE 2 (%COLOR_SUBTLE% %+ echo - %ENTITY_FOR_PRINT% age is: %fileAge, for: %filename)
    if %fileAge GT %latestMatchingDate (
        set latestMatchingDate=%fileAge 
        set latestMatchingName=%filename
    )
)

if "%DIR_MODE%" ne "1" (
    set LATESTFILE=%latestMatchingName%
    set LATEST_FILE=%latestMatchingName%
    set LATESTFILENAME=%latestMatchingName%
    set LATEST_FILENAME=%latestMatchingName%
) else (
    set LATESTDIR=%latestMatchingName%
    set LATEST_DIR=%latestMatchingName%
    set LATESTDIRNAME=%latestMatchingName%
    set LATEST_DIRNAME=%latestMatchingName%
)
if %VERBOSE GE 1 (%COLOR_IMPORTANT_LESS% %+ echo - The latest %ENTITY_FOR_PRINT% is: %latestMatchingName% %+ %COLOR_NORMAL%)


