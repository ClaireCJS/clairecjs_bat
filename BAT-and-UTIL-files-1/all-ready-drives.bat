@Echo Off
 on break cancel


rem Check invocation
        if "%1" eq "" (
            %COLOR_ERROR%
            echo :USAGE:          call all-ready-drives "command to run on each drive with DRIVE_LETTER as a string that will get auto-substituted"
            echo :USAGE: example: call all-ready-drives "md DRIVE_LETTER:\BACKUPS" will make a backups on every ready drive, c:\backups, d:\backups, etc
            echo :USAGE:    Also: can set DRIVE_LETTERS_TO_USE=L M N O P    .... in order to only use certain letters or control the order. Must set it each call.
            echo :USAGE:                                                    .... [But you don't generally need to worry about this because it uses %%THE_ALPHABET_BY_DRIVE_PRIORITY%% internally]
            echo :USAGE:    Also: can set OPTION_SKIP_SAME_C=1              .... to make it not apply to any drive letter that is the same as the current computer's C: drive
            echo :USAGE:    Also: can set OPTION_ECHO_RAYRAY=1              .... to echo 'rayrayrayray' to our command ... needed for overwriting on copies
            echo :USAGE:    
            echo :USAGE:    Note: MACHINENAME and DRIVE_C_MACHINAME must be set if you don't want to end up trying to copy files over themselves (which shoudln't hurt, but is ugly-looking)

            call scream
            goto :END
        )
        set FIXED_COMMAND=N/A


rem get command, which may be enclosed in quotes (so we can in theory use multiple commands) or not (so we can use commands that use quote)
                       set COMMAND=%*
        if "%2" eq "" (set COMMAND=%@UNQUOTE[%1%])
        rem echo %ANSI_COLOR_DEBUG% command is %COMMAND%%ANSI_RESET%

        set                                            OUR_ALPHABET_TO_USE=a b c d e f g h i j k l m n o p q r s t u v w x y z %+ rem Default alphabet
        if defined THE_ALPHABET                   (set OUR_ALPHABET_TO_USE=%THE_ALPHABET%)                                     %+ rem Allow user-defined alphabet 
        if defined THE_ALPHABET_BY_DRIVE_PRIORITY (set OUR_ALPHABET_TO_USE=%THE_ALPHABET_BY_DRIVE_PRIORITY%)                   %+ rem Allow user-defined alphabet by drive priority —— when testing with another human you tend to want it to copy it to that human's drive before all the other drives, and want your own alphabet order
        if defined DRIVE_LETTERS_TO_USE           (set OUR_ALPHABET_TO_USE=%DRIVE_LETTERS_TO_USE%)                             %+ rem Allow on-the-fly user-defined alphabet —— for very specialized situations
        rem call debug                                "OUR_ALPHABET_TO_USE is '%OUR_ALPHABET_TO_USE%'"

        
rem Go through each ready drive, and substitute DRIVE_LETTER into the proper letter:
        call wake-all-drives
        echo.
        for %%tmpletter in (%OUR_ALPHABET_TO_USE%) gosub doLetter %tmpletter

goto :END






        :doLetter [letter]
            set DRIVE_LETTER_PRETTY=%emphasis%%@UPPER[%letter%]%deemphasis%:
            rem call important_less "doing %drive_letter_pretty%"
            rem echo if "%%@READY[%letter%]"{%@READY[%letter%]} eq "1" 


                                                                                set SAME=0
            if "%@UPPER[%[%letter]]" eq "%@UPPER[%[%[DRIVE_C_%MACHINENAME%]]]"  set SAME=1
            rem same for %letter% is %same%
            if  not  defined     OPTION_SKIP_SAME_C       (goto :Not_Skipped)
            if %SAME eq 0 .and. %OPTION_SKIP_SAME_C eq 1  (goto :Not_Skipped)
                echo.
                rem echos %STAR% ``
                rem echo %ANSI_COLOR_RED%Skipping drive %DRIVE_LETTER_PRETTY% %ANSI_COLOR_RED%because it's the same as C: for %[EMOJI_MACHINE_%MACHINENAME%]%MACHINENAME%%[EMOJI_MACHINE_%MACHINENAME%]... %ANSI_RESET%
                call bigecho %STAR% %ANSI_COLOR_RED%Skipping drive %DRIVE_LETTER_PRETTY%
                echo       %ITALICS_ON%%ANSI_COLOR_RED%(because it's the same as C: for %[EMOJI_MACHINE_%MACHINENAME%]%MACHINENAME%%[EMOJI_MACHINE_%MACHINENAME%]...)%ITALICS_OFF%%ANSI_RESET%
                echo.
                goto :End_Of_For_Loop
            :Not_Skipped

            if "%@READY[%letter%]" ne "1" goto :Drive_Not_Ready
                rem no yes
                echo.
                call bigecho %STAR% Doing drive letter %DRIVE_LETTER_PRETTY%... 
                set FIXED_COMMAND=%@REPLACE[DRIVE_LETTER,%letter,%COMMAND]
                title Doing %letter%: -- %FIXED_COMMAND% 

                rem call debug "cmd=%COMMAND%%NEWLINE%         fix=%FIXED_COMMAND%%NEWLINE%"                   
                rem echo WOULD DO: FIXED_COMMAND=%FIXED_COMMAND%

                rem Actually do it —— a lot of experimental stuff in this section that isn't actually used:
                        if %OPTION_ECHO_RAYRAY ne 1 (goto :NoRayRay)

                                if %OPTION_ARD_POSTPROCESS eq 1 (goto :PostprocessYes)
                                         echo rayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayray|%FIXED_COMMAND%
                                goto :PostprocessYesDone
                                :PostprocessYes
                                        rem echo %ansi_color_debug%- DEBUG: FIXED_COMMAND is: %FIXED_COMMAND% %ansi_color_normal%
                                        echos %@RANDFG_SOFT[]
                                        (echo rayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayrayray|%FIXED_COMMAND%) |&:u8 copy-move-post.py |:u8 fast_cat
                                :PostprocessYesDone

                        goto :NoRayRayEnd
                                :NoRayRay
                                iff %OPTION_ECHO_RAYRAY ne 1 then
                                    iff %OPTION_ARD_POSTPROCESS ne 1 then
                                            %FIXED_COMMAND%
                                    else
                                            echos %@RANDFG_SOFT[]
                                            (%FIXED_COMMAND% |&:u8 copy-move-post.py) |:u8 fast_cat
                                    endiff
                                endiff
                        :NoRayRayEnd
            :Drive_Not_Ready
            :End_Of_For_Loop
        return


:END

rem Cleanup
        if defined DRIVE_LETTERS_TO_USE (unset /q DRIVE_LETTERS_TO_USE)
        if defined OPTION_SKIP_SAME_C   (unset /q OPTION_SKIP_SAME_C  )
        call fix-window-title
        echos %ANSI_RESET%