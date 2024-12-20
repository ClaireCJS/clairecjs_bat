@Echo OFF
@on break cancel

:%COLOR_DEBUG% %+ echo * EXTRA_NAME is %EXTRA_NAME% ... YOUTUBE_MODE=%YOUTUBE_MODE% %+ %COLOR_NORMAL%
:%COLOR_DEBUG% %+ echo ARGS: %*

:::: Do nothing when passed these arguments:
    if           "%1"  eq ""   goto :END
    if "%@UNQUOTE[%1]" eq "."  goto :END
    if "%@UNQUOTE[%1]" eq ".." goto :END
    if not exist  %1           goto :DNE

:::: Get/react to arguments:
    rem OLD ne "" .and. "%1" ne "recursive" .and. "%2" ne "recursive" goto :oops_they_meant_to_do_ren_and_not_rn
                                                                       set END_NAME_SPECIFIED=0
    if "%2" ne "" .and. "%1" ne "recursive" .and. "%2" ne "recursive" (set END_NAME_SPECIFIED=1)
    set FILES=%@FILES[%1]                                                                                                              %+ call print-if-debug * FILES is %FILES%
    set ISDIR=0
    if  isdir    %1 goto :IsDir
    if %FILES% gt 1 goto :IsManyFiles
                    goto :IsSingleFile

        :IsManyFiles
            :cho for /a: %%fi in (%1) call rn "%fi" %2 recursive
                 for /a:  %fi in (%1) call rn "%fi" %2 recursive
            gosub :after
        goto :END

        :IsDir
            set ISDIR=1
        :IsSingleFile
            set REN=*ren /Nts
            if %ISDIR eq 1 (
                                   set REN=  mv /ds /Ns
                if "%3" eq "fast" (set REN=*move/ds /Ns)
            )
            set  FILENAME_OLD=%@UNQUOTE[%1]                             
                    :et  FILENAME_OLD_TRUENAME=%@TRUENAME["%1"]
                    set  FILENAME_OLD_TRUENAME=%@TRUENAME["%FILENAME_OLD%"]
                    if %DEBUG gt 0 (call print-if-debug "[About to validate-env-var FILENAME_OLD_TRUENAME (%FILENAME_OLD_TRUENAME%)]")
                    call validate-environment-variable FILENAME_OLD_TRUENAME
            color bright red on black 
            set  FILENAME_NEW=%FILENAME_OLD%        
            if %END_NAME_SPECIFIED eq 1 ( set FILENAME_NEW=%2)
            if %END_NAME_SPECIFIED ne 1 (
                    eset FILENAME_NEW
                    call set-cursor
            )
            %COLOR_RUN%
            if "%FILENAME_NEW%" eqc "%FILENAME_OLD%" (%COLOR_WARNING% %+ echos * %ITALICS_ON%No change.%ITALICS_OFF% %+ %COLOR_NORMAL% %+ echo. %+ goto :END)
            set  UNDOCOMMAND=%REN% "%FILENAME_NEW%" "%@UNQUOTE[%FILENAME_OLD%]" 
            set  REDOCOMMAND=%REN% "%FILENAME_OLD%" "%@UNQUOTE[%FILENAME_NEW%]"      %+ if "%DEBUG%" eq "1" (echo [DEBUG] About to: %REDOCOMMAND% %+ pause)
                                 set LAST_RENAMED_TO=%@UNQUOTE[%FILENAME_NEW%]

                %COLOR_SUCCCESS%
                echos %FAINT_ON%%@RANDFG_SOFT[]%RN_DECORATOR% ``
                REM echo y|%REDOCOMMAND%                                                 
                rem call debug "redo command is %blink_on%%REDOCOMMAND%%blink_off%"
                %REDOCOMMAND%                                                 
                echos %FAINT_OFF%
                if not exist %FILENAME_NEW (call fatal_error "filename_new does not exist! %blink_off%%filename_new%%blink_off%")

        :RenameCompanions
            set BASENAME_OLD=%~n1
            set BASENAME_NEW=%@NAME[%FILENAME_NEW%]
            for %%F in ("%~dp1%BASENAME_OLD%.*") do (
                if "%%~nxF" neq "%FILENAME_OLD%" (
                    set FILENAME_COMPANION_OLD=%%~nxF
                    set FILENAME_COMPANION_NEW=%BASENAME_NEW%%%~xF
                    %COLOR_SUCCESS%        %+  echo %FAINT_ON%     - Renaming sidecar file: %FILENAME_COMPANION_OLD% 
                    %COLOR_SUCCESS%        %+  echo %FAINT_ON%                          To: %FILENAME_COMPANION_NEW%%FAINT_OFF% %+ %COLOR_NORMAL%
                    %COLOR_SUBTLE%         %+  echos %FAINT_ON%%ITALICS_ON%                           ``
                    call validate-environment-variable FILENAME_COMPANION_OLD "Script currently doesn't rename companion files if they aren't in the current folder"
                                              %REN% "%FILENAME_COMPANION_OLD%" "%FILENAME_COMPANION_NEW%"
                    set UNDOCOMMAND_COMPANION=%REN% "%FILENAME_COMPANION_NEW%" "%FILENAME_COMPANION_OLD%"
                    set REDOCOMMAND_COMPANION=%REN% "%FILENAME_COMPANION_OLD%" "%FILENAME_COMPANION_NEW%"
                    echos %FAINT_OFF%%ITALICS_OFF%
                )
            )


            
            gosub :after
        goto :END


        :DNE
                if "%3" eq "recursive" goto :END
                call warning "No action taken, because file does not exist: %1 " 2
        goto :END

        :oops_they_meant_to_do_ren_and_not_rn
                %COLOR_WARNING%  %+ echo * Looks like you meant to use 'ren' and not 'rn', so we'll do that instead:
                %COLOR_RUN%      %+ ren "%@UNQUOTE[%1]" "%@UNQUOTE[%2]" 
                set UNDOCOMMAND=    ren "%@UNQUOTE[%2]" "%@UNQUOTE[%1]" 
                set LAST_RENAMED_TO=%@UNQUOTE[%2]
        goto :END

        :after
            if "%AFTER_PRE%" eq ""  .and. "%AFTER_POST%" eq "" goto :NoAfter
                %AFTER_PRE% %NEW_FILENAME% %AFTER_POST%
                set LAST_RN_AFTER_PRE=%LAST_AFTER_PRE%
                set LAST_RN_AFTER_POST=%LAST_AFTER_POST%
                unset /q AFTER_PRE
                unset /q AFTER_POST
            :NoAfter
        return
:END

