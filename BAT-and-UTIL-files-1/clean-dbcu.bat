@Echo OFF

rem My personal script for cleaning out my "Dropbox\camera uploads" ['dbcu'] folder


rem Define subfolders for various folder purposes:
        rem SCREENSHOTS=%NEWPICS%\_screenshots is now defined in environm.btm so it can be used outside of this script
        set        NSFW=%NEWPICS%\_NSFW
        set        EBAY=%NEWPICS%\_EBAY
        set      TRIALS=%NEWPICS%\_TRIALS
        set     CABINET=%NEWPICS%\_FILING CABINET
        set     MEDICAL=%PUBCL%\medical


rem Validate the environment + variables we've defined in this script:
        call validate-environment-variables NEWPICS PRN_NEW HARDWARE BAT SCREENSHOTS NSFW TRIALS MEDICAL FILEMASK_VIDEO

rem Define subfolders that we need to process:
        set FOLDERS_TO_PROCESS=_SCREENSHOTS _HARDWARE _NSFW _EBAY _TRIALS _TRIALS\_ORDERS _TRIALS\RETURNS _TRIALS\RETURNS\_DONE _PORN "_FILING CABINET" _PUB_MEDICAL

rem Ensure each of the defined subfolders exists:
        for %%1 in (%FOLDERS_TO_PROCESS%) do if not exist "%1" md "%1"

rem Sort things out
        pushd .                                                                   %+ rem save location to return later
        call dbcu                                                                 %+ rem go to the dropbox folder
        call fix-google-photo-filenames                                           %+ rem fix google filenames to the format we like
        if exist *nsfw* .and. isdir _NSFW      (*move *nsfw* _NSFW)               %+ rem segregate NSFW pix
        if exist *.dep .or. exist *.deprecated (if not isdir dep md dep)          %+ rem segregate deprecated files
        if isdir   dep                         (*move/ds dep %NEWPICS%\dep)       %+ rem move deprecated files to newpics

rem Now that we're done sorting things out, move them to the proper places:
        echos %@RANDFG[] %+ *move /ds _screenshots %SCREENSHOTS%
        echos %@RANDFG[] %+ *move /ds _hardware    %HARDWARE%
        echos %@RANDFG[] %+ *move /ds _nsfw        %NSFW%
        echos %@RANDFG[] %+ *move /ds _ebay        %EBAY%
        echos %@RANDFG[] %+ *move /ds _porn        %PRN_NEW%
        echos %@RANDFG[] %+ *move /ds _trials      %TRIALS%
        echos %@RANDFG[] %+ *move /ds _pub_medical %MEDICAL%

rem NOT USED ANYMORE: Folders related to when we did Amazon Product testing:
        set NEWPICS_TRIALS=%NEWPICS%\_TRIALS
        set NEWPICS_TRIALS_DONE=%NEWPICS%\_TRIALS\_DONE
        set NEW_TRIALS=_TRIALS
        set NEW_TRIALS_DONE=_TRIALS\_DONE
        if not isdir %NEW_TRIALS_DONE% goto :No_Done_New_Trials
            if not isdir %NEWPICS_TRIALS       (md %NEWPICS_TRIALS%     ) 
            if not isdir %NEWPICS_TRIALS_DONE% (md %NEWPICS_TRIALS_DONE%) 
            mv/ds        %NEW_TRIALS_DONE%         %NEWPICS_TRIALS_DONE%
            if not isdir %NEW_TRIALS_DONE%     (md %NEW_TRIALS_DONE%    )
        :No_Done_New_Trials


rem Ask to move all video to _ASSIMILATE, which is often the last and easiest way to free dropbox space:
        if not exist %FILEMASK_VIDEO (goto :NoVideo)
            if not isdir _ASSIMILATE (call error "_ASSIMILATE folder should definitely exist at this point in %0")
             if    isdir _ASSIMILATE (
                echos %@RANDFG[] 
                call divider
                call askyn "Move all videos out of dropbox" yes 120
                if %DO_IT eq 1 (
                    *move /g %FILEMASK_VIDEO% _ASSIMILATE
                )
            )
        :NoVideo

rem Ensure that the temporarily "_ASSIMILATE" folder exists:
        set NEWPICS_TO_BE=_ASSIMILATE 
        if isdir %NEWPICS_TO_BE% (
            mv/ds %NEWPICS_TO_BE% %NEWPICS% 
            if not isdir %NEWPICS_TO_BE% (md %NEWPICS_TO_BE%)
        )



rem Also ensure, yet again, that all the directories we need to process exist, so that we have them for the future:
        call ensure-directories-exist %FOLDERS_TO_PROCESS%

:The_End
    popd
    %COLOR_NORMAL%
    call display-size-of-current-folder-tree
