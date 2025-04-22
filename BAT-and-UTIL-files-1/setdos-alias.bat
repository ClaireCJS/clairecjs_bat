@echo off

if "%1" ==  ""  (goto :help)
if "%1" == "/h" (goto :help)
if "%1" == "/?" (goto :help)

goto :end
                :help
                        echo.
                        %color_advice%
                        echo *setdos /cA  %EMdash% set %blink_on%command separator character%blink_off% to “A” %faint_on%{or whatever}%faint_off%
                        echo *setdos /eA  %EMdash% set            %blink_on%escape character%blink_off% to “A” %faint_on%{or whatever}%faint_off%
                        echo.
                        echo *setdos /x-1 %EMdash% All alias expansion 
                        echo *setdos /x-2 %EMdash% Nested alias expansion only 
                        echo *setdos /x-3 %EMdash% All variable expansion (includes environment variables, batch file parameters, variable function evaluation, and alias parameters) 
                        echo *setdos /x-4 %EMdash% Nested variable expansion only  
                        echo *setdos /x-5 %EMdash% Multiple commands, conditional commands, piping, and %blink_on%command separator%blink_off%
                        echo *setdos /x-6 %EMdash% Redirection 
                        echo *setdos /x-7 %EMdash% Quoting (affects back-quotes and double quotes and square brackets) 
                        echo *setdos /x-8 %EMdash% %blink_on%Escape character%blink_off%
                        echo *setdos /x-9 %EMdash% Include lists (to allow semicolons in filenames)
                        echo.
                            echos ...followed by:  ``
                                    %color_important%
                                        echos %italics_on%setdos /x0%italics_off% 
                                    %color_advice%
                            echo  to reset
                    %color_normal%
                        echo.
                goto :end

:end

set last_setdos_command=*setdos %*

*setdos %*
