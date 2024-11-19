@echo off
@on break cancel
set DEBUG_CALLER_ERRORLEVEL=1

set CATCHER=call errorlevel "my fail msg" "my success msg"   %+ cls    %+ color yellow on black 


realias                                                   

echo WITH alias: %+ which call                               %+  echo. %+ color green on black %+ echo. %+ echo.
    return-a-0.py %+ %CATCHER%                               %+ @echo. %+ color red   on black %+ echo. %+ echo.
    return-a-1.py %+ %CATCHER%


goto :END



    REM This section is to do an additional suite with the command unaliased. Not something we need to do usually.


            unalias call                                                 %+  echo. %+ pause %+ color yellow on black 

            echo WITHOUT alias: %+ which call                            %+  echo. %+           color green on black
                return-a-0.py %+ %CATCHER%                               %+ @echo. %+           color red   on black
                return-a-1.py %+ %CATCHER%



:END