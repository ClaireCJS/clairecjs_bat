@Echo OFF


rem DOCUMENATION:
    :PURPOSE: Segregates a mask of filenames into a sub-directory named in the configuration
    :USAGE:   "Segregate *.jpg", for example.

rem CONFIGURATION:
    call segregate-vars

rem VALIDATION:
    if ""  eq   "%1" goto :Usage
    if not exist %1  goto :Exist_NO
    if isdir %SUBFOLDER% gosub :Subdir_Exists_YES
    SET FILES_TO_SEGREGATE=%1

rem SEGREGATION:
    md "%SUBFOLDER%"            
    if not isdir %SUBFOLDER% goto :Subdir_Exists_NO
    %COLOR_REMOVAL% %+ mv %FILES_TO_SEGREGATE% "%SUBFOLDER%"
                       cd "%SUBFOLDER%"
    %COLOR_RUN%     %+ dir
    set UNDOCOMMAND=call desegregate
    


    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    goto :END
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Usage
            echo * USAGE: %* *.whatever - will segregate *.whatever into a subfolder named %SUBFOLDER%
        goto :END
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Exist_NO
            echo * FATAL ERROR: %1 does not match any files!
        goto :END
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Subdir_Exists_YES
            %COLOR_WARNING% %+ echos * WARNING: Sub-folder of %SUBFOLDER% exists already!
            %COLOR_ADVICE%  %+ echo  Maybe clean that mess up?
            %COLOR_PAUSE%   %+ pause
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Subdir_Exists_NO
            echo * FATAL ERROR: Sub-folder of %SUBFOLDER% does not exist, but we just tried creating it! WTF?!
        goto :END
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :END
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


