@Echo Off
 on break cancel

rem EXAMPLE:
rem    C:\>mcgetmac goliath
rem           Name: Goliath
rem           IP address: 66.167.233.212
rem           Ethernet MAC address: BC:5F:F4:43:EC:6E

rem Validate environment:
        iff 1 ne %validated_wakecomp% then
                call validate-environment-variable ALL_COMPUTERS_UP          "1ˢᵗ parameter to %italics_on%%0.bat%italics_off% must be set ALL_COMPUTERS_UP to a list of computer names in our system, for example, set “%italics_on%ALL_COMPUTERS_UP”%italics_off% TO “%italics_On%GOLIATH THAILOG DEMONA WYVERN%italics_off%”"
                call validate-in-path              wake-on-lan.exe           "the Wake-On-Lan utility %italics_on%wake-on-lan.exe%italics_off% needs to be in the path"
                call validate-environment-variable ANSI_COLORS_HAVE_BEEN_SET "ANSI codes have not been defined. Please run: %blink_on%%italics_on%set-ansi force%italics_off%%blink_off%"
                set validated_wakecomp=1
        endiff                

rem Validate that each computer in our system has its IP address and MAC address set, even if set to "?":
        rem New code that requires no maintanance:
                for %%TmpMachineName in (%ALL_COMPUTERS_UP%) do (
                        if not defined  IP_%TmpMachineName (call error  "%italics_on%IP_%TmpMachineName%%italics_off% is not defined for machine %italics_on%%TmpMachineName%%italics_off%")
                        if not defined MAC_%TmpMachineName (call error "%italics_on%MAC_%TmpMachineName%%italics_off% is not defined for machine %italics_on%%TmpMachineName%%italics_off%")
                        gosub wake_up_by_computer_name %TmpMachineName
                )
        rem Old code that required maintanance:
                rem call validate-environment-variables  IP_WYVERN  IP_THAILOG  IP_DEMONA  IP_GOLIATH 
                rem call validate-environment-variables MAC_WYVERN MAC_THAILOG MAC_DEMONA MAC_GOLIATH 
                rem gosub wake_up_by_computer_name                     Wyvern                                    
                rem gosub wake_up_by_computer_name                                Thailog                        
                rem gosub wake_up_by_computer_name                                            Demona             
                rem gosub wake_up_by_computer_name                                                       Goliath 


rem Annd we’re done!
        goto :END
        
        
    :wake_up_by_computer_name [name]
                rem Fetch the official IP address (and emoji😎) of the machine, defined in environm.btm:
                        set tmp_ip=%[ip_%name%]
                        set tmp_emoji=%[emoji_machine_%name%]
                
                rem check if MACHINANAME_DOWN=1 has been set in environm.btm. If so, the machine is down, so don’t try to wake it:
                        set down=%[%name%_down]                             
                        if %down eq 1 (%COLOR_REMOVAL% %+ echo %NO% Skip:  %tmp_emoji% %name% %tmp_emoji%%tab% — because it is currently down %+ return)

                rem Adjustment for machines with multiple network cards:
                        set tmp_mac_1=%[mac_%name%]
                        set tmp_mac_2=%[mac_%name%_2]
                        set tmp_mac_3=%[mac_%name%_3]
                        set tmp_mac_4=%[mac_%name%_4]
                        set tmp_mac_5=%[mac_%name%_5]
                        set tmp_mac_6=%[mac_%name%_6]
                        set tmp_mac_7=%[mac_%name%_7]

                rem For each mac address that we know of, attempt a wakeup through it’s enterference:
                        if defined tmp_mac_1 gosub wake_up_by_MAC_address %name% %tmp_mac_1 %tmp_ip %tmp_emoji %down
                        if defined tmp_mac_2 gosub wake_up_by_MAC_address %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
                        if defined tmp_mac_3 gosub wake_up_by_MAC_address %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
                        if defined tmp_mac_4 gosub wake_up_by_MAC_address %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
                        if defined tmp_mac_5 gosub wake_up_by_MAC_address %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
                        if defined tmp_mac_6 gosub wake_up_by_MAC_address %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
                        if defined tmp_mac_7 gosub wake_up_by_MAC_address %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
    return

    :wake_up_by_MAC_address [name tmp_mac tmp_ip tmp_emoji down]
                call less_important "Waking %tmp_emoji% %name% %tmp_emoji%  %tab%%@ansi_move_to_col[27] %star2% IP: %tmp_ip%%@ansi_move_to_col[52]%star2% MAC: %tmp_mac%"
                wake-on-lan.exe %tmp_mac% /a %tmp_ip% >nul
    return
:END
