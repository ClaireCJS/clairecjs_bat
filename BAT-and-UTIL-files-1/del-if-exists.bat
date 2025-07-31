@Echo Off
@on break cancel

set params=%1$

rem Validate environment (once):
        iff "2" != "%validated_delifexist%" then
                call validate-environment-variables MIN_RGB_VALUE_FG MAX_RGB_VALUE_FG MIN_RGB_VALUE_BG MAX_RGB_VALUE_BG ansi_colors_have_been_set emoji_have_been_set
                set  validated_delifexist=2
        endiff


rem Deal with parameters:
        unset /q params
        :postshift
        set file_to_check=%@UNQUOTE["%1"]
        rem  call debug "file_to_check is now %file_to_check%"
        iff "%@LEFt[1,%file_to_check%]" == "/" then
                set params=%params% %file_to_check%
                shift
                goto :postshift
        endiff


rem If it exists, delete it:
        rem DEBUG: echo - DEBUG: iff isfile "%file_to_check%" then ... [params=%params%]
        iff isfile "%file_to_check%" then
                rem Make each file deletion a random color so we can see where one ends and the other begins
                rem But not TRULY random of a color. Choose between colors in a tasteful, easily-visible threshold
                        rem This was the original function we used: echos %@randfg_soft[]  ``
                        rem But we manually expanded it so that there is not a dependency on the %@randfg_soft function existing
                                echos %@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m

                rem For extra safety, add the /p option if wildcards are involved
                        unset /q                                      additional_del_if_later_opt
                        rem %@REGEX[\*,"%*"]"              == "1" set additional_del_if_later_opt=/p
                        if "%@REGEX[\*,"%file_to_check%"]" == "1" set additional_del_if_later_opt=/p

                rem Delete the file now that we know it exists:
                        rem DEBUG: echo *del /R /a: /Ns %params% %additional_del_if_later_opt% "%file_to_check%"
                        echos %@ansi_move_left[2]                %emoji_axe% ``
                             *del /R /a: /Ns %params% %additional_del_if_later_opt% "%file_to_check%"

        endiff
