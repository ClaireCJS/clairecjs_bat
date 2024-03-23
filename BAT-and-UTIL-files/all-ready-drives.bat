@Echo Off

rem Check invocation
        if "%1" eq "" (
            %COLOR_ERROR%
            echo :USAGE:          call all-ready-drives "command to run on each drive with DRIVE_LETTER as a string that will get auto-substituted"
            echo :USAGE: example: call all-ready-drives "md DRIVE_LETTER:\BACKUPS" will make a backups on every ready drive, c:\backups, d:\backups, etc
            echo :USAGE:    Also: can set DRIVE_LETTERS_TO_USE=L M N O P    .... in order to only use certain letters or control the order. Must set it each call.
            echo :USAGE:                                                    .... [But you don't generally need to worry about this because it uses %%THE_ALPHABET_BY_DRIVE_PRIORITY%% internally]
            echo :USAGE:    Also: can set OPTION_SKIP_SAME_C=1              .... to make it not apply to any drive letter that is the same as the current computer's C: drive

            call scream
            goto :END
        )

rem get command, which may be enclosed in quotes (so we can in theory use multiple commands) or not (so we can use commands that use quote)
                       set COMMAND=%*
        if "%2" eq "" (set COMMAND=%@UNQUOTE[%1%])
        rem echo %ANSI_COLOR_DEBUG% command is %COMMAND%%ANSI_RESET%

rem Go through each ready drive EXCEPT c which is our assumed drivfe, and substitute DRIVE_LETTER into the proper letter:
        set                                            OUR_ALPHABET_TO_USE=a b c d e f g h i j k l m n o p q r s t u v w x y z
        if defined THE_ALPHABET                   (set OUR_ALPHABET_TO_USE=%THE_ALPHABET%)
        if defined THE_ALPHABET_BY_DRIVE_PRIORITY (set OUR_ALPHABET_TO_USE=%THE_ALPHABET_BY_DRIVE_PRIORITY%)
        if defined DRIVE_LETTERS_TO_USE           (set OUR_ALPHABET_TO_USE=%DRIVE_LETTERS_TO_USE%)
        rem call debug                                "OUR_ALPHABET_TO_USE is '%OUR_ALPHABET_TO_USE%'"
        for %%tmpletter in                           (%OUR_ALPHABET_TO_USE%) gosub doLetter %tmpletter
goto :END

        :doLetter [letter]
            set DRIVE_LETTER_PRETTY=%emphasis%%@UPPER[%letter%]%deemphasis%:
            rem call important_less "doing %drive_letter_pretty%"
            rem echo if "%%@READY[%letter%]"{%@READY[%letter%]} eq "1" 

                                                                                set SAME=0
            if "%@UPPER[%[%letter]]" eq "%@UPPER[%[%[DRIVE_C_%MACHINENAME%]]]"  set SAME=1
            rem same for %letter% is %same%
            if %SAME eq 0 .and. %OPTION_SKIP_SAME_C eq 1  goto :Not_Same
                echos %STAR% ``
                echo %ANSI_COLOR_RED%Skipping drive %DRIVE_LETTER_PRETTY% %ANSI_COLOR_RED%because it's the same as C: for %[EMOJI_MACHINE_%MACHINENAME%]%MACHINENAME%%[EMOJI_MACHINE_%MACHINENAME%]... %ANSI_RESET%
                goto :End_Of_For_Loop
            :Not_Same


            if "%@READY[%letter%]" ne "1" goto :Drive_Not_Ready
                echo %STAR% Doing drive letter %DRIVE_LETTER_PRETTY%... 
                title Doing %letter%: -- %COMMAND% -- (remember: DRIVE_LETTER will be substituted with the drive letter of each and every available drive in this situation)
                set FIXED_COMMAND=%@REPLACE[DRIVE_LETTER,%letter,%COMMAND]

                rem call debug "cmd=%COMMAND%%NEWLINE%         fix=%FIXED_COMMAND%%NEWLINE%"                   
                rem echo WOULD DO: FIXED_COMMAND=%FIXED_COMMAND%

                rem Actually do it:
                        %FIXED_COMMAND%
            :Drive_Not_Ready
            :End_Of_For_Loop
        return


:END

rem Cleanup
        if defined DRIVE_LETTERS_TO_USE (unset /q DRIVE_LETTERS_TO_USE)
        if defined OPTION_SKIP_SAME_C   (unset /q OPTION_SKIP_SAME_C)