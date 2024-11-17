@Echo OFF

REM validate environment
    call validate-in-path set-largest-filename less_important  split-mp3-by-inputted-chapter-info-helper.py 


REM If any pre-existing generated splitter .bat exists, get rid of it:
    set       SPLITTING_SCRIPT=generated-splitter.bat
    if exist %SPLITTING_SCRIPT%   (%COLOR_REMOVAL% %+ *del %SPLITTING_SCRIPT%)



REM Actually generate a new splitter .bat and run it on the largest file, which sould be the unsplit album:
    call set-largest-filename

    call less_important "Splitting largest file: '%largest_file%'"
    split-mp3-by-inputted-chapter-info-helper.py 




REM Ensure new splitter .bat exists:
    call validate-environment-variable SPLITTING_SCRIPT


REM Now that we have our splitter.bat, run it:
    echo. 
    echo. 
    :Redo
    %COLOR_WARNING% %+ echo * About to run %SPLITTING_SCRIPT%... %+ pause
    %COLOR_RUN%     %+                call %SPLITTING_SCRIPT% "%largest_file%"


REM Check if we've run it successfully or not:
    REM this thing returns 2 which kinda makes our errorlevelcatcher not so great: call errorlevel "but sometimes we see an errorlevel of 2 which seems to be not so bad in this situation?" 
    if %REDO% eq 1 goto :Redo
    %COLOR_REMOVAL% 
    del %SPLITTING_SCRIPT% "%largest_file%"


REM Hopefully there is just 1 of each of these files, but that's what should be the case if we're here!
    ren *.json   info.json
    ren *.txt  README.txt
    ren *.webp  cover.webp

