@Echo OFF

set maxSize=0
set largestFile=


for %%G in (*.*) do (
    set fileSize=%%~zG
    if %fileSize% GT %maxSize% (
        set /A maxSize=%fileSize%
        set largestFile=%%G
    )
)

if "%largestFile%"=="" (%COLOR_ERROR% %+ echo Largest file not found! %+ goto :END)

echo.
echo.
call important "The largest file is: '%emphasis%%largestFile%%deemphasis%'"
call warning "Delete the largest file?"
%COLOR_REMOVAL%   
if exist "\recycled\%largestFile%" (%COLOR_UNIMPORTANT %+ *del "\recycled\%largestFile%" %+ %COLOR_REMOVAL%)
set UNDOCOMMAND=mv \recycled\"%largestFile%" .
del "%largestFile%" %* 



:END