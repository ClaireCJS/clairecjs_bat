@Echo Off


REM PROTECTION FROM PASSING NO ARGS WHICH WOULD PULL OUR RECYCLE BIN INTO CURRENT FOLDER WHICH IS A NASTY CLEANUP:
        REM @echo %%1 is %1, %%2 is %2
        if "%1" eq "\recycled" .and. "%2" eq "" goto :END
        if "%1" eq ""                           goto :END



REM Automatic coloring
        if "%2" eq "\recycled" (
            %COLOR_REMOVAL%
        ) else (
            %COLOR_RUN%
        )


REM special decorator invocation
        if "%MV_DECORATOR%" eq "randcolor" .or. "%MV_DECORATOR_ON%" eq "randcolor" .or. "%MOVE_DECORATOR%" eq "randcolor" .or. "%MOVE_DECORATOR_ON%" eq "randcolor" (call randcolor %+ gosub reset_option_variables)
        if "%MV_DECORATOR%" eq "randfg"    .or. "%MV_DECORATOR_ON%" eq "randfg"    .or. "%MOVE_DECORATOR%" eq "randfg"    .or. "%MOVE_DECORATOR_ON%" eq "randfg"    (call randfg    %+ gosub reset_option_variables)
        if "%MV_DECORATOR%" eq "randbg"    .or. "%MV_DECORATOR_ON%" eq "randbg"    .or. "%MOVE_DECORATOR%" eq "randbg"    .or. "%MOVE_DECORATOR_ON%" eq "randbg"    (call randbg    %+ gosub reset_option_variables)


REM create our move and undo commands 
        REM MOVE_COMMAND=move /r /g /h    REM added /E to continue after error messages on 20230601 which i think  will improve reliability a lot because more stuff gets done set                   
        SET MOVE_COMMAND=move /r /g /h /E 
        SET  UNDOCOMMAND=echo %MOVE_COMMAND% %9 %8 %7 %6 %5 %4 %3 %2 %1
        REM @echo move_command is %italics%%MOVE_COMMAND%%italics_off%

REM actually do the move command:
        echos %MV_DECORATOR%%MOVE_DECORATOR%%MV_DECORATOR_ON%%MOVE_DECORATOR_ON%
              %MOVE_COMMAND% %* |& copy-move-post.py
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
