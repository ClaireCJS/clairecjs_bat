@loadbtm on
@Echo OFF
@on break cancel

    
REM old, called the bat file repeatedly which created overhead
        REM for %ee in (%*) do (call c:\bat\validate-environment-variable %ee)

REM new, relies on the VALIDATE_MULTIPLE flag to do the loop internally in validate-environment-variable.bat to reduce overhead
        set  VALIDATE_MULTIPLE_PLUGINS=1
        call validate-plugin %*
        set  VALIDATE_MULTIPLE_PLUGINS=0
