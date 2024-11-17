@Echo OFF

: EXAMPLE:
:    C:\new>mcgetmac goliath
:    Name: Goliath
:    IP address: 66.167.233.212
:    Ethernet MAC address: BC:5F:F4:43:EC:6E

        call validate-environment-variables  IP_WYVERN  IP_THAILOG  IP_DEMONA  IP_GOLIATH 
        call validate-environment-variables MAC_WYVERN MAC_THAILOG MAC_DEMONA MAC_GOLIATH 
        gosub wake_computer                     Wyvern                                    
        gosub wake_computer                                Thailog                        
        gosub wake_computer                                            Demona             
        gosub wake_computer                                                       Goliath 


goto :END
    :wake_computer [name]
        set tmp_emoji=%[emoji_machine_%name%]
        set tmp_ip=%[ip_%name%]
        set down=%[%name%_down]
        set tmp_mac=%[mac_%name%]

        set tmp_mac_2=%[mac_%name%_2]
        set tmp_mac_3=%[mac_%name%_3]
        set tmp_mac_4=%[mac_%name%_4]
        set tmp_mac_5=%[mac_%name%_5]
        set tmp_mac_6=%[mac_%name%_6]
        set tmp_mac_7=%[mac_%name%_7]

        if %down eq 1 (%COLOR_REMOVAL% %+ echo %NO% Skip:  %tmp_emoji% %name% %tmp_emoji%%tab% — because it is currently down %+ return)

        if defined tmp_mac   gosub wake_mac %name% %tmp_mac   %tmp_ip %tmp_emoji %down
        if defined tmp_mac_2 gosub wake_mac %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
        if defined tmp_mac_3 gosub wake_mac %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
        if defined tmp_mac_4 gosub wake_mac %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
        if defined tmp_mac_5 gosub wake_mac %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
        if defined tmp_mac_6 gosub wake_mac %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down
        if defined tmp_mac_7 gosub wake_mac %name% %tmp_mac_2 %tmp_ip %tmp_emoji %down

    return

    :wake_mac [name tmp_mac tmp_ip tmp_emoji down]
        call less_important "Waking %tmp_emoji% %name% %tmp_emoji%%tab% — at ip: %tmp_ip%%tab%— mac: %tmp_mac%"
        rem echo wake-on-lan.exe %tmp_mac% /a %tmp_ip%
    return
:END
