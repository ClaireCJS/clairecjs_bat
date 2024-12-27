@Echo OFF

rem Validate environment (once):
        iff 1 ne %validated_stDfCmdSepChar% then
                call validate-envirnment-variable DEFAULT_COMMAND_SEPARATOR_CHARACTER "DEFAULT_COMMAND_SEPARATOR_CHARACTER needs to be defined in environm.btm"
                set  validated_stDfCmdSepChar=1 
        endiff        

rem Set the command separator to the default one defined in environm.btm:
        @setdos /x0                                                     %+ rem Restore defaults (redundant, but feels safer)
        @setdos /x-5                                                    %+ rem Remove command separator parsing        
        @setdos /c%DEFAULT_COMMAND_SEPARATOR_CHARACTER%                 %+ rem Remove command separator parsing

        @setdos /x0
