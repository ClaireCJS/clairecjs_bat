@Echo OFF            
@on break cancel


rem Validate environemnt (once):
        @setdos /x0
        iff 1 ne %validated_setesccharandcomsep% then
                validate-in-path set-default-command-separator set-default-escape-character
                set validated_setesccharandcomsep=1
        endiff


call set-default-escape-character
call set-default-command-separator
