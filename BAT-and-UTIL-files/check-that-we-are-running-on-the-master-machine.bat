@Echo OFF

:DESCRIPTION: Breaks execution of all scripting if we are not on our master machine. Used to control authority and script distribution.


rem VALIDATE ENVIRONMENT:
        call validate-environment-variables MASTERMACHINE MACHINENAME


rem IF WE ARE ON THE MASTER MACHINE, EXIT PEACEFULLY:
        if "%@UPPER[%MASTERMACHINE]" eq "%@UPPER[%MACHINENAME]" (goto :Everything_Is_Okay)



rem IF WE ARE NOT, SOUND THE ALARM!
        call fatal_error "This script can only be run on %blink_on%%MASTERMACHINE%%blink_off%"
        CANCEL          %+ REM       Stops all batch processing, even the bat file that called this one. Fatal_error should already do this, but we'll do it again here just in case.



:Everything_Is_Okay
