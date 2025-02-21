@Echo On
@loadbtm on

rem Validate environment (once):
        *setdos /x0  
        if "1" == "%validated_stDfEscChar%" goto :already_validated
                if not defined DEFAULT_ESCAPE_CHARACTER_DESCRIPTION (echos FATAL ERROR: DEFAULT_ESCAPE_CHARACTER_DESCRIPTION %+ echo  must be defined %+ goto :END)
                if not defined DEFAULT_ESCAPE_CHARACTER             (echos FATAL ERROR: DEFAULT_ESCAPE_CHARACTER             %+ echo  must be defined %+ goto :END)
                if not defined         ESCAPE_CHARACTER             (echos FATAL ERROR: ESCAPE_CHARACTER                     %+ echo  must be defined %+ goto :END)
                set  validated_stDfEscChar=1 
        :already_validated      

rem Set the command separator to the default one defined in environm.btm:
        *setdos /x0                                                                    
        *setdos /x-8                                                                   
        *set   ESCAPE_CHARACTER_DESCRIPTION=%DEFAULT_ESCAPE_CHARACTER_DESCRIPTION%       
        *iff "%ESCAPE_CHARACTER_DESCRIPTION%" == "PlusOverMinusSymbol" then
                *set ESCAPE_CHARACTER=%@CHAR[177]
                *setdos             /e%@CHAR[177]
        *else
                *set ESCAPE_CHARACTER=%DEFAULT_ESCAPE_CHARACTER%
                *setdos             /e%DEFAULT_ESCAPE_CHARACTER%
        *endiff
        *setdos /x0                                                                    

:END
