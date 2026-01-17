@loadbtm on
@echo off
@on break cancel

rem Validate environment:
        iff "1" != "%validated-valfilelist%" then
                call validate-in-path perl validate-filelist.pl
                set  validated-valfilelist=1
        endiff

rem Validate parameters:
        if not exist %1 goto :DNE1
        %COLOR_IMPORTANT% %+ echo *** Validating %1: 
        %COLOR_RUN% 


rem Run it:
(perl %BAT%\validate-filelist.pl) <%1 
: cut-to-width




goto :END


    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :DNE1
        echo ERROR: %1 does not exist!
    goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
%COLOR_NORMAL%
