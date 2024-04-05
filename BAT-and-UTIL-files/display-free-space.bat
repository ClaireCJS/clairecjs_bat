@Echo off

set MESSAGE_TYPE=success

rem Add help parameters:
        call check-if-asking-for-usage.bat %*
        if %ASKING_FOR_USAGE eq 1 (
                %color_advice%
                    rem echos %ANSI_COLOR_RESET%...%ANSI_CLEAR_TO_EOL%
                    echos %ANSI_COLOR_ADVICE%%ANSI_CLEAR_TO_EOL%
                    echo.
                    call bigecho %ANSI_COLOR_ADVICE%%STAR% %double_underline%USAGE%double_underline_off%:%@ANSI_bg[0,0,0]%ANSI_COLOR_ADVICE%%ansi_erase_to_eol%
                    echos %ANSI_COLOR_ADVICE%%ANSI_CLEAR_TO_EOL%
                    echo.
                    echo %0 {location}    - displays %underline_on%free space%underline_off%  at   the%italics_on% location  %italics_off%specified                 %faint_on%(can be drive/folder)%faint_off%%ansi_erase_to_eol%
                    echo %0               - displays %underline_on%free space%underline_off% using the%italics_on%  default  %italics_off%message type of %[ANSI_COLOR_%MESSAGE_TYPE%]%italics_on%%MESSAGE_TYPE%%italics_off%%ANSI_COLOR_ADVICE%   %faint_on%(in the current location)%faint_off%%ansi_erase_to_eol%
                    call gather-message-types-into-pretty-environment-variable
                    call validate-environment-variable MESSAGE_TYPES_PRETTY
                    echo %ansi_color_advice%%0 {messagetype} - displays %underline_on%free space%underline_off% using the%italics_on% specified %italics_off%message type              %faint_on%(must be one of the ones below)%faint_off%%ansi_erase_to_eol%
                    echo                                    %emphasis%messages types%deemphasis%: %MESSAGE_TYPES_PRETTY%%ANSI_COLOR_ADVICE%
                    echo %0 {location} {messagetype} - How to combine different location %italics%and%italics_off% message type at once%ansi_erase_to_eol%
                %color_normal%
            goto :END
        )



rem Process paramters:
    if "%2" eq "" (
            rem if we give 1 arg, it could be either a message type or drive letter with or without a colon after it:
                    if 1 eq %@REGEX[:,%1] .or. 1 eq %@LEN[%1] (
                        set DISPLAY_FREE_SPACE_TARGET=%1
                    ) else (
                        set MESSAGE_TYPE=%1
                    )
    ) else (
            rem if we give 2 args, the first should be the location, and the 2nd the message type:
                    set DISPLAY_FREE_SPACE_TARGET=%1
                    set MESSAGE_TYPE=%2
    )


rem Validate parameters:
        if 0 eq %@READY[%DISPLAY_FREE_SPACE_TARGET%] (call error "Does not exist: '%italics_on%%DISPLAY_FREE_SPACE_TARGET%%italics_off%'" %+ goto :END)


rem Get the free space and print it out
        set DISKFREE=%ansi_color_error%%blink%ERROR
        set DISKFREE=%@COMMA[%@EVAL[%@DISKFREE[%DISPLAY_FREE_SPACE_TARGET%]/1024/1024/1024]]
        call print-message %MESSAGE_TYPE% "Free space now %DISKFREE%"

rem a Warning if space is low?
        if %@DISKFREE[%SYNCTARGET%] lt 150000000 (set NEWLINE_REPLACEMENT=0 %+ repeat 3 (beep 60 25 %+ beep 800 3) %+ call WARNING "Not much free space left on %SYNCTARGET%!" %+ pause 3000 )


:END

