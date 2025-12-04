@loadbtm on
@Echo OFF
@on break cancel




rem USAGE:
        if "%1" == "" goto :Usage

rem Validate environment:
        iff "2" != "%validated_askmv%" then
                call validate-in-path               move mv warning 
                call validate-environment-variables colors_have_been_set emoji_have_been_set escape_character
                set  validated_askmv=2
        endiff




rem PARAMETER PARSING:
        rem Parsing out parameters to validate would be laborious. We will let the errors fall to the 
        rem command we are invoking rather than attempting to detect them here, which is unrealistic
        set COMMAND=%*


rem Convert “” to "", because “” is our cute way of passing "":
        unset /q CONVERTED_COMMAND
        set CONVERTED_COMMAND=%@ReReplace[[“”],%escape_character%\Q,%COMMAND%]



rem Ask:
        echo.
        echo %ansi_color_less_important% %star%           COMMAND: %COMMAND%
        echo %ansi_color_less_important% %star% CONVERTED_COMMAND: %CONVERTED_COMMAND%
        call AskYN "Run command" yes 0


rem Check answer:
        if "%ANSWER%" != "Y" goto :Refuse

rem Actually do the command:
        set LAST_COMMAND=%CONVERTED_COMMAND%        
                         %CONVERTED_COMMAND%




goto :END
                        
                :Usage
                        echo.
                        %color_advice%
                        USAGE:   ask-command {command}
                        echo.
                        EXAMPLE #1: ask-command mv *.bak        c:\recycled - moves everything to recycled, but only after asking
                        EXAMPLE #2: ask-command mv “* hi *.bak” c:\recycled - use smart quotes to pass commands with actual quotes
                        echo.
                        USAGE: ask-mv c:\*.txt d:\ 
                        %color_normal%
                        echo.
                goto :END

                :Refuse
                        echo.
                        call warning "Not executing command because we answered “No”" silent
                goto :END


:END

