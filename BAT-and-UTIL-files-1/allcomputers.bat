@Echo off
 on break cancel

:DESCRIPTION:  will do the following command, for each machine in our environment: a <machinename> b c d e

rem TODO!
	call warning "This script has not been abstracted to use the ALL_COMPUTERS[_UP] environment variables. It may need to be modified with each new computer."
	rem PERHAPS COULD USE CODE LIKE THIS: for %computer in (%ALL_COMPUTERS_UP%) echo DRIVE_C_%computer% is %[DRIVE_C_%computer%]"


rem COMMAND-LINE PARAMTER BRANCHING:
    if "%1"==""  goto :usage
    if "%1"=="1" goto :MachineNameIsFirstArgument
                 goto :usage



rem MACHINE-SPECIFIC:
    :MachineNameIsFirstArgument
        if    "%HELL_DOWN%" ne "1" (%2 HELL    %3 %4 %5 %6 %7 %8 %9)
        if   "%MAGIC_DOWN%" ne "1" (%2 MAGIC   %3 %4 %5 %6 %7 %8 %9)
        if   "%STORM_DOWN%" ne "1" (%2 STORM   %3 %4 %5 %6 %7 %8 %9)
        if    "%MIST_DOWN%" ne "1" (%2 MIST    %3 %4 %5 %6 %7 %8 %9)
        if    "%FIRE_DOWN%" ne "1" (%2 FIRE    %3 %4 %5 %6 %7 %8 %9)
        if "%GOLIATH_DOWN%" ne "1" (%2 GOLIATH %3 %4 %5 %6 %7 %8 %9)
        if "%THAILOG_DOWN%" ne "1" (%2 THAILOG %3 %4 %5 %6 %7 %8 %9)
        if  "%DEMONA_DOWN%" ne "1" (%2 DEMONA  %3 %4 %5 %6 %7 %8 %9)
        if  "%WYVERN_DOWN%" ne "1" (%2 WYVERN  %3 %4 %5 %6 %7 %8 %9)
    goto :end

:usage
    %COLOR_ADVICE%
    echo allcomputers 1 a b c d e
    echo ... will do the following command, for each machine name in our environment: ...
    echo           a <machinename> b c d e
    echo     The "1" after allcomputers means the machinename is the first argument of each command (i.e. "a <machinename> b c d e")
    %COLOR_NORMAL%
goto :end

:end

