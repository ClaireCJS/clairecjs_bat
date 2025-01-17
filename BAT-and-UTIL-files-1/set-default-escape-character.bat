@Echo OFF
@loadbtm on

rem Validate environment (once):
        @setdos /x0  
        iff 1 ne %validated_stDfEscChar% then
                rem call validate-environment-variable DEFAULT_ESCAPE_CHARACTER ESCAPE_CHARACTER
                set  validated_stDfEscChar=1 
        endiff        

rem Set the command separator to the default one defined in environm.btm:
        @*setdos /x0                                                                    
        @*setdos /x-8                                                                   
        @*setdos /e`%DEFAULT_ESCAPE_CHARACTER%`
        @*set ESCAPE_CHARACTER_DESCRIPTION=%DEFAULT_ESCAPE_CHARACTER_DESCRIPTION%       
        @*setdos /x0                                                                    
