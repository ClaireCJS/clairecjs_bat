@Echo Off


:Validate_Environment
        set                                DisplayFusionCommand="C:\Program Files (x86)\DisplayFusion\DisplayFusionCommand.exe"
        call validate-environment-variable DisplayFusionCommand


:Restore_Window_Positions
        call important "Restoring window positions %*"
        rem  on 2023/01/23 support told me this was wrong:    full email thread at: https://mail.google.com/mail/u/0/#inbox/FMfcgzGrcPJTKNjfJvShTQWjHDCnkXWV
        rem  %COLOR_RUN% %+ if "%1" eq "" (%DisplayFusionCommand% -functionrun "Restore Window"                          %*) ...... so i changed it to:
             %COLOR_RUN% %+ if "%1" eq "" (%DisplayFusionCommand% -functionrun "Restore Window Positions From Last Save" %*)
             %COLOR_RUN% %+ if "%1" ne "" (%DisplayFusionCommand% -windowpositionprofileload %* %+ set LAST_RESTORED_WINDOW_POSITION=%*)


:END
        call fix-minilyrics-window-size-and-position
        %COLOR_NORMAL%

