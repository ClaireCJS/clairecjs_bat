@Echo OFF
@on break cancel


rem Validate environment (once):
        iff "1" != "%validated-rml%" then
                call validate-in-path start-minilyrics stop-minilyrics sleep askyn fix-minilyrics-window-size-and-position
                set  validated-rml=1
        endiff        


rem Stop, wait, & restart MiniLyrics:
        call  stop-minilyrics
        sleep 2
        call start-minilyrics

rem Ask if we should fix window positions:
        call AskYN "Fix MiniLyrics window position & size" 30 no 
        if "Y" == "%ANSWER%" call fix-minilyrics-window-size-and-position

