@Echo OFF

echo.
call important "Going to Claire's github"

iff exist "c:\bat\%@UNQUOTE[%1]" then
        call see-latest-version-of-BAT-on-github.bat %*
else
        https://github.com/ClaireCJS/clairecjs_bat/
endiff
