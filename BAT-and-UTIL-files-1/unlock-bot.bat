@Echo OFF
@on break cancel

rem Validate environment (once):
        iff "1" != "%validated_unlock_bot%" then
                call validate-in-path  status-bar.bat
                set  validated_unlock_bot=1
        endiff        

rem Unlock the rows:
        call status-bar unlock

