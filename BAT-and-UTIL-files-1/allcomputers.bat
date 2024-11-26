@Echo off
 on break cancel

:DESCRIPTION: Performs a command with the machine name of every computer we have, as defined by the environment variable ALL_COMPUTERS
:USAGE:       allComputers 1 {word of command to appear before computer name} {words of commands to appear after computer name}
:EXAMPLE:     allComputers 1 echo is currently up
:USAGE:       can set ALL_COMPUTERS_EXCEPT_SELF=1 to run this on all computers except yourself


rem Validate environment:
        iff 1 ne %validated_allcomputers% then
                call validate-environment-variable ALL_COMPUTERS
                set  validated_allcomputers=1
        endiff
        
rem COMMAND-LINE PARAMETER BRANCHING:
    if "%1"==""  goto :usage
    if "%1"=="1" goto :Do_It
                 goto :usage



rem New code that doesn't need maintenance when new computer names come along:
    :Do_It
        for %%TmpMachineName in (%all_computers%) do (gosub doComputer %TmpMachineName%)
                goto :doComputerDone
                :doComputer [TmpMachineName]
                        set down=%[%TmpMachineName%_down]
                        
                        iff "%TmpMachineName%" eq "%MachineName%" then
                                set self=1
                        else
                                set self=0
                        endiff
                        
                        rem DEBUG: echo %down% -- %2 %TmpMachineName %3$
                        
                        iff 1 eq %self% .and. 1 eq %ALL_COMPUTERS_EXCEPT_SELF% then
                                echo Not performing on %TmpMachineName% because ALL_COMPUTERS_EXCEPT_SELF=%ALL_COMPUTERS_EXCEPT_SELF%
                        else                
                                if 1 ne %DOWN (echo %2 %TmpMachineName %3$)
                        endiff                        
                return              
                :doComputerDone
    goto :end
rem Old code that needed maintenance when new computer names came along::
    :Do_It_OLD
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
    echo USAGE: allcomputers 1 {set of commands, i.e. word1 word2 word3 word4}
    echo.
    echo ... will do the following command, for each machine name in our environment: ...
    echo           a {machinename} b c d e
    echo.
    echo     The "1" is a sanity parameter to prevent destructive behavior.
    echo.
    echo So for example if you wanted to echo every machinename, you could do:
    echo.
    echo.       allComputers 1 echo
    echo.
    echo which would decompose into "echo thailog", "echo demona", "echo mist",e tc, for whatever your computer name are.
    echo.
    echo.
    %COLOR_NORMAL%
goto :end

:end

