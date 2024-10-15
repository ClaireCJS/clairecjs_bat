@Echo OFF

:DESCRIPTION: Locks a non-scrollable banner message at the top 3 rows of our console menu. Good for keeping track of tasks, percentage complete, etc.

:USAGE: top-banner unlock               - unlock any previously set top banner
                                        
:USAGE: top-banner {no arguments}       - banner message is a report of free space on the current drive
:USAGE: top-banner  C:                  - banner message is a report of free space on the given drive letter
:USAGE: top-banner "Hello precious!"    - banner message is a custom message saying whatever we want
:USAGE: top-banner "Hi! {freespace}"    - banner message is a custom message that includes our report of free space on the current drive
:USAGE: top-banner "Hi! {freespace}" S: - banner message is a custom message that includes our report of free space on the given drive letter



rem Capture parameters:
        set TB_PARAM_1=%1
        set TB_PARAM_2=%2

rem ENVIRONMENT: Validate the environment:
        if 1 ne %VALIDATED_LOCKED_MESSAGE_BAT% (
                call validate-environment-variables PLUGIN_STRIPANSI_LOADED ANSI_UNLOCK_MARGINS ANSI_SAVE_POSITION ANSI_RESTORE_POSITION ANSI_EOL NEWLINE CONNECTING_EQUALS BLINK_ON BLINK_OFF DOT ANSI_COLOR_ERROR ANSI_UNLOCK_MARGINS
                set VALIDATED_LOCKED_MESSAGE_BAT=1
        )


rem CONFIG: Set message background color & divider:
        set LOCKED_MESSAGE_COLOR_BG=%@ANSI_BG[0,0,64]
        set LOCKED_MESSAGE_COLOR=%ANSI_COLOR_IMPORTANT%%LOCKED_MESSAGE_COLOR_BG%
        rem DIVIDER_FILE=%BAT%\dividers\rainbow-%_COLUMNS.txt is defined when it happens later
        rem DIVIDER=%@REPEAT[%CONNECTING_EQUALS,%@EVAL[%_COLUMNS]] is only defined if needed
        set DOTTIE=%BLINK_ON%%DOT%%BLINK_OFF%
        rem TOO SLOW: call echo-rainbow generate %DIVIDER% %+ set DIVIDER=%RAINBOW_TEXT%



rem Respond to command-line parameters:
        unset /q LOCKED_MESSAGE
        rem Unlock mode:
                if "%TB_PARAM_1" eq "unlock" (
                        echos %ANSI_UNLOCK_MARGINS%
                        repeat 2 echo.
                        goto :END
                )



rem Set free space stuffs:
        set CWDTMP=%_CWD
        set CUSTOM_MESSAGE=0
        set FREE_SPACE_MESSAGE_IS_USED=0
        set USE_JUST_FREE_SPACE_MESSAGE=0
        iff "%TB_PARAM_1" eq "" then
                set USE_JUST_FREE_SPACE_MESSAGE=1
        else
                set LOCKED_MESSAGE=%@UNQUOTE[%TB_PARAM_1]
                set CUSTOM_MESSAGE=1
                rem echo inner: got '%TB_PARAM_1' len=%@LEN[%TB_PARAM_1] instr=%@INSTR[1,1,%TB_PARAM_1] %goat%
                iff %@LEN[%TB_PARAM_1] eq 2 .and. "%@INSTR[1,1,%TB_PARAM_1]" eq ":" then
                        rem echo first[a1]%goat%
                        set CWDTMP=%TB_PARAM_1 
                        set USE_JUST_FREE_SPACE_MESSAGE=1
                        set FREE_SPACE_MESSAGE_IS_USED=1
                        iff 0 eq %@READY[%TB_PARAM_1] then
                                set LOCKED_MESSAGE=%ANSI_COLOR_ERROR%Drive %TB_PARAM_1: is not ready 
                                goto :Display_Message_Now
                        endiff
                endiff
                iff %@LEN[%TB_PARAM_2] eq 2 .and. "%@INSTR[1,1,%TB_PARAM_2]" eq ":" then
                        rem echo second[b2]%goat%
                        set CWDTMP=%TB_PARAM_2 
                        set USE_JUST_FREE_SPACE_MESSAGE=0 %+ rem This is tricky, but it should actually be 0 because if PARAM_2 is a drive letter, we're using a custom message
                        set FREE_SPACE_MESSAGE_IS_USED=1
                        iff 0 eq %@READY[%TB_PARAM_2] then
                                set LOCKED_MESSAGE=%ANSI_COLOR_ERROR%Drive %TB_PARAM_2: is not ready 
                                goto :Display_Message_Now
                        endiff
                endiff
        endiff
        rem         echo DEBUG: echo %blink%CWDTMP is %CWDTMP%%blink_off% ... locked_message='%locked_message%'
        rem call debug "TB_PARAM_1=%TB_PARAM_1,TB_PARAM_2=%TB_PARAM_2,CWDTMP=%CWDTMP %goat%"


rem Calculate free space values:
        set DF=%@DISKFREE[%CWDTMP]
        set FREE_MEGS=%@COMMA[%@FLOOR[%@EVAL[%DF%/1024/1024]]]
        set FREE_GIGS=%@COMMA[%@FORMATN[.2,%@EVAL[%DF%/1024/1024/1024]]]
        set FREE_TERA=%@FORMATN[.2,%@EVAL[%DF%/1024/1024/1024/1024]]

rem Create message text:
        set OUR_SLASH=%bold_on%%slash%%bold_off%
        SET FREE_SPACE_MESSAGE=%bold_on%%FREE_MEGS%%bold_off% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%M %our_slash% %locked_message_color%%FREE_GIGS% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%G
        if %FREE_GIGS gt 1000 (set FREE_SPACE_MESSAGE=%FREE_SPACE_MESSAGE%%locked_message_color% %our_slash% %FREE_tera% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%T)
        set FREE_SPACE_MESSAGE=%FREE_SPACE_MESSAGE% %italics_on%free%italics_off% on %bold_on%%@UPPER[%@INSTR[0,2,%CWDTMP]]%bold_off%%LOCKED_MESSAGE_COLOR%
        if %USE_JUST_FREE_SPACE_MESSAGE eq 1 ( set LOCKED_MESSAGE=%FREE_SPACE_MESSAGE% )

rem Respond to environment-variable parameter to stick text AFTER free space if you call it with no parameters: [[[EXPERIMENTAL——NOT IMPLEMENTED]]]        rem if defined DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE (        rem         set LOCKED_MESSAGE=%LOCKED_MESSAGE%%DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE%        rem         unset /q DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE        rem )

rem Substitute the token {freespace} with our generated free space message:
        set LOCKED_MESSAGE=%@unquote[%@rereplace[{freespace},"%FREE_SPACE_MESSAGE%","%locked_message"]]


rem Get message length and create side-spacers of appropriate length to center the message:
        :Display_Message_Now
                                             SET LOCKED_MESSAGE_LENGTH=%@LEN[%@STRIP_ANSI[%LOCKED_MESSAGE]]
        if %FREE_SPACE_MESSAGE_IS_USED eq 1 (SET LOCKED_MESSAGE_LENGTH=%@EVAL[%LOCKED_MESSAGE_LENGTH+2])         %+ rem the slash emojis we use twice in our free space message are not correctly measured by %@LEN[] which creates a bug of wrapping the line onto the next line, unless we manually deduct the number of wide emojis {or at least, the # of wide emojis that %@LEN isn't correctly counting!} ... May take some experimentation if you change the free message format.

        set SPACER=%@REPEAT[ ,%@FLOOR[%@EVAL[(%_COLUMNS-%LOCKED_MESSAGE_LENGTH-3)/2-2]]]``

rem Set up dividers:
        set        DIVIDER_FILE=%BAT%\dividers\rainbow-%_COLUMNS.txt
        iff exist %DIVIDER_FILE% then 
                set DIVIDER=%@LINE[%DIVIDER_FILE,0]
                set INTERNAL_DIVIDER=0
        else 
                set DIVIDER=%@REPEAT[%CONNECTING_EQUALS,%@EVAL[%_COLUMNS]]%NEWLINE%
                set INTERNAL_DIVIDER=1
        endiff

rem Output the message:
        echos %ANSI_SAVE_POSITION%%@ANSI_MOVE_TO[0,0]%LOCKED_MESSAGE_COLOR%
        echos %DIVIDER%%LOCKED_MESSAGE_COLOR%
        echos %SPACER%%dottie% %LOCKED_MESSAGE%%LOCKED_MESSAGE_COLOR% %dottie%%SPACER%%ANSI_EOL%%NEWLINE%
        echos %DIVIDER%%LOCKED_MESSAGE_COLOR%
        echos %ANSI_RESTORE_POSITION%%@CHAR[27]7%@CHAR[27][s%@CHAR[27][4;%[_rows]r%@CHAR[27]8%@CHAR[27][u
:END
