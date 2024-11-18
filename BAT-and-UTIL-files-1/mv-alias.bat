@Echo Off
 on break cancel
 set ARGS=%*

:USAGE: mv like mv, but also you can set env-var MV_DRY_RUN_FIRST=1 to simulate the move first (with configurable timeout via env-var DRY_RUN_WAIT_TIME_BEFORE_PROCEEDING), and you can also set MV_DECORATOR to be a string before each line of the move, or MV_DECORATOR_ON & MV_DECORATOR_OFF to be more granular in decorating your mvs


REM Title
        title %@CHAR[55357]%@CHAR[56986]Moving: %*

REM CONFIGURATION:
        set DRY_RUN_WAIT_TIME_BEFORE_PROCEEDING=60




REM PROTECTION FROM PASSING NO ARGS WHICH WOULD PULL OUR RECYCLE BIN INTO CURRENT FOLDER WHICH IS A NASTY CLEANUP:
        REM @echo %%1 is %1, %%2 is %2
        if "%1" eq "\recycled" .and. "%2" eq "" goto :END
        if "%1" eq ""                           goto :END


REM Automatic coloring
        echo %ANSI_RESET%
        iff "%2" eq "\recycled" then
            %COLOR_REMOVAL%
        else
            %COLOR_RUN%
        endiff


REM special decorator invocation
        if "%MV_DECORATOR%" eq "randcolor" .or. "%MV_DECORATOR_ON%" eq "randcolor" .or. "%MOVE_DECORATOR%" eq "randcolor" .or. "%MOVE_DECORATOR_ON%" eq "randcolor" (call randcolor %+ gosub reset_option_variables)
        if "%MV_DECORATOR%" eq "randfg"    .or. "%MV_DECORATOR_ON%" eq "randfg"    .or. "%MOVE_DECORATOR%" eq "randfg"    .or. "%MOVE_DECORATOR_ON%" eq "randfg"    (call randfg    %+ gosub reset_option_variables)
        if "%MV_DECORATOR%" eq "randbg"    .or. "%MV_DECORATOR_ON%" eq "randbg"    .or. "%MOVE_DECORATOR%" eq "randbg"    .or. "%MOVE_DECORATOR_ON%" eq "randbg"    (call randbg    %+ gosub reset_option_variables)


REM create our move and undo commands 
        REM MOVE_COMMAND=*move /r /g /h    REM added /E to continue after error messages on 20230601 which i think  will improve reliability a lot because more stuff gets done set                   
        SET MOVE_COMMAND=*move /r /g /h /E 
        SET  UNDOCOMMAND=echo %MOVE_COMMAND% %9 %8 %7 %6 %5 %4 %3 %2 %1
        REM @echo move_command is %italics%%MOVE_COMMAND%%italics_off%

REM do we add /N to do a dry run first?
        if   %MV_DRY_RUN_FIRST eq 1 (goto :Dry_Run_Begin)
        if %MOVE_DRY_RUN_FIRST eq 1 (goto :Dry_Run_Begin)
                                     goto :Dry_Run_End
        :Dry_Run_Begin            
            echo.
            call bigecho %RED_FLAG% Dry run: %RED_FLAG%
                echos %MV_DECORATOR%%MOVE_DECORATOR%%MV_DECORATOR_ON%%MOVE_DECORATOR_ON%
                      rem cat_fast re-rendered broken ansi correctly:
                      %MOVE_COMMAND% /N %ARGS% |&:u8 c:\bat\copy-move-post.py |:u8 c:\util\cat_fast
                rem   %MOVE_COMMAND% /N %ARGS% |& copy-move-post.exe ... is 7X slower
                echos %MV_DECORATOR_OFF%%MOVE_DECORATOR_OFF%
            echo.
            call askyn "%EMOJI_UP_ARROW%%EMOJI_UP_ARROW%%EMOJI_UP_ARROW% Above %EMOJI_UP_ARROW%%EMOJI_UP_ARROW%%EMOJI_UP_ARROW% was a %blink%DRY RUN / TEST%blink_off%. Do it for %italics%real%italics_off%" Y %DRY_RUN_WAIT_TIME_BEFORE_PROCEEDING% 
                if %answer eq Y (echo. %+ goto :Dry_Run_End)
                    call warning "Aborted by user!"
                    goto :END
        :Dry_Run_End

REM actually do the move command:
        echos %MV_DECORATOR%%MOVE_DECORATOR%%MV_DECORATOR_ON%%MOVE_DECORATOR_ON%
        rem   %MOVE_COMMAND% %A%GS%  |&    copy-move-post.exe ... is 7X slower
        rem   %MOVE_COMMAND% %ARGS%  |&    copy-move-post.py
        rem echo (%MOVE_COMMAND% %ARGS%) {PIPE} copy-move-post.py
                 (%MOVE_COMMAND% %ARGS%) |&:u8  copy-move-post.py
        echos %MV_DECORATOR_OFF%%MOVE_DECORATOR_OFF%

gosub reset_option_variables

goto :END

                :reset_option_variables
                        REM options expire after being used once:        
                            if defined   MV_DECORATOR     (set   MV_DECORATOR=)
                            if defined MOVE_DECORATOR     (set MOVE_DECORATOR=)
                            if defined   MV_DECORATOR_ON  (set   MV_DECORATOR_ON=)
                            if defined MOVE_DECORATOR_ON  (set MOVE_DECORATOR_ON=)
                            if defined   MV_DECORATOR_OFF (set   MV_DECORATOR_OFF=)
                            if defined MOVE_DECORATOR_OFF (set MOVE_DECORATOR_OFF=)
                return

:END

rem Done window title:
        title %CHECK%Done: mv %*

