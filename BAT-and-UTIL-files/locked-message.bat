@Echo off

:USAGE: locked-message {no arguments} - Will lock the upper rows of the screen with a message, which defaults a report of free space
:USAGE: locked-message "Hello precious" - locked message of specific text


rem Validate the environment:
        if 1 ne %VALIDATED_LOCKED_MESSAGE_BAT% (
                call validate-environment-variables PLUGIN_STRIPANSI_LOADED ANSI_UNLOCK_MARGINS ANSI_SAVE_POSITION ANSI_RESTORE_POSITION ANSI_EOL NEWLINE CONNECTING_EQUALS BLINK_ON BLINK_OFF DOT ANSI_COLOR_ERROR
                set VALIDATED_LOCKED_MESSAGE_BAT=1
        )

rem Set message background color & divider:
        set LOCKED_MESSAGE_COLOR_BG=%@ANSI_BG[0,0,64]
        set LOCKED_MESSAGE_COLOR=%ANSI_COLOR_IMPORTANT%%LOCKED_MESSAGE_COLOR_BG%
        set DIVIDER=%@REPEAT[%CONNECTING_EQUALS,%@EVAL[%_COLUMNS]]
        set DOTTIE=%BLINK_ON%%DOT%%BLINK_OFF%
        rem TOO SLOW: call echo-rainbow generate %DIVIDER% %+ set DIVIDER=%RAINBOW_TEXT%

rem Set free space stuffs:
        set CWDTMP=%_CWD
        set LM_BY_DRIVE=0
        if "%1" ne "" .and. %@LEN[%1] eq 1 (
            set CWDTMP=%1: 
            set LM_BY_DRIVE=1
            if 0 eq %@READY[%1] (set LOCKED_MESSAGE=%ANSI_COLOR_ERROR%Drive %1: is not ready %+ goto :Display_Message_Now)
        )
        rem DEBUG: echo %blink%CWDTMP is %CWDTMP%%blink_off%
        set DF=%@DISKFREE[%CWDTMP]
        set FREE_MEGS=%@COMMA[%@FLOOR[%@EVAL[%DF%/1024/1024]]]
        set FREE_GIGS=%@COMMA[%@FORMATN[.2,%@EVAL[%DF%/1024/1024/1024]]]
        set FREE_TERA=%@FORMATN[.2,%@EVAL[%DF%/1024/1024/1024/1024]]

rem Create message text:
        set OUR_SLASH=%bold_on%/%bold_off%
        SET LOCKED_MESSAGE=%bold_on%%FREE_MEGS%%bold_off% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%M %our_slash% %locked_message_color%%FREE_GIGS% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%G
        if %FREE_GIGS gt 1000 (set LOCKED_MESSAGE=%LOCKED_MESSAGE%%locked_message_color% %our_slash% %FREE_tera% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%T)
        set LOCKED_MESSAGE=%LOCKED_MESSAGE% %italics_on%free%italics_off% on %bold_on%%@UPPER[%@INSTR[0,2,%CWDTMP]]%bold_off%%LOCKED_MESSAGE_COLOR%

rem Respond to command-line parameters:
        rem if "%1" ne "" .and. %LM_LETTER_GIVEN eq 0 (set LOCKED_MESSAGE=%@UNQUOTE[%1$])
        set LOCKED_MESSAGE=%@UNQUOTE[%LOCKED_MESSAGE]

rem Respond to environment-variable parameters:
        if defined DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE (
            set LOCKED_MESSAGE=%LOCKED_MESSAGE%%DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE%
            unset /q DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE
        )

rem Get message length and create side-spacers of appropriate length to center the message:
        :Display_Message_Now
        SET LOCKED_MESSAGE_LENGTH=%@LEN[%@STRIP_ANSI[%LOCKED_MESSAGE]]
        set SPACER=%@REPEAT[ ,%@FLOOR[%@EVAL[(%_COLUMNS-%LOCKED_MESSAGE_LENGTH-3)/2]]]``

rem Output the message:
        echos %ANSI_SAVE_POSITION%%@ANSI_MOVE_TO[0,0]%LOCKED_MESSAGE_COLOR%%DIVIDER%%NEWLINE%%SPACER%%dottie% %LOCKED_MESSAGE%%LOCKED_MESSAGE_COLOR% %dottie%%SPACER%%ANSI_EOL%%NEWLINE%%DIVIDER%%ANSI_RESTORE_POSITION%%@CHAR[27]7%@CHAR[27][s%@CHAR[27][4;%[_rows]r%@CHAR[27]8%@CHAR[27][u

