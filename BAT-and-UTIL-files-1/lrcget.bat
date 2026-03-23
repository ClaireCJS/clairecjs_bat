@Echo OFF
@loadbtm on
@on break cancel


rem Validate environment (once):
        iff "1" != "%validated_lrcget_bat%" then
                call validate-in-path              lrcget.exe junction.exe print-message.bat advice.bat less_important important advice celebration advice sweep approve-lyrics less_important
                call validate-environment-variable ansi_has_been_set EMOJI_GEAR
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
        repeat 4 echo.
        call important "Starting %italics_on%LRCget%italics_off% ... click the %EMOJI_GEAR%" big
        LRCget.exe


rem Run LRC get:
        repeat 9 echo.
        call celebration "Done with %italics_on%LRCget!%italics_off%"



rem Run LRC get:
        repeat 2 echo.
        call Advice "If we don’t approve the %italics_on%LRCget%italics_off% lyrics now, manually approving them later will be more time-consuming"
        call AskYN "Recursively approve all TXT lyrics" yes 0
                iff "Y" == "%ANSWER%" then
                        repeat 3 echo.
                        call less_important "Approving all TXT lyrics in this folder, and its subfolders!"
                        sweep if exist *.txt call approve-lyrics *.txt force
                endiff
        repeat 2 echo.



