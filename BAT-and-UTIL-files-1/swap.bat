@Echo Off

call validate-environment-variables COLOR_NORMAL COLOR_LOGGING
call validate-in-path setTmpFile move ren copy important

call setTmpFile


move %1 "%TMPFILE%"    >nul
ren  %2          %1    >nul
copy "%TMPFILE%" %2    >nul

call important "Filenames swapped."

echo.
 
:END
