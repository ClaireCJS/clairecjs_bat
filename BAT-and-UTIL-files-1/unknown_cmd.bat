@*Echo OFF
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
*set PARAMS=%*
*setdos /x0 
*set PAUSE_WINDOW_TITLE=❌ ERR: %1$ ❌ 
*set old_title=%_TITLE
*if "" != "%PAUSE_WINDOW_TITLE%" *title %PAUSE_WINDOW_TITLE%
*echos %ansi_color_normal%
*echoserr %ansi_color_normal%
*echoerr 🚩 %ANSI_COLOR_ERROR% Unknown command: '%italics%%ANSI_BRIGHT_YELLOW%%1$%ANSI_COLOR_ERROR%%italics_off%' %@unquote[%@IF["" != "%_PBATCHNAME","%ANSI_BACKGROUND_BLACK% in %italics%%[_PBATCHNAME]%italics_off%",]]%ANSI_RESET% 🚩 
*beep
*if "" != "%PARAMS%" (
        set msg=%ansi_color_warning%Pausing to allow time for this error to be discovered, but not stopping...%ansi_color_normal%%ansi_background_black%%ansi_color_bright_red%
        if "" != "%@search[pause-for-x-seconds]" (
                call pause-for-x-seconds 600 "%msg%"
        ) else (
                *echo %msg%
                *pause                
        )
)
*echos %ansi_color_normal%
*if "" != "%old_title%" *title %old_title%
rem echo %_PBATCHNAME !
