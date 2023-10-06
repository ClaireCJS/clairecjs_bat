@Echo OFF


REM  USAGE: call %0 PURPOSE
REM EFFECT: sets TEMP_FOLDER      with PURPOSE in its name, and changes into it
REM EFFECT: sets WHERE_WE_STARTED to original location before changing to temp folder


REM CONFIG
        set VERBOSITY=0         %+ REM 0=silent


REM Is there a stated purpose?
    set PURPOSE=
    if "%1" ne "" (set PURPOSE=%1)
    

REM Store the folder we were in when we created the temp folder
    set WHERE_WE_STARTED=%_CWD

REM Create a temp folder:
    call          set-TEMP-FOLDER %PURPOSE% %~2
    mkdir            %TEMP_FOLDER%
    call val-env-var  TEMP_FOLDER

    
REM Change into the temp folder:
   
    cd               %TEMP_FOLDER%



