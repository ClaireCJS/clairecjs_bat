@Echo OFF
@on break cancel

rem Validate environment (once):
        iff 1 ne %validated_unlock_top% then
                call validate-in-path top-message.bat
                set  validated_unlock_top=1
        endiff        

rem Unlock the rows:
        call top-message unlock


