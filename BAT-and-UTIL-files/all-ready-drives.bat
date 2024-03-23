@Echo OFF

rem Check invocation
        if "%1" eq "" (
            %COLOR_ERROR%
            echo :USAGE:          call all-ready-drives "command to run on each drive with DRIVE_LETTER as a string that will get auto-substituted"
            echo :USAGE: example: call all-ready-drives "md DRIVE_LETTER:\BACKUPS" will make a backups on every ready drive, c:\backups, d:\backups, etc
            echo :USAGE:    Also: can set DRIVE_LETTERS_TO_USE=L M N O P    .... in order to only use certain letters or control the order. Must set it each call.
            echo :USAGE:                                                         (But you don't generally need to worry about this because it uses %%THE_ALPHABET_BY_DRIVE_PRIORITY%% internally)

            call scream
            goto :END
        )

rem get command, which may be enclosed in quotes (so we can in theory use multiple commands) or not (so we can use commands that use quote)
                      set COMMAND=%*
        if "2" eq "" (set COMMAND=%@UNQUOTE[%1%])


rem Go through each ready drive EXCEPT c which is our assumed drivfe, and substitute DRIVE_LETTER into the proper letter:
        set                                            OUR_ALPHABET_TO_USE=a b c d e f g h i j k l m n o p q r s t u v w x y z
        if defined THE_ALPHABET                   (set OUR_ALPHABET_TO_USE=%THE_ALPHABET%)
        if defined THE_ALPHABET_BY_DRIVE_PRIORITY (set OUR_ALPHABET_TO_USE=%THE_ALPHABET_BY_DRIVE_PRIORITY%)
        if defined DRIVE_LETTERS_TO_USE           (set OUR_ALPHABET_TO_USE=%DRIVE_LETTERS_TO_USE%)
        for %%letter in                              (%OUR_ALPHABET_TO_USE%) do (    
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

rem Cleanup
        if defined DRIVE_LETTERS_TO_USE (unset /q DRIVE_LETTERS_TO_USE)
