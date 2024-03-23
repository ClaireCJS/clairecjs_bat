@Echo OFF

rem Check invocation
        if "%1" eq "" (
            %COLOR_ERROR%
            echo :USAGE:          call all-ready-drives "command to run on each drive with DRIVE_LETTER as a string that will get auto-substituted"
            echo :USAGE: example: call all-ready-drives "md DRIVE_LETTER:\BACKUPS" will make a backups on every ready drive, c:\backups, d:\backups, etc
            call scream
            goto :END
        )

rem get command, which may be enclosed in quotes (so we can in theory use multiple commands) or not (so we can use commands that use quote)
                      set COMMAND=%*
        if "2" eq "" (set COMMAND=%@UNQUOTE[%1%])


rem Go through each ready drive EXCEPT c which is our assumed drivfe, and substitute DRIVE_LETTER into the proper letter:
        for %%letter in (a b d e f g h i j k l m n o p q r s t u v w x y z) do (    
                rem echo if "%%@READY[%letter%]"{%@READY[%letter%]} eq "1" 
                if "%@READY[%letter%]" eq "1" (
                    echo %STAR% Doing drive letter %emphasis%%@UPPER[%letter%]%deemphasis%:... 
                    set FIXED_COMMAND=%@REPLACE[DRIVE_LETTER,%letter,%COMMAND]

                    rem call debug "cmd=%COMMAND%%NEWLINE%         fix=%FIXED_COMMAND%%NEWLINE%"                   
                    rem echo %FIXED_COMMAND%

                    %FIXED_COMMAND%
                )
        )

:END
