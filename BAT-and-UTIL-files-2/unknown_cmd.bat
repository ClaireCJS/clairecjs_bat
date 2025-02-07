@*Echo OFF
@setdos /x0

*rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ DEFINE ANSI: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*if not defined ansi_background_black set ansi_background_black=%@CHAR[27][40m
*if not defined ansi_color_bright_red set ansi_color_bright_red=%@CHAR[27][91m
*if not defined ansi_color_error      set ansi_color_error=%@CHAR[27][39m%@CHAR[27][49m%@CHAR[27][0m%@CHAR[27][97m%@CHAR[27][41m
*if not defined ansi_color_normal     set ansi_color_normal=%@CHAR[27][39m%@CHAR[27][49m%@CHAR[27][0m
*if not defined ansi_color_warning    set ansi_color_warning=%@CHAR[27][39m%@CHAR[27][49m%@CHAR[27][0m%@CHAR[27][93m%@CHAR[27][44m
*if not defined ansi_reset            set ansi_reset=%@CHAR[27][39m%@CHAR[27][49m%@CHAR[27][0m
*if not defined ansi_bright_yellow    set ansi_bright_yellow=%@CHAR[27][93m
*if not defined ansi_yellow           set ansi_yellow=%@CHAR[27][33m
*if not defined italics               set italics=%@CHAR[27][3m
*if not defined italics_off           set italics_off=%@CHAR[27][23m
*rem todo blink on/off
*rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ CONFIGURATION: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*set unknown_command_highlight_color=
*set wait_time_for_unknown_commands=9999 %+ rem I want 43200 for 12 hours, but TCC v33 seemingly has max of 9999 

*rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PARAMETER PROCESSING: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*set PARAMS=%*
*iff "%1" == "BATCHLINE" then
        shift
        set BATCHLINE=%1
        shift   
*else
        unset /q BATCHLINE
*endiff

*rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ WINDOW TITLEING: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*set PAUSE_WINDOW_TITLE=❌ ERR: %1$ ❌ 
*set old_title=%_TITLE
*if "" != "%PAUSE_WINDOW_TITLE%" *title %PAUSE_WINDOW_TITLE%

*rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━ OUTPUT ERROR MESSAGE: ━━━━━━━━━━━━━━━━━━━━━━━━━━
*echoerr.
*echos %ansi_color_normal%
*echoserr %ansi_color_normal%
*echoerr 🚩 %ANSI_COLOR_ERROR% Unknown command: %blink_on%“%blink_off%%italics%%unknown_command_highlight_color%%1$%ANSI_COLOR_ERROR%%italics_off%%blink_on%”%blink_off% %@unquote[%@IF["" != "%_PBATCHNAME","%ANSI_BACKGROUND_BLACK% in %italics%%[_PBATCHNAME]%italics_off%",]]%ANSI_RESET% 🚩 
*if defined BATCHLINE .and. "%BATCHLINE%" != "-1" *echoerr 🚩 %ANSI_COLOR_ERROR% Line number: %italics%%unknown_command_highlight_color%%BATCHLINE%%ANSI_COLOR_ERROR%%italics_off%
*beep

*rem ━━━━━━━━━━━━━━━━━━━━━ HALT EXECUTION UNTIL ACKNOWLEDGED: ━━━━━━━━━━━━━━━━━━━━━
*if "" != "%PARAMS%" (
        set msg=%ansi_color_warning%Pausing to allow time for this error to be discovered, but %italics_on%not%italics_off% stopping...%ansi_color_normal%%ansi_background_black%%ansi_color_bright_red%
        if "" != "%@search[pause-for-x-seconds]" .and. defined wait_time_for_unknown_commands (
                call pause-for-x-seconds %wait_time_for_unknown_commands% "%msg%"
        ) else (
                *echo %msg%
                *pause                
        )
)


*rem ━━━━━━━━━━━━━━━━━━━━━ PUT EVERYTHING BACK TO NORMAL: ━━━━━━━━━━━━━━━━━━━━━
*echos %ansi_color_normal%
*if "" != "%old_title%" *title %old_title%
rem echo %_PBATCHNAME !
