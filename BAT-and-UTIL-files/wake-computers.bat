@Echo OFF

: EXAMPLE:
:    C:\new>mcgetmac goliath
:    Name: Goliath
:    IP address: 66.167.233.212
:    Ethernet MAC address: BC:5F:F4:43:EC:6E

rem  Assuming we're running this on Demona, so don't need Demona in here:
        call validate-environment-variables  IP_WYVERN  IP_THAILOG  IP_GOLIATH
        call validate-environment-variables MAC_WYVERN MAC_THAILOG MAC_GOLIATH
        gosub wake_computer                     Wyvern
        gosub wake_computer                                Thailog
        gosub wake_computer                                            Goliath


goto :END
    :wake_computer [name]
        set tmp_emoji=%[emoji_machine_%name%]
        call less_important "Waking %tmp_emoji% %name% %tmp_emoji%..."
        echo wake-on-lan.exe %[mac_%name%] /a %[ip_%name%]
    return
:END
