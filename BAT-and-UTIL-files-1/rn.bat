@Echo OFF
@on break cancel
@loadbtm on

rem %COLOR_DEBUG% %+ echo * EXTRA_NAME is %EXTRA_NAME% ... YOUTUBE_MODE=%YOUTUBE_MODE% %+ %COLOR_NORMAL%
rem %COLOR_DEBUG% %+ echo ARGS: %*


rem Validate environment (once):
        rem if "%ANSI_CURSOR_CHANGE_COLOR_WORD[]" == "" function ANSI_CURSOR_CHANGE_COLOR_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`
        call validate-is-function ANSI_CURSOR_CHANGE_COLOR_WORD
        rem iff 1 ne %validated_rn_1% then
        rem        set  validated_rn_1=1
        rem endiff

rem Get/react to instrumental arguments:
        iff "%1" == "as_instrumental" then
                shift
                set as_instrumental=1
                set as_instrmental_param=as_instrumental
                set instrumental_text= [instrumental]
        else
                set as_instrumental=0
                unset /q as_instrmental_param
                unset /q instrumental_text
        endiff

rem Get/react to these arguments that we should do nothing if passed:
        if            "%1"   == ""   goto :END
        if "%@UNQUOTE["%1"]" == "."  goto :END
        if "%@UNQUOTE["%1"]" == ".." goto :END
        if  not exist  %1            goto :DNE

rem Get/react to recursive arguments:
        rem OLD != "" .and. "%1" != "recursive" .and. "%2" != "recursive" goto :oops_they_meant_to_do_ren_and_not_rn
                                                                       set END_NAME_SPECIFIED=0
        if "%2" != "" .and. "%1" != "recursive" .and. "%2" != "recursive" (set END_NAME_SPECIFIED=1)

rem Count files matching parameter:
    set FILES=%@FILES["%@UNQUOTE[%1]"]                                                                                                              %+ call print-if-debug * FILES is %FILES%
    set ISDIR=0
    if  isdir    %1 goto :IsDir
    if %FILES% gt 1 goto :IsManyFiles
                    goto :IsSingleFile

    :IsManyFiles
            :cho for /a: %%fi in (%1) call rn %as_instrmental_param% "%fi" %2 recursive
                 for /a:  %fi in (%1) call rn %as_instrmental_param% "%fi" %2 recursive
            gosub :after
    goto :END

    :IsDir
            set ISDIR=1
            rem We continue using the IsSinglefile code but with ISDIR set to 1:

    :IsSingleFile
        rem Set rename command:
                set REN=*ren /Nts                                                      
                if %ISDIR eq 1 (
                                           set REN=  mv /ds /Ns
                        if "%3" == "fast" (set REN=*move/ds /Ns)
                )

        rem Save old filename:
                set                                               FILENAME_OLD=%@UNQUOTE["%1"]                             
                set            FILENAME_OLD_TRUENAME=%@TRUENAME["%FILENAME_OLD%"]                                            %+ if %DEBUG gt 0 (call print-if-debug "[About to validate-env-var FILENAME_OLD_TRUENAME (%FILENAME_OLD_TRUENAME%)]")
                if not exist "%FILENAME_OLD_TRUENAME%" call validate-environment-variable FILENAME_OLD_TRUENAME

        rem Set new filename:
                color bright red on black 
                set                                   FILENAME_NEW=%FILENAME_OLD%        
                if "1" == "%END_NAME_SPECIFIED%" (set FILENAME_NEW=%2)
                if "1" == "%AS_INSTRUMENTAL%"    (set FILENAME_NEW="%@NAME["%FILENAME_NEW%"] [instrumental].%@EXT["%FILENAME_NEW%"]")
                rem DEBUG: echo filename_new is %lq%%filename_new%%rq% %+ pause

        rem Let user edit the filename:
                echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[yellow]
                eset FILENAME_NEW
                call set-cursor

        rem If the filename isn’t actually any different, then we don’t need to do anything (and warn them of that):
                if "%FILENAME_NEW%" == "%FILENAME_OLD%" (%COLOR_WARNING% %+ echos * %ITALICS_ON%No change.%ITALICS_OFF% %+ %COLOR_NORMAL% %+ echo. %+ goto :END)

        rem Store the command/undo command/redo commands, and the last filename we renamed something to (for auditing/integration purposes):
                set  UNDOCOMMAND=%REN% "%FILENAME_NEW%" "%@UNQUOTE[%FILENAME_OLD%]" 
                set      COMMAND=%REN% "%FILENAME_OLD%" "%@UNQUOTE[%FILENAME_NEW%]"      
                set  REDOCOMMAND=%COMMAND%   
                set LAST_RENAMED_TO=%@UNQUOTE["%FILENAME_NEW%"]

        rem Add any decorator we’ve defined for cosmetic porpuses:
                %COLOR_SUCCCESS%
                echos %FAINT_ON%%@RANDFG_SOFT[]%RN_DECORATOR% ``

        rem DO the acutal file renaming:
                REM echo y|%REDOCOMMAND%                                                 
                rem call debug "redo command is %blink_on%%REDOCOMMAND%%blink_off%"
                %COLOR_RUN%
                %REDOCOMMAND%                                                 
                echos %FAINT_OFF%

        rem Make sure we actually succeeded in our renaming:
                if not exist %FILENAME_NEW (call fatal_error "filename_new does not exist! %blink_off%%filename_new%%blink_off%")

        rem Rename any existing sidecar/companion files
        goto :NewMethodTest

        :RenameSidecars
            set BASENAME_OLD=%~n1
            set BASENAME_NEW=%@UNQUOTE[%@NAME["%FILENAME_NEW%"]]
            rem goat pushd basedir
            for %%F in ("%~dp1%BASENAME_OLD%.*") do (
                if "%%~nxF" neq "%FILENAME_OLD%" (
                    set FILENAME_SIDECAR_OLD=%%~nxF
                    set FILENAME_SIDECAR_NEW=%BASENAME_NEW%%%~xF
                    %COLOR_SUCCESS%        %+  echo %FAINT_ON%     - Renaming sidecar file: %FILENAME_SIDECAR_OLD% 
                    %COLOR_SUCCESS%        %+  echo %FAINT_ON%                          To: %FILENAME_SIDECAR_NEW%%FAINT_OFF% %+ %COLOR_NORMAL%
                    %COLOR_SUBTLE%         %+  echos %FAINT_ON%%ITALICS_ON%                           ``
                    set comment=rem I’m not quite sure what we were validating here:
                    if not exist "%FILENAME_SIDECAR_OLD%"  call validate-environment-variable FILENAME_SIDECAR_OLD "Script currently doesn't rename sidecar files if they aren't in the current folder"
                                            %REN% "%FILENAME_SIDECAR_OLD%" "%FILENAME_SIDECAR_NEW%"
                    set UNDOCOMMAND_SIDECAR=%REN% "%FILENAME_SIDECAR_NEW%" "%FILENAME_SIDECAR_OLD%"
                    set REDOCOMMAND_SIDECAR=%REN% "%FILENAME_SIDECAR_OLD%" "%FILENAME_SIDECAR_NEW%"
                    echos %FAINT_OFF%%ITALICS_OFF%
                )
            )
            rem goat popd

        :NewMethodTest
                setlocal enabledelayedexpansion

                :RenameSidecars
                set BASENAME_OLD=%~n1
                set BASENAME_NEW=%@UNQUOTE[%@NAME["%FILENAME_NEW%"]]

                for %%F in ("%~dp1%BASENAME_OLD%.*") do (
                    if "%%~nxF" neq "%FILENAME_OLD%" (
                        set "FILENAME_SIDECAR_OLD=%~dp1%%~nxF"
                        set "FILENAME_SIDECAR_NEW=%~dp1%BASENAME_NEW%%%~xF"

                        echo DEBUG: Checking sidecar file - !FILENAME_SIDECAR_OLD!
                        echo DEBUG: Renaming to - !FILENAME_SIDECAR_NEW!
                        %COLOR_SUCCESS%        %+  echo %FAINT_ON%     - Renaming sidecar file: !FILENAME_SIDECAR_OLD%!
                        %COLOR_SUCCESS%        %+  echo %FAINT_ON%                          To: !FILENAME_SIDECAR_NEW!%FAINT_OFF% %+ %COLOR_NORMAL%
                        %COLOR_SUBTLE%         %+  echos %FAINT_ON%%ITALICS_ON%                           ``

                        if not exist "!FILENAME_SIDECAR_OLD!" (
                            call validate-environment-variable FILENAME_SIDECAR_OLD "Script currently doesn't rename sidecar files if they aren't in the current folder"
                        )

                        %REN% "!FILENAME_SIDECAR_OLD!" "!FILENAME_SIDECAR_NEW!"

                        set "UNDOCOMMAND_SIDECAR=%REN% "!FILENAME_SIDECAR_NEW!" "!FILENAME_SIDECAR_OLD!""
                        set "REDOCOMMAND_SIDECAR=%REN% "!FILENAME_SIDECAR_OLD!" "!FILENAME_SIDECAR_NEW!""

                        echo Sidecar file renamed successfully.
                    ) else (
                        echo DEBUG: Skipping main file - %%~nxF matches %FILENAME_OLD%
                    )
                )

                endlocal

            
        gosub :after


goto :END

rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :DNE
                if "%3" == "recursive" goto :END
                call warning "No action taken, because file does not exist: %1 " 2
        goto :END
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :oops_they_meant_to_do_ren_and_not_rn
                %COLOR_WARNING%  %+ echo * Looks like you meant to use 'ren' and not 'rn', so we'll do that instead:
                %COLOR_RUN%      %+ ren "%@UNQUOTE["%1"]" "%@UNQUOTE["%2"]" 
                set UNDOCOMMAND=    ren "%@UNQUOTE["%2"]" "%@UNQUOTE["%1"]" 
                set LAST_RENAMED_TO=%@UNQUOTE[%2]
        goto :END
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :after
            if "%AFTER_PRE%" == ""  .and. "%AFTER_POST%" == "" goto :NoAfter
                %AFTER_PRE% %NEW_FILENAME% %AFTER_POST%
                set LAST_RN_AFTER_PRE=%LAST_AFTER_PRE%
                set LAST_RN_AFTER_POST=%LAST_AFTER_POST%
                unset /q AFTER_PRE
                unset /q AFTER_POST
            :NoAfter
        return
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:END

