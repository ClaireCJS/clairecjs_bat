@Echo OFF


:USAGE: %0 [force] {num_chars_to_remove} {wildcard}
:USAGE: %0 5               -- strip 1st 5 chars off every filename - DRY RUN ONLY
:USAGE: %0 force 5         -- strip 1st 5 chars off every filename - DO IT!!!!!!!
:USAGE: %0 force 2 *.jpg   -- strip 1st 2 chars off every jpg      


rem Default values:
        set MASK=*.*
        set NUM_TO_REMOVE=0

rem Fetch parameters:
        if "%1" eq "force" (
            if "%2" ne "" (set NUM_TO_REMOVE=%2)
            if "%3" ne "" (set MASK=%3)
        ) else (
            if "%1" ne "" (set NUM_TO_REMOVE=%1)
            if "%2" ne "" (set MASK=%2)
        )

rem Dry run?
        set                     dry_run=1
        if "%1" eq "force" (set dry_run=0)

rem Process all the filenames, either as a dry run or real run:
        for /h /o:n %%tmpfile in (%MASK%) (
            echo Processing file %tmpfile%...
            if %dry_run eq 1 (
                echos %STAR% %FAINT_OFF%%ANSI_COLOR_WARNING_SOFT%DRY RUN, BUT %ITALICS_ON%WOULD%ITALICS_OFF% DO: %FAINT_ON%%@ANSI_RANDFG[]
                echo  ren "%tmpfile%" "%@SUBSTR[%tmpfile%,%NUM_TO_REMOVE]"
            ) else (
                echos %@ANSI_RANDFG[]
                set NEW_NAME=%@SUBSTR[%tmpfile%,%NUM_TO_REMOVE]
                *ren "%tmpfile%" "%NEW_NAME"
            )
        )

rem Give advice and force-implemention if this is a dry run:
        if %dry_run eq 1 (
            if "%MASK%" eq "*.*" (unset /q MASK)
            echo %STAR% %faint_off%%ansi_color_advice%Run this command to actually do it:%NEWLINE%%TAB%%TAB%%FAINT_OFF%%BOLD_ON%%ansi_color_run%%0 force %NUM_TO_REMOVE% %MASK%
        )
