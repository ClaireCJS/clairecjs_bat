@echo off
@on break cancel

:PUBLISH:
:DECRIPTION:   random file selector
:EFFECT:       sets RANDFILE to filename of randomly selected file
:SIDE-EFFECTS: also sets RANDFILE_FULL for the full-path filename, and RANDFILE_FILENAME for the filename-only
:USAGE:        call set-randomfile {optional wildcards}
:EXAMPLE:      call set-randomfile c:\util\tool\profiles\*.ini
:DEPENDENCIES: fatal_error.bat, print-message.bat
:USED-BY:      randfile.bat (alias), make-black-into-a-randomblack.bat (for accessibility)

REM get parameters
    set DEBUG_RANDOM=0          %+ REM set to 1 to see stuff, 2 to see even more stuff like going through the loop
    set MASK=%1
    if "%MASK%" eq "" (set MASK=*.*)

REM get folder
    set "folder=%~1"
    if "%folder%"=="" set "folder=%CD%"

REM get file list and count
    set FILES=%@EXPAND[%MASK%]
    set COUNT=%@FILES[/h %MASK%]
    if "%COUNT%" == "0" (call fatal_error "FATAL ERROR! set-randomfile called in a folder (%_CWP) that has no files matching %MASK% in it!")
    if "%DEBUG_RANDOM%" gt "1" (call debug "--- Files      are %FILES%")
    if "%DEBUG_RANDOM%" eq "1" (call debug "--- Filecount   is %COUNT%")

REM generate random index
    set randomIndex=%@RANDOM[1,%COUNT%]
    if "%DEBUG_RANDOM%" eq "1" (call debug "--- randomIndex is %randomIndex%")

REM go through filelist to find our index
    set currentIndex=0
    for %%tmpFile in (%FILES%) do (
        set /a "currentIndex+=1"
        if "%DEBUG_RANDOM%" gt 1 (call debug "Checking file %currentIndex%: %tmpFile")
        if %currentIndex% == %randomIndex% set RANDFILE=%@UNQUOTE[%tmpFile%]
    )


REM strip off quotes, though
    set RANDFILE=%@UNQUOTE[%RANDFILE]

REM set side/audit/synonym/alias/extra variables based on our results
    :et RANDFILE=%RANDFILE%
    set RANDFILE_FULL=%RANDFILE%
    set RANDFILE_FILENAME=%@FILENAME[%RANDFILE%]
    set RANDFILE_FILENAME_ONLY=%@FILENAME[%RANDFILE%]
    set RANDOMFILE=%RANDFILE%
    set RANDOMFILE_FULL=%RANDFILE%
    set RANDOMFILE_FILENAME=%@FILENAME[%RANDFILE%]
    set RANDOM_FILE=%RANDFILE%
    set RANDOM_FILE_FULL=%RANDFILE%
    set RANDOM_FILE_FILENAME=%@FILENAME[%RANDFILE%]
    set RANDOM_FILE_FILENAME_ONLY=%@FILENAME[%RANDFILE%]


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END

if "%DEBUG_RANDOM%" eq "1" (
    call debug "*** RANDFILE          = %RANDFILE%"
    call debug "*** RANDFILE_FULL     = %RANDFILE_FULL%"
    call debug "*** RANDFILE_FILENAME = %RANDFILE_FILENAME%"
)

