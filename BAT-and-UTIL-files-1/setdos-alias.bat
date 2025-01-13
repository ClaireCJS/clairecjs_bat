@echo off

if "%1" == "" .or. "%1" == "/h" .or. "%1" == "/?" (goto :help)

goto :end
                :help
                        echo.
                        %color_advice%
                        echo setdos /x-1 %EMdash% All alias expansion 
                        echo setdos /x-2 %EMdash% Nested alias expansion only 
                        echo setdos /x-3 %EMdash% All variable expansion (includes environment variables, batch file parameters, variable function evaluation, and alias parameters) 
                        echo setdos /x-4 %EMdash% Nested variable expansion only  
                        echo setdos /x-5 %EMdash% Multiple commands, conditional commands, piping, and %blink_on%command separator%blink_off%
                        echo setdos /x-6 %EMdash% Redirection 
                        echo setdos /x-7 %EMdash% Quoting (affects back-quotes and double quotes and square brackets) 
                        echo setdos /x-8 %EMdash% Escape character 
                        echo setdos /x-9 %EMdash% Include lists (to allow semicolons in filenames)
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

*setdos %*
