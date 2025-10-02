@Echo OFF
@loadbtm on
@on break cancel


rem Validate environment (once):
        iff "1" != "%validated_lrcget_bat%" then
                call validate-in-path              lrcget.exe junction.exe print-message.bat advice.bat less_important important advice
                call validate-environment-variable ansi_has_been_set
                set  validated_lrcget_bat=1
        endiff




rem Junction to current folder:
        junction.exe c:\lrcget .

rem Let user know:
        repeat 10 echo.
        call less_important "Junctioned %italics_on%c:\lrcget%italics_off% to current folder"
        call important      "❶ Go into the settings %faint_off%(gear icon)%faint_off% for %italics_on%LRCget%italics_off%"
        call important      "❷ Click “%italics_on%Refresh my library for new changes%italics_off%” near the bottom"
        call advice         "If refreshing does not work after %italics_on%LRCget%italics_off% is run, double-check that %italics_on%c:\lrcget\%italics_off% is in the %italics_on%scanning folders%italics_off% section of the %italics_on%LRCget%italics_off% config"

rem Run LRC get:
        lrcget.exe


