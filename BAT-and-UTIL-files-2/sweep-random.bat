@loadbtm on
@echo Off

rem Validate environment (once):
        iff "2" != "%validated_sweeprandom1%" then
                call validate-in-path insert-before-each-line.py insert-after-each-line.py less_important advice print-message randomize-file run-piped-input-as-bat set-tmp-file cd-for-sweep-random.bat less_important print-message
                call validate-environment-variables lq rq bold_on bold_off faint_on faint_off ansi_color_warning_soft color_advice color_normal italics_on italics_off
                set  validated_sweeprandom1=2
        endiff

rem Get parameters:
        set COMMAND=%1
        iff "%1" == "" then
                %color_advice%
                echo USAGE: Put the command you want to sweep in quotes, i.e.: 
                echo        %0 "dir" 
                echo.
                echo USAGE: To force it after the above dry run:
                echo        %0 "dir" force
                %color_normal%
                goto :END
        endiff
        echo %ansi_color_warning_soft%%star% command to randomly walk through folders is: %bold_on%%bold_off%%faint_on%%italics_on%%@unquote[%command%]%italics_off%%faint_off%%bold_on%%bold_off%%ansi_color_normal%

rem Force?
        iff "force" == "%2" then
                set PRECOMMAND=
                set SR_FORCE=1
        else
                set PRECOMMAND=echo ``
                set SR_FORCE=0
        endiff
        rem echo 🐐 GOAT 🐐 Tracer #QQ1 >nul

rem Advice for force:
        if "1" != "%SR_FORCE%" (call less_important "Dry run:")
        rem echo 🐐 GOAT 🐐 Tracer #QQ2

rem Run command in current folder:
        rem echo 🐐 GOAT 🐐 Tracer #QQ3 ━━ doing root >nul
        call cd-for-sweep-random .
        %PRECOMMAND% %@UNQUOTE["%COMMAND%"]

rem Run command in every subfolder, but randomly, by generating a script:
        rem echo 🐐 GOAT 🐐 Tracer #QQ4 ━━ doing rest >nul
        call set-tmp-file
        rem (dir /a:d /s /b |:u8 randomize-file |:u8 insert-before-each-line.py              "*cd                  {{{{QUOTE}}}}" |:u8 insert-after-each-line.py "{{{{QUOTE}}}} {{{{PERCENT}}}}+ %PRECOMMAND% %@UNQUOTE["%COMMAND%"]" ) 
            (dir /a:d /s /b |:u8 randomize-file |:u8 insert-before-each-line.py "echo. %+ call cd-for-sweep-random {{{{QUOTE}}}}" |:u8 insert-after-each-line.py "{{{{QUOTE}}}} {{{{PERCENT}}}}+ %PRECOMMAND% %@UNQUOTE["%COMMAND%"]" ) >:u8%tmpfile%.bat
        pushd .

        rem DEBUG:        type %tmpfile%.bat %+ pause

rem Run the script to run the command in every subfolder randomly:                
        call %tmpfile%.bat
        popd

rem Advice for force:
        if 1 ne %SR_FORCE% (call advice "Add “force” as 2ⁿᵈ argument to run this")

:END
