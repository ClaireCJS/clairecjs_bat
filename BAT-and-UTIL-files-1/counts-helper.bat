@Echo OFF


for /a:d %1 in (. [@#$&_+=a-z0-9]*) gosub countdir "%1"

goto :END






    :countdir [dir]
        echos %@EXECSTR[dir /bs %dir%\*|:u8wc -l]
        echo  %dir%
    return








:END
