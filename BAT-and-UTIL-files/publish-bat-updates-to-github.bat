@Echo OFF
 cls

rem Go to my development folder:
        call dev
        cd   clairecjs_bat


rem Do the updates:
        title .
        echo pentagram test: %pentagram% %+ pause 
        call update-from-BAT-and-push-and-commit.bat

