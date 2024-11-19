@Echo OFF
@on break cancel
 cls

rem Go to my development folder:
        call dev
        cd   clairecjs_bat


rem Do the updates:
        title .
        rem echo pentagram test: %pentagram% %+ pause 
        call update-from-BAT-and-push-and-commit.bat

