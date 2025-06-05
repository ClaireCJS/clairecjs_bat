@Echo Off
@on break cancel

set params=%1$

rem Validate environment (once):
        iff "1" != "%validated_delifexist%" then
                call validate-environment-variables MIN_RGB_VALUE_FG MAX_RGB_VALUE_FG MIN_RGB_VALUE_BG MAX_RGB_VALUE_BG
                set  validated_delifexist=1
        endiff


rem If it exists, delete it:
        iff isfile %* then
                rem Make each file deletion a random color so we can see where one ends and the other begins
                rem But not TRULY random of a color. Choose between colors in a tasteful, easily-visible threshold
                        rem This was the original function we used: echos %@randfg_soft[]  ``
                        rem But we manually expanded it so that there is not a dependency on the %@randfg_soft function existing
                                echos %@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m

                rem For extra safety, add the /p option if wildcards are involved
                        unset /q                         additional_del_if_later_opt
                        if "%@REGEX[\*,"%*"]" == "1" set additional_del_if_later_opt=/p

                rem Delete the file now that we know it exists:
                        *del /R /a: /Ns %params% %additional_del_if_later_opt% %*

        endiff
