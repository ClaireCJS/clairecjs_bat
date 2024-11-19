@on break cancel
@Echo OFF
 set  REVISION=%1
 set  FILE=%2
 call git-initvars



if exist %2 goto :DoNotShowUsage           
        %COLOR_ADVICE% 
        echo.
        echo USAGE: %0 {revision} {file}
        echo        - revision should be something like "4b88dc1ad640cb33820f3ea8ec4b83ffd28c9d28"
        echo        - FILE should exist
:DoNotShowUsage




%COLOR_IMPORTANT% 
echo. 
echo * Contents of %FILE% at revision %REVISION%:
%COLOR_NORMAL%    
git.exe show %REVISION%:%FILE%


