@on break cancel
@Echo OFF

:::::::::: TODO would work better if all dirlists were only one level deep

:::: DOCUMENTATION:
    :::: USAGE:
    ::          set FILE_TO_CHECK_FOR=filename
    ::          set FILESIZE_MUST_BE=0
    ::          set RANDOM_DIR_WALKING=1
    ::          set SKIP_IF_FOUND_1=some_thing
    ::          set SKIP_IF_FOUND_*=[...]
    ::          set SKIP_IF_FOUND_9=maybe_even_nine_things
    ::          set SKIP_IF_FILEMASK_NOT_PRESENT=%FILEMASK_IMAGE%     Skips (not stops) if folder does not contain files matching a filemask
    ::          set STOP_IF_NOT_FOUND_1=some_thing_1                  \___ stops if *both* are not found. (SKIPS are evaluated before STOPS)
    ::          set STOP_IF_NOT_FOUND_2=some_thing_2                  /
    ::          set CRUMBS=1.crumb
    ::          set KEYSTACK=fa
    ::          call find-folder-that-meets-conditions
    ::
    ::  .... Will look through folders until we find a file named "filename" with size of "0".
    ::  .... Will do so in RANDOM folder order, so as not to have alphabeticall bias.
    ::  .... Will automatically keep going if the file "some_other.crumb" is found. (can use for multiple files, currently coded up to: SKIP_IF_FOUND_9)
    ::  .... Will leave a file named "1.crumb" in each folder after it and its children have been checked, 
    ::            which prevents unnecessary folder crawls when working on longterm projects with deep, vast repositories
    ::  .... When done, command-line will be pre-populated with command "fa"
    ::
    ::  To not use any of these subfeatures, simply do not define these environment variables.


::::: CONSTANTS THAT MAYBE COULD BE PARAMETERS:
    SET MINUTES_BEFORE_TRASHING_CURRENT_DIRECTORY_RANDOMIZATION=10
    SET MINUTES_BEFORE_TRASHING_CURRENT_DIRECTORY_LIST=1440
::::: CONSTANTS:
    set DIRLISTRAND=dirlist-random-%_YEAR.bak
    set DIRLISTNORM=dirlist-normal-%_YEAR.bak
    if "%@UPPER[%USERNAME%]" eq "CLAIRE" goto :IsClio
    if "%@UPPER[%USERNAME%]" eq "CLIO"   goto :IsClio
        set DIRLISTRAND=%DIRLISTRAND%-%USERNAME%.bak
        set DIRLISTNORM=%DIRLISTNORM%-%USERNAME%.bak
    :IsClio
    set DIRLISTS_MASK=%DIRLISTNORM%;%DIRLISTRAND%


:::: CHECK FOR CORRECT INVOCATION:
    call validate-environment-variable EDITOR
    call validate-environment-variable FILE_TO_CHECK_FOR
    call validate-environment-variable DIRLISTRAND
    call validate-environment-variable DIRLISTNORM  
    :: BAD IDEA, SHOULD BE A PARAMETER: if "%FIND_FOLDER_GENERAL_MAPPINGS_CHECKED%" ne "1" (call checkmappings %+ set FIND_FOLDER_GENERAL_MAPPINGS_CHECKED=1)


:::: TRASH EXPIRED INDEXES:
    :: delete %DIRLISTRAND% if it's more than 15min old
            SET FILE_TO_CHECK=%DIRLISTRAND%
            SET MINUTES_BEFORE_REFRESH=%MINUTES_BEFORE_TRASHING_CURRENT_DIRECTORY_RANDOMIZATION%
                SET   TIMESTAMP_PER_SECOND=10000000
                SET     SECONDS_PER_MINUTE=60
                set LOCAL_FILE_AGE=99999999999
                if exist "%FILE_TO_CHECK"% (SET LOCAL_FILE_AGE=%@FILEAGE["%FILE_TO_CHECK%"])
                SET          TIMESTAMP_NOW=%@MAKEAGE[%_date,%_time]
                SET  REFRESH_THRESHOLD_MIN=%@EVAL[%MINUTES_BEFORE_REFRESH% * %SECONDS_PER_MINUTE% * %TIMESTAMP_PER_SECOND%]
                SET      CURRENT_DELTA_VAL=%@EVAL[%TIMESTAMP_NOW%     -         %LOCAL_FILE_AGE%]
                SET      CURRENT_DELTA_SEC=%@EVAL[%CURRENT_DELTA_VAL% /   %TIMESTAMP_PER_SECOND%]
                SET      CURRENT_DELTA_MIN=%@EVAL[%CURRENT_DELTA_SEC% /     %SECONDS_PER_MINUTE%]
                SET                  DO_IT=%@EVAL[%CURRENT_DELTA_MIN% > %MINUTES_BEFORE_REFRESH%]
                if "%DO_IT%" eq "1" .and. exist "%FILE_TO_CHECK%"  (echo * Deleting %FILE_TO_CHECK% for being more than %MINUTES_BEFORE_REFRESH% minutes old %+ *del %FILE_TO_CHECK%)
    :: delete %DIRLISTNORM% if it's more than 24hrs (1440min) old
            SET FILE_TO_CHECK=%DIRLISTNORM%
            SET MINUTES_BEFORE_REFRESH=%MINUTES_BEFORE_TRASHING_CURRENT_DIRECTORY_LIST%
                SET   TIMESTAMP_PER_SECOND=10000000
                SET     SECONDS_PER_MINUTE=60
                SET         LOCAL_FILE_AGE=%@FILEAGE["%FILE_TO_CHECK%"]
                SET          TIMESTAMP_NOW=%@MAKEAGE[%_date,%_time]
                SET  REFRESH_THRESHOLD_MIN=%@EVAL[%MINUTES_BEFORE_REFRESH% * %SECONDS_PER_MINUTE% * %TIMESTAMP_PER_SECOND%]
                SET      CURRENT_DELTA_VAL=%@EVAL[%TIMESTAMP_NOW%     -         %LOCAL_FILE_AGE%]
                SET      CURRENT_DELTA_SEC=%@EVAL[%CURRENT_DELTA_VAL% /   %TIMESTAMP_PER_SECOND%]
                SET      CURRENT_DELTA_MIN=%@EVAL[%CURRENT_DELTA_SEC% /     %SECONDS_PER_MINUTE%]
                SET                  DO_IT=%@EVAL[%CURRENT_DELTA_MIN% > %MINUTES_BEFORE_REFRESH%]
                if "%DO_IT%" eq "1"  (echo * Deleting %FILE_TO_CHECK% for being more than %MINUTES_BEFORE_REFRESH% minutes old %+ *del %FILE_TO_CHECK%)

:::: CHECK ALL FOLDERS FOR UPLOAD SCRIPT:
    set ALREADY_FOUND=0

    :: determine whether we go through our dir list in sequential or random order:
        if "%RANDOM_DIR_WALKING%" ne "1" (gosub ensureDirListNormal %+ set DIRLIST_TO_USE=%DIRLISTNORM%)
        if "%RANDOM_DIR_WALKING%" eq "1" (gosub ensureDirListRandom %+ set DIRLIST_TO_USE=%DIRLISTRAND%)

    :: go through our dir list, checking for the situation:
        for /a:d %1 in (@%DIRLIST_TO_USE%) do gosub processdir "%1"

:::: THE SCRIPT ENDS ITSELF IF WE GET TO ONE THAT DOESN'T HAVE IT, SO IF WE GET HERE, WE NEVER FOUND IT.
    unset /q NOT %+ if "%ALREADY_FOUND%" ne "1" set NOT= NOT
    %COLOR_ALARM% %+ echos *** Got to the end. Did%NOT% find a folder that meets these conditions. 
    %COLOR_DEBUG% %+ echo     (ALREADY_FOUND=%ALREADY_FOUND% and should always be 0 here)
                     if "%ALREADY_FOUND%" eq "1" call alarm-charge
                     if "%ALREADY_FOUND%" eq "0" call white-noise 1
                     pause
    goto :END



::::::::::::::::::::::::::::::::::::::::::::::::::::::::: THIS IS THE SUBROUTINE THAT CHECKS EACH FOLDER:
:processdir [dirwithquotes]
    ::::: Debug:
        ::echo * Checking folder %dirwithquotes%

    ::::: We have to run through every folder, so if we've already found it, we do nothing:
        if "%ALREADY_FOUND%" eq "1" (goto :Nevermind)
        set dir=%@STRIP[%=",%dirwithquotes]
        if "%dir%" eq "" .or. "%dir%" eq "." .or. "%dir%" eq ".." goto :Nevermind

    ::::: If we're here, we're *actually* checking a folder. Change into it:
        echo. %+ %COLOR_IMPORTANT% %+ echos * Checking folder "%dir%"... %+ %COLOR_NORMAL%
        if not isdir "%dir%" goto :Nevermind
        cd "%dir%"
        :Deciding to do this later, after recursing: if defined CRUMBS if exist "%CRUMBS%" (color bright blue on black %+ echos ...crumbs found... %+ color white on black %+ goto :FoundIt_NO_NoCrumbs)

    ::::: Recurse folders:
        if "%RANDOM_DIR_WALKING%" eq "1" goto :Random_YES
        if "%RANDOM_DIR_WALKING%" eq "0" goto :Random_NO
                                         goto :Random_NO
            :Random_YES
                color cyan on black %+ echos ...Ensuring random dirlist... %+ color white on black
                gosub ensureDirListRandom 
                for /a:d %1 in (@%DIRLISTRAND%) do gosub processdir "%1"
                if "%ALREADY_FOUND%" eq "1" goto :Nevermind
                goto :Recurse_Done
            :Random_NO
                color bright blue on black %+ echos ...Ensuring non-random dirlist... %+ color white on black
                gosub ensureDirListNormal
                for /a:d %1 in (@%DIRLISTNORM%) do gosub processdir "%1"
                if "%ALREADY_FOUND%" eq "1" goto :Nevermind
                goto :Recurse_Done
            :Recurse_Done



    ::::: Did we earlier instruct to ignore the folder entirely if a certain file is found?
        if defined SKIP_IF_FILEMASK_NOT_PRESENT (if not exist %SKIP_IF_FILEMASK_NOT_PRESENT% (%COLOR_LOGGING% %+ echo * Skipping this folder because no files exist matching the filemask of %SKIP_IF_FILEMASK_NOT_PRESENT% %+ goto :FoundIT_NO))
        if exist %SKIP_IF_FOUND_1% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_2% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_3% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_4% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_5% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_6% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_7% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_8% goto :FoundIt_NO
        if exist %SKIP_IF_FOUND_9% goto :FoundIt_NO

    ::::: Consider STOP_IF_NOT_FOUND_1  and above:
            if defined SKIP_IF_NOT_FOUND_1 .and. not exist "%SKIP_IF_NOT_FOUND_1%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_1%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_2 .and. not exist "%SKIP_IF_NOT_FOUND_2%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_2%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_3 .and. not exist "%SKIP_IF_NOT_FOUND_3%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_3%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_4 .and. not exist "%SKIP_IF_NOT_FOUND_4%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_4%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_5 .and. not exist "%SKIP_IF_NOT_FOUND_5%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_5%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_6 .and. not exist "%SKIP_IF_NOT_FOUND_6%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_6%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_7 .and. not exist "%SKIP_IF_NOT_FOUND_7%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_7%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_8 .and. not exist "%SKIP_IF_NOT_FOUND_8%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_8%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  
            if defined SKIP_IF_NOT_FOUND_9 .and. not exist "%SKIP_IF_NOT_FOUND_9%" (%COLOR_LOGGING% %+ echo. %+ echo * Stopping execution because the following file was not found: "%SKIP_IF_NOT_FOUND_9%" %+ %COLOR_NORMAL% %+ goto :Nevermind)  

    ::::: Is what we are looking for here?
        if defined CRUMBS if exist "%CRUMBS%" (color bright blue on black %+ echos ...crumbs found... %+ color white on black %+ goto :FoundIt_NO_NoCrumbs)
        if exist %FILE_TO_CHECK_FOR% goto :FoundIt_YES
                                     goto :FoundIt_NO
            :FoundIt_YES
                if not defined FILESIZE_MUST_BE goto :FoundIt_CheckFilesize_NO
                                                goto :FoundIt_CheckFilesize_YES
                    :FoundIt_CheckFilesize_YES
                            color blue on black %+ echos ...Filesize checked... %+ color white on black
                             if %@FILESIZE["%FILE_TO_CHECK_FOR%"] != %FILESIZE_MUST_BE% goto :FoundIt_NO
                    :FoundIt_CheckFilesize_NO
                echo. %+ color bright green on black %+ echo * %FILE_TO_CHECK_FOR% found! %+ color white on black
                set ALREADY_FOUND=1
                :DEBUG: echo on %+ REM this is a debug for seeing what happens after the file is found
                goto :Found_It_DONE
            :FoundIt_NO
                if defined CRUMBS >"%CRUMBS%"
                color blue on black %+ echos ...crumbs left... %+ color white on black
                :FoundIt_NO_NoCrumbs
                cd ..
            :Found_It_DONE

    ::::: DONE / NEVERMIND:
        :Nevermind
        :: these files are sometimes locked still, so we now do this in cleanup phase: if exist %DIRLISTNORM% *del %DIRLISTNORM%
        :: these files are sometimes locked still, so we now do this in cleanup phase: if exist %DIRLISTRAND% *del %DIRLISTRAND%
        :DEBUG: color bright white on black %+ @echo - PreReturn: processdir %dirwithquotes% ... %+ color white on black
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::: END OF SUBROUTINE






::::::::::::: UTILITY FUNCTIONS: BEGIN: ::::::::::::: 

                    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                    :ensureDirListNormal
                        if   exist      %DIRLISTNORM% return
                        dir /a:d /b    >%DIRLISTNORM% >&>nul
                    return                        
                    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                    :ensureDirListRandom
                        if exist %DIRLISTRAND% return
                        gosub ensureDirListNormal
                        (type %DIRLISTNORM% |:u8 cygsort -R) >:u8%DIRLISTRAND% >&>nul
                    return                        
                    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::: UTILITY FUNCTIONS: END :::::::::::::::



::::: When we're done, some minor cleanup:
    :END

    :: remove our temp files, since they tend to still be file-locked if we delete them earlier:
        global /q if exist %DIRLISTS_MASK% *del %DIRLISTS_MASK%

    :: stack any keys we're told to stack:
        :DEBUG: echo ALREADY_FOUND is %ALREADY_FOUND%, keystack=%KEYSTACK%
        if "%ALREADY_FOUND%" eq "0" goto :NoKeystack
            if not defined KEYSTACK goto :NoKeystack
            keystack %KEYSTACK%
        :NoKeystack

    :: unset environment variables we don't want set again (parameters especially)
        unset /q FILE_TO_CHECK_FO R
        unset /q FILESIZE_MUST_BE 
        unset /q RANDOM_DIR_WALKING 
        unset /q SKIP_IF_FOUND_1
        unset /q SKIP_IF_FOUND_2
        unset /q SKIP_IF_FOUND_3
        unset /q SKIP_IF_FOUND_4
        unset /q SKIP_IF_FOUND_5
        unset /q SKIP_IF_FOUND_6
        unset /q SKIP_IF_FOUND_7
        unset /q SKIP_IF_FOUND_8
        unset /q SKIP_IF_FOUND_9
        unset /q CRUMBS
        unset /q KEYSTACK
   
    :: show user folder we just found:
        dir
