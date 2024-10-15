@echo off

if not exist %1 goto :DNE1
%COLOR_IMPORTANT% %+ echo *** Validating %1: 
%COLOR_RUN% 
(c:\perl\bin\perl.exe %BAT%\validate-filelist.pl) <%1 
: cut-to-width




goto :END


    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :DNE1
        echo ERROR: %1 does not exist!
    goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
%COLOR_NORMAL%
