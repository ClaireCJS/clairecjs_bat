@Echo Off
 echo.



rem Validate our environment:
        if not "1" == "%VALIDATED_DISPLAYDRIVESBYCOMPUTER%" (
                call validate-environment-variables MACHINENAME DRIVES_%MACHINENAME% MAX_MACHINENAME_LENGTH THE_ALPHABET EMOJI_COMPUTER_DISK BOLD_ON BOLD_OFF ITALICS_ON ITALICS_OFF NEWLINE BIG_TOP BIG_BOT ANSI_COLOR_IMPORTANT
                call validate-in-path               highlight-by-computer-name
                set VALIDATED_DISPLAYDRIVESBYCOMPUTER=1
        )
   

rem Report on the drives on our current machine, then do all the other ones:
                                                              gosub TellForMachine %MACHINENAME%
        for %ma in (%ALL_COMPUTERS%) if %ma ne %MACHINENAME% (gosub TellForMachine %ma%)

        


goto :END
    :TellForMachine [MACHINENAME]
        rem Get drives for that machine [defined in environm.btm]
                SET DRIVES=%[DRIVES_%MACHINENAME%]

        rem Make each letter in the list a random color [using our randFG function in set-colors.bat]
                for %tmp_letter in (%THE_ALPHABET) (set DRIVES=%%@REREPLACE[(%tmp_letter),%@randFG[]\1,%DRIVES])

        rem Create the line of output for the machinename in question
                unset /q stuff
                SET STUFF=%STUFF%%ANSI_RESET%%EMOJI_COMPUTER_DISK% %BOLD_OFF%%ANSI_COLOR_IMPORTANT%Drives for %@FORMAT[-%MAX_MACHINENAME_LENGTH%,%MACHINENAME%] %ANSI_COLOR_IMPORTANT%are: %ITALICS_ON%%BOLD_ON%%DRIVES%%BOLD_OFF%%ITALICS_OFF% %NEWLINE% 

        rem Pass the double-height text through our script that adds the emoji for each machine 
        rem [defined in environm.btm] next to any mention of it:
                echos %BIG_TOP%%STUFF%%BIG_BOT%%STUFF% |:u8 call highlight-by-computer-name
    return
:END
