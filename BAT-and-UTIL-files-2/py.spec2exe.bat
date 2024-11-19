@Echo Off 
@on break cancel

REM TODO: may want to force %1's extention to be .spec if %@FILES[*.spec] ge 1 but force a .py 


REM Get parameter of script name and validate that we're ready to compile...
        set NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE=%1
        REM call debug NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE is %NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE%
        call validate-environment-variable NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE
        call validate-in-path pyinstaller errorlevel ls


REM Let user know what we're doing...
        echo.
        call important * Attempting to build %NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE%...
        echo.


REM Check if other parameters were passed
        set OPTIONS=
        if "%2" ne "onefile" (echo. %+ call advice - Remember, we can do %0 %1 --onefile to compile as a single .EXE)
        if "%2" ne "" (set OPTIONS=%2$)
        eset options
        REM DEBUG: call debug "- OPTIONS are: '%OPTIONS%'"


REM Make sure dist folder is nuked
        if isdir dist  (%COLOR_REMOVAL% %+ rd /s /q dist )
        if isdir build (%COLOR_REMOVAL% %+ rd /s /q build)
        if isdir dist  (call warning Dist  dir still exists!)
        if isdir build (call warning Build dir still exists!)


REM Compile the EXE...  Time it...
        timer /7 /q on
        set                     COMMAND=pyinstaller --noconfirm --log-level DEBUG %OPTIONS% %NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE%
        call debug - About to: %COMMAND%
        %COLOR_RUN%    %+      %COMMAND%
        call errorlevel "compilation of '%NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE%' must have failed?" "??? Compilation was maybe succesful ???


REM Let user know how long it took...
        echo.
        %COLOR_COMPLETION% 
        timer /7 off
        %COLOR_NORMAL%
        echo.


REM Change into the folder where the new EXE was built...  But save where we are so we can return with popd
        pushd
        set DIST_DIR=dist\%@NAME[%NAME_OF_PYTHON_SCRIPT_TO_BUILD_TO_EXE%]
        call validate-environment-variable DIST_DIR
        cd "%DIST_DIR%"


REM Show contents to user...
        %COLOR_SUCCESS% 
        ls
        %COLOR_NORMAL%
        dir *.exe 





