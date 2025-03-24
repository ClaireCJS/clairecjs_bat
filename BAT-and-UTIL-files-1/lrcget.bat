@Echo OFF


rem Validate environment (once):
        iff "1" != "%validated_lrcget_bat%" then
                call validate-in-path lrcget.exe junction.exe print-message.bat advice.bat
                set  validated_lrcget_bat=1
        endiff




rem Junction to current folder:
        junction.exe c:\lrcget .

rem Let user know:
        repeat 10 echo.
        call less_important "Junctioned %italics_on%c:\lrcget%italics_off% to current folder"
        call advice         "If refreshing does not work after %italics_on%LRCget%italics_off% is run, double-check that %italics_on%c:\lrcget\%italics_off% is in the %italics_on%scanning folders%italics_off% section of the %italics_on%LRCget%italics_off% config"

rem Run LRC get:
        lrcget.exe


