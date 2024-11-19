@Echo OFF
 on break cancel
iff exist %* then
    rem Make it pretty:
            echos %@randfg_soft[]  ``

    rem Delete the file now that we know it exists:
            *del /R %*

    rem If we were paranoid:
            rem if "%@REGEX[\*,%*]" set == "1" OPT=/p
            rem set OPT=
            rem *del %OPT% %*
endiff