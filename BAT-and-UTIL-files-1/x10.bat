@Echo OFF
:original bat moved to x10-index.bat

::::: DOCUMENTATION:
		:echo x10 [A1%=|A2%=|A3...] [on%=|off%=|dim 100%=|bright 100]
		:echo x10 A [allunitsoff, AllLightsOn]
        ::::: NOTE: IF THERE ARE PROBLEMS, YOU MAY NEED TO INSTALL THE ACTIVEHOMEPRO SDK!


::::: SETUP (variables are validated later):
	:set X10=%UTIL%\ahcmd.exe
	 set X10=%UTIL%\x10cmd.exe
	:set STANDARDWAITINMS=400
	:set STANDARDWAITINMS=50
	 set STANDARDWAITINMS=225


::::: GRAB COMMAND-LINE PARAMETERS:
    set CODE=%1
    SET STATUS=%2                                                                    %+ rem ECHO 1=%1, 2=%2, status=%status%
    if "%STATUS%" eq "of"   (set STATUS=OFF)                                         %+ rem //Typo protection
    if "%STATUS%" eq "offf" (set STATUS=OFF)                                         %+ rem //Typo protection
    if "%STATUS%" eq "onn"  (set STATUS=ON )                                         %+ rem //Typo protection
	set PAYLOAD=%CODE% %STATUS%                                                      %+ rem ECHO 1=%1, 2=%2, status=%status%

::::: VALIDATE ENVIRONMENT/PARAMETERS:
    if "%VALIDATED_X10_BAT%" eq "1" goto :Validated
        call validate-environment-variables X10 StandardWaitInMS Code status payload MachineName X10_Server
        set VALIDATED_X10_BAT=1
    :Validated

    
    
::::: IS THIS MACHINE EVEN CAPABLE OF DOING THIS?
    if "%MACHINENAME%" eq "%X10_SERVER%" (goto :DoIt)
    call unimportant "This computer is not X10 capable, so %CODE% was NOT set to %STATUS%."
    goto :Past_X10_Command_Being_Run




::::: TRACK THE STATE CHANGE VIA ENVIRONMENT VARIABLES {FOR WHAT IT'S WORTH}:
    if "%STATUS%" eq "on" .or. "%STATUS%" eq "off" (set X10_STATE_%@UPPER[%CODE%]=%@UPPER[%STATUS%])



::::: SEND THE COMMAND:
    :DoIt
    unset /q X10DOWNORNOTHANDLER
    if "%X10_DOWN%" eq "1" goto :X10_DOWN_YES
                           goto :X10_DOWN_NO
        :X10_DOWN_YES
            set X10DOWNORNOTHANDLER=echo X10 DOWN. NOT DOING: 
        :X10_DOWN_NO
            %COLOR_DEBUG% %+ echos - [x10] [sendplc %PAYLOAD%] `` %+ %COLOR_RUN%    %+ %X10DOWNORNOTHANDLER% %X10% sendplc %PAYLOAD% %+ *delay /m %STANDARDWAITINMS%   
            %COLOR_DEBUG% %+ echos - [x10] [sendrf  %PAYLOAD%] `` %+ %COLOR_NORMAL% %+ %X10DOWNORNOTHANDLER% %X10% sendrf  %PAYLOAD% %+ *delay /m %STANDARDWAITINMS%   
    :Past_X10_Command_Being_Run

:END
