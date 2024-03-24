@Echo Off
 echo.

call validate-environment-variables MACHINENAME DRIVES_%MACHINENAME% MAX_MACHINENAME_LENGTH

set STUFF=
%COLOR_IMPORTANT% %+                                                       gosub TellForMachine %MACHINENAME%
%COLOR_SUBTLE%    %+ for %ma in (%ALL_COMPUTERS%) if %ma ne %MACHINENAME% (gosub TellForMachine %ma%)
echo %STUFF% |:u8 call highlight-by-computer-name

goto :END
    :TellForMachine [MACHINENAME]
        SET STUFF=%STUFF%%ANSI_RESET%%EMOJI_COMPUTER_DISK% %BOLD_OFF%Drives for %@FORMAT[-%MAX_MACHINENAME_LENGTH%,%MACHINENAME%] are: %ITALICS_ON%%BOLD_ON%%[DRIVES_%MACHINENAME%]%BOLD_OFF%%ITALICS_OFF% %NEWLINE% 
    return
:END
