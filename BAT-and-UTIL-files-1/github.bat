@on break cancel
@Echo OFF

echo.
call important "Going to Claire's github"

iff "%1" eq "audio-processing-batch-NOTES.txt" then
        echo call see-latest-version-of-BAT-on-github.bat "`notes%20-%20audio%20processing.txt`"
elseiff exist "c:\bat\%@UNQUOTE[%1]" .or. exist "c:\notes\%@UNQUOTE[%1]" then
        call see-latest-version-of-BAT-on-github.bat %*
else
        https://github.com/ClaireCJS/clairecjs_bat/
endiff
