@Echo OFF
@loadbtm on

rem Validate environment (once):
        setdos /x0
        iff 1 ne %validated_stDfCmdSepChar% then
                call validate-environment-variable DEFAULT_COMMAND_SEPARATOR_CHARACTER DEFAULT_COMMAND_SEPARATOR_DESCRIPTION
                set  validated_stDfCmdSepChar=1 
        endiff        

rem Set the command separator to the default one defined in environm.btm:
        @*setdos /x0                                                     
        @*setdos /x-5                                                    
        @*setdos /c%DEFAULT_COMMAND_SEPARATOR_CHARACTER%                 
        @*set COMMAND_SEPARATOR=%DEFAULT_COMMAND_SEPARATOR_DESCRIPTION%              
        @*setdos /x0                                                     
