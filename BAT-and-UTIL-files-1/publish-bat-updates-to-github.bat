@Echo Off
@on break cancel

 cls
*cls

 call say.bat "Here we go!" 
 

rem Capture parameters:
        set pbutg_params=%*

rem Go to my development folder:
        call dev
        set  dir=clairecjs_bat
        call validate-environment-variable dir
        *cd  %dir%


rem Do the updates:
        title .
        rem echo pentagram test: %pentagram% %+ pause 
        set torun=update-from-BAT-and-push-and-commit.bat
        call validate-in-path %torun% 
        
rem Actually do it:        
        call %torun% %pbutg_params%

