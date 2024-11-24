@Echo Off

call validate-environment-variables MIN_RGB_VALUE_FG MAX_RGB_VALUE_FG MIN_RGB_VALUE_BG MAX_RGB_VALUE_BG

 on break cancel
iff exist %* then
    rem Make it pretty:
            rem echos %@randfg_soft[]  ``
            echos %@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m

    rem Delete the file now that we know it exists:
            *del /R %*

    rem If we were paranoid:
            rem if "%@REGEX[\*,%*]" set == "1" OPT=/p
            rem set OPT=
            rem *del %OPT% %*
endiff