@Echo OFF
@on break cancel
REM USAGE: $0 {filemask to seach for first file from}

set VERBOSITY=1 %+ REM 0=silent, 1=announce conclusions, 2=announce some debug, 3=announce every filename

REM Get file mask
    set MASK=*.*
    if "%1" ne "" (set MASK=%1)
    if %VERBOSITY% GE 2 (%COLOR_IMPORTANT_LESS% %+ echo * MASK set to: %MASK%)

REM Find "first" file:
    REM This was not valid because FINDFIRST only finds the first file matching in your list, 
    REM not the first file on the harddrive out of all the files sent to FINDFIRST
    REM         set FIRST_FILE=%@FINDFIRST[%MASK%]

    set FIRST_FILE=
    for /h /o:n %filename in (%MASK%) do (
        if %VERBOSITY% GE 3 (%COLOR_IMPORTANT% %+ echo * Checking file: %filename)
        if %SUBSTR[%%,%filename] != 0 (
            if %VERBOSITY% GE 2 (
                %COLOR_WARNING% 
                echo WARNING: filename=%filename% has percent - this script will probably fail %+ %COLOR_NORMAL%
                echo set escaped_filename=%@REPLACE[%%,%%%%,%filename]
                set      escaped_filename=%@REPLACE[%%,%%%%,%filename]
                echo     escaped_filename=%escaped_filename%
            )
        )
        set firstFile=%filename%
        set FIRST_FILE=%filename%
        goto :Got_It
    )
    :Got_It
    if %VERBOSITY% GE 1 (%COLOR_IMPORTANT% %+ echo * FIRST_FILE set to: %FIRST_FILE%)




