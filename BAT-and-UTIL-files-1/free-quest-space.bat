@Echo OFF


rem Validate environment (once):
        iff "1" != "%validated-freequestspace%" then
                call validate-environment-variables ansi_color_has_been_set
                call validate-in-path               adb sleep 
                set  validated-freequestspace=1
        endiff

rem Display free space on Quest/adb device:
        :display
        echos %@randfg_soft[]                                        
        call adb shell df /sdcard


rem Check for a key...
        unset /q key
        inkey /w0 /k %%key 
        if  "" !=  "%key" (goto :stop_displaying)
        sleep 2
        repeat 1 echos %ansi_move_up_1%
        goto :display

:stop_displaying


