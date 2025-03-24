@Echo Off
@loadbtm on

rem 🧹Pre-run clean-up:
        if defined eset_fail unset /q eset_fail

rem 🔍Validate environment, but only once:
        iff "1" != "%ESET_VALIDATED_2%" then
                call validate-environment-variables EMOJI_PENCIL ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING ANSI_COLOR_PROMPT ANSI_COLOR_NORMAL CURSOR_RESET ansi_color_warning underline_on underline_off italics_on italics_off color_advice color_normal blink_on  blink_off emoji_warning ansi_color_important_less faint_on faint_off ansi_color_important
                call validate-is-function           CURSOR_COLOR
                call validate-in-path               eset divider echos beep.bat clear-buffered-keystrokes
                set ESET_VALIDATED_2=1
        endiff

rem 📪Did we get a command-line parameter?
        iff "%1" eq "" then
                %color_advice%
                                echos %ANSI_COLOR_WARNING%Must provide a %underline_on%variable name%underline_off% to %italics_on%eset%italics_on%!
                %color_normal%
                goto :actual_eset
        else
                set CMD_TAIL=%*
                if "%2" == "quick" set CMD_TAIL=%1 %3$
        endiff

rem ➕Implement our /p option to prompt the user:
        iff "%2" eq "/p" then       
                set varname=%1
                set CMD_TAIL=%1 %3$
                echo %ansi_color_important_less%%emoji_warning% Please edit the value of %faint_on%'%faint_off%%ansi_color_important%%italics_on%%varname%%ansi_color_important_less%%faint_on%'%faint_off%:
                echos %BIG_OFF%
        endiff
        

rem 🔊Gentle audio prompt —— the lowest audible beep and the shortest duration —— to grab user attention:
        if "%2" != "quick" call beep.bat lowest 1

rem 🔎Make sure the variable actually exists:
        if not defined %1 .and. "%1" != "/?" (set %1=?>&>nul)

rem 💄Purely cosmetic:
        if "%1" eq "/?" (call divider)

rem ✏Emojify✏ & 🏳‍🌈colorfy🏳 the prompt, and change the cursor⬜ to the largest blinkiest bright yellow🟨 —— to grab user attention:
        echos %EMOJI_PENCIL%%@CURSOR_COLOR[yellow]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%%ANSI_COLOR_PROMPT% ``

rem Clear the keybaord buffer...
        rem still necessarily even in quick mode, unfortunately: if "%2" != "quick"
        call clear-buffered-keystrokes %2$

rem 📴Turn ANSI rendering off or things will get crazy:
rem 🔨Do the actual eset command:
        :actual_eset
                echos %BIG_OFF%
                if "%2" != "quick" call ansi-off
                on break set eset_fail=1
                *eset %CMD_TAIL%
                if "%2" != "quick" .and. "1" == "%ansi_off%"  call ansi-on
                on break cancel
 
rem 🔛Turn ANSI rendering and Ctrl-Break handling back to normal:
        if "1" == "%eset_fail%" goto :END

rem 📰Remind user of our extra options:
        iff "%1" eq "" .or. "%1" eq "/?" then
                                call divider
                                        echos %ansi_color_important%
                                        echo ➕%blink_on%EXTRA OPTIONS%blink_off%:
                                        echo.     
                                        echo        /p = Give a basic prompt using the environment variable's name%ansi_color_important_less%
                                        echo             EXAMPLE: %0 varname /p             
                                call divider
                %color_normal%
        endiff

rem ✅Reset the color & cursor back to normal:
        :END
       on break cancel
       echos %ANSI_COLOR_NORMAL%%CURSOR_RESET%
       if "1" == "%ansi_off%"  call ansi-on
       if "1" == "%eset_fail%" quit 667


 