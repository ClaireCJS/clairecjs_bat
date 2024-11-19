@on break cancel
call git-initvars
echo USAGE: %0 {date} {file}
echo        - DATE should be YYYY-MM-DD
echo        - FILE should exist
set FILE=%1
set DATE=%2
git show HEAD@{%DATE%}:%FILE%
