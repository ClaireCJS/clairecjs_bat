@loadbtm on
@echo %ansi_color_bright_green%-—━━━━━━━━━━━━━━━RN.BAT: START -—━━━━━━━━━━━━━━━%ansi_color_normal%
@Echo off
@on break cancel

rem %COLOR_DEBUG% %+ echo * EXTRA_NAME is %EXTRA_NAME% ... YOUTUBE_MODE=%YOUTUBE_MODE% %+ %COLOR_NORMAL%
rem %COLOR_DEBUG% %+ echo ARGS: %*

rem Fix environment:
        if "0" == "%ansi_off%" call ansi-on
        rem No! Leave it! Worst that happens is an erroneous blank line! set SIDECARS_RENAMED=0


rem Validate environment (once):
        rem if "%ANSI_CURSOR_CHANGE_COLOR_WORD[]" == "" function ANSI_CURSOR_CHANGE_COLOR_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`
        iff "5" != "%validated_rn%" then
                rem pause "goat debug about to val function"
                call validate-is-function ANSI_CURSOR_CHANGE_COLOR_WORD
                rem pause "goat debug about to val env vars"
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET 
                rem pause "goat debug about to val path"
                call validate-in-path ansi-on ansi-off warning fatal_error set-cursor print-if-DEBUG print-message eset-alias
                set  validated_rn=5
        endiff

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
        if            "%1"   == ""   goto :END_of_rn
        if "%@UNQUOTE["%1"]" == "."  goto :END_of_rn
        if "%@UNQUOTE["%1"]" == ".." goto :END_of_rn
        if  not exist  %1 .and. not exist "%@UNQUOTE["%1"]"            goto :DNE

rem Get/react to recursive arguments:
                                                                           set END_NAME_SPECIFIED=0
        if "%2" != "" .and. "%1" != "recursive" .and. "%2" != "recursive" (set END_NAME_SPECIFIED=1)

rem Get/react to auto argument:
        if "%3" == "auto" set RN_SKIP_USER_EDIT=1
        if "%3" != "auto" set RN_SKIP_USER_EDIT=0


rem Count files matching parameter:
    set FILES=%@FILES["%@UNQUOTE[%1]"] 
    if defined debug call print-if-DEBUG "FILES is “%FILES%”"
    set ISDIR=0
    if  isdir    %1 goto :IsDir
    if %FILES% gt 1 goto :IsManyFiles
                    goto :IsSingleFile


rem React to count accordingly?
    :IsManyFiles
                for /a: %%fi in (%1)                                 echo call rn %as_instrmental_param% "%fi" %2 recursive
rem             for /a:  %fi in (%1) if exist %as_instrmental_param%      call rn %as_instrmental_param% "%fi" %2 recursive
                for /a:  %fi in (%1)                                      call rn %as_instrmental_param% "%fi" %2 recursive
            gosub :after
    goto :END_of_rn

    :IsDir
            set ISDIR=1
            rem ✨ ✨ ✨ ✨ ✨ We continue using the IsSinglefile code but with ISDIR set to 1: ✨ ✨ ✨ ✨ ✨ 

    :IsSingleFile
        rem Set rename command:
                set REN=*ren /Nts                                                      
                if "1" == "%ISDIR%" (
                                                                 set REN=  mv /ds /Ns
                        if "%3" == "fast"                       (set REN=*move/ds /Ns)
                )

        rem Save old filename:
                set                                               FILENAME_OLD=%@UNQUOTE["%1"]                             
                set            FILENAME_OLD_TRUENAME=%@TRUENAME["%FILENAME_OLD%"]                                            %+ if %DEBUG gt 0 (call print-if-DEBUG "[About to validate-env-var FILENAME_OLD_TRUENAME (%FILENAME_OLD_TRUENAME%)]")
                if not exist "%FILENAME_OLD_TRUENAME%" call validate-environment-variable FILENAME_OLD_TRUENAME

        rem Set new filename:
                color bright red on black 
                set                                   FILENAME_NEW=%FILENAME_OLD%        
                if "1" == "%END_NAME_SPECIFIED%" (set FILENAME_NEW=%2)
                if "1" == "%AS_INSTRUMENTAL%"    (set FILENAME_NEW="%@NAME["%FILENAME_NEW%"] [instrumental].%@EXT["%FILENAME_NEW%"]")
                rem DEBUG: echo filename_new is %lq%%filename_new%%rq% %+ pause




        rem Let user edit the filename: 
                rem Skip this if instructed...
                        if "%RN_SKIP_USER_EDIT%" == "1" goto :skip_rn_user_edit

                rem Let user edit the filename: first change cursor to yellow for the edit:
                        echos %@ANSI_CURSOR_CHANGE_COLOR_WORD[yellow]

                rem Let user edit the filename: set up flag to capture error in subordinate ESET script:
                        set rn_goto_end=0
                        set rn_fix_ansi=0

                rem Let user edit the filename: send them to the eset-alias.bat where they do the actual editing: 
                rem                       then: capture any errorlevel——probably due to user hitting Ctrl-Break:
                        call eset-alias FILENAME_NEW        
                        if "%_" == "667" .or. "1" == "%eset_fail%" (set rn_goto_end=1 %+ set rn_fix_ansi=1)
                                                                       
                rem Let user edit the filename: In order to edit ANSI codes that are environment varaibles, we always turn off ANSI when editing one
                rem                             Check if ANSI was not properly turned back on, probably due to user hitting Ctrl-Break:
                        if "1" == "%rn_fix_ansi%" .or. "1" == "%ansi_off%"  call ansi-on

                rem Let user edit the filename: Fix the cursor afteward
                       rem call set-cursor
                       echos %ANSI_COLOR_NORMAL%%CURSOR_RESET%%@ansi_move_to_col[1]

                rem Let user edit the filename: Skip the renaming if there was a Ctrl-Break from the eset-alias.bat, or errorlevel otherwise returned:
                        rem echo %@ansi_move_to_col[1]- DEBUG: errorlevel='%_errorlevel%' %%?='%?' %%_='%_?' ansi_off='%ansi_off%' rn_fix_ansi='%rn_fix_ansi%' rn_goto_end='%rn_goto_end%'
                        if "1" == "%rn_goto_end%" goto :END_of_rn

                rem End label:
                        :skip_rn_user_edit




        rem If the filename isn’t actually any different, then we don’t need to do anything (and warn them of that):
                                                                               set NAMES_MATCH_FOR_CASE_INSENSITIVE_COMPARISON=0
                if          "%FILENAME_NEW%"   ==          "%FILENAME_OLD%"    set NAMES_MATCH_FOR_CASE_INSENSITIVE_COMPARISON=1
                if          "%FILENAME_NEW%"   ==          "%FILENAME_OLD%"    set REN=*ren
                set NO_CHANGE=0
                if "%@ASCII["%FILENAME_NEW%"]" == "%@ASCII["%FILENAME_OLD%"]" (%COLOR_WARNING% %+ set NO_CHANGE=1 %+ echos * %ITALICS_ON%No change.%ITALICS_OFF% %+ %COLOR_NORMAL% %+ echo. %+ goto :END_of_rn)

        rem Store the command/undo command/redo commands, and the last filename we renamed something to (for auditing/integration purposes):
                set  UNDOCOMMAND=%REN% "%FILENAME_NEW%" "%@UNQUOTE[%FILENAME_OLD%]" 
                set      COMMAND=%REN% "%FILENAME_OLD%" "%@UNQUOTE[%FILENAME_NEW%]"      
                set  REDOCOMMAND=%COMMAND%   
                set LAST_RENAMED_TO=%@UNQUOTE["%FILENAME_NEW%"]

        rem Add any decorator we’ve defined for cosmetic porpuses:
                %COLOR_SUCCCESS%
                echos %FAINT_ON%%@RANDFG_SOFT[]%RN_DECORATOR%``

        rem Cosmetic line skip if last set had sidecars renamed:
                if "1" == "%SIDECARS_RENAMED%" echo.

        rem DO the acutal file renaming:
                REM echo y|%REDOCOMMAND%                                                 
                rem call debug "redo command is %blink_on%%REDOCOMMAND%%blink_off%"
                %COLOR_RUN%
                echos %blink_on%%bold_on%%STAR5% RENAMING:%bold_off% %blink_off%``
                %REDOCOMMAND%                                                 
                echos %FAINT_OFF%

        rem Make sure we actually succeeded in our renaming:
                iff not exist %FILENAME_NEW then
                        call fatal_error "%italics_on%FILENAME_NEW%italics_off% does not exist! %blink_off%'%filename_new%'%blink_off%"
                endiff

        rem Rename any existing sidecar/companion files
                :Rename_Sidecars_2024
                set SIDECARS_RENAMED=0
                setlocal enabledelayedexpansion

                        :RenameSidecars
                        set BASENAME_OLD=%~n1
                        set BASENAME_NEW=%@UNQUOTE[%@NAME["%FILENAME_NEW%"]]

                        for %%F in ("%~dp1%BASENAME_OLD%.*") do (
                            if "%%~nxF" neq "%FILENAME_OLD%" (
                                set "FILENAME_SIDECAR_OLD=%~dp1%%~nxF"
                                set "FILENAME_SIDECAR_NEW=%~dp1%BASENAME_NEW%%%~xF"
                                echo %ansi_color_debug%DEBUG: Checking sidecar file - %lq%!FILENAME_SIDECAR_OLD!%rq%
                                echo %ansi_color_debug%DEBUG: Renaming to ----------- %lq%!FILENAME_SIDECAR_NEW!%rq%
                                %COLOR_SUCCESS%        %+  echo      %ansi_color_bright_red%%star3% %ansi_color_green%Renaming sidecar file: %ansi_color_green%%italics_on%%faint_on%%@NAME[!FILENAME_SIDECAR_OLD!]%faint_off%%italics_off%
                                %COLOR_SUCCESS%        %+  echo      %ansi_color_green%%zzzzzzzzzzzzzzzzzzzzzzz%                     To: %italics_on%%faint_on%%@NAME[!FILENAME_SIDECAR_NEW!]%faint_off%%italics_off% %+ %COLOR_NORMAL%
                                %COLOR_SUBTLE%         %+  echos %FAINT_ON%%ITALICS_ON%                              ``

                                if not exist "!FILENAME_SIDECAR_OLD!" (
                                    call validate-environment-variable FILENAME_SIDECAR_OLD "Script currently doesn't rename sidecar files if they aren't in the current folder"
                                )

                                %REN% "!FILENAME_SIDECAR_OLD!" "!FILENAME_SIDECAR_NEW!"
                                set SIDECARS_RENAMED=1  

                                set "UNDOCOMMAND_SIDECAR=%REN% "!FILENAME_SIDECAR_NEW!" "!FILENAME_SIDECAR_OLD!""
                                set "REDOCOMMAND_SIDECAR=%REN% "!FILENAME_SIDECAR_OLD!" "!FILENAME_SIDECAR_NEW!""
                                rem echo %ansi_color_success% %cake%%party_popper% %Sidecar file renamed successfully!!! %party_popper%%cake% %ansi_color_normal%
                            ) else (
                                echo DEBUG: Skipping main file - %%~nxF matches %FILENAME_OLD%
                            )
                        )

                endlocal SIDECARS_RENAMED
                rem DEBUG: echo SIDECARS_RENAMED=%SIDECARS_RENAMED%

        rem Watch out for 0-byte versions of the original filename leftover due to filesystem locks:
                :check_that_it_is_actually_gone
                set old_file_seems_to_be_gone=0
                if "%@ASCII["%FILENAME_NEW%"]" == "%@ASCII["%FILENAME_OLD%"]"                   (set old_file_seems_to_be_gone=1) %+ rem This is the case of us not actually renaming it
                if "1"  ==   "%NO_CHANGE%"                                                      (set old_file_seems_to_be_gone=1)
                if not exist "%FILENAME_OLD%"                                                   (set old_file_seems_to_be_gone=1)
                if     exist "%FILENAME_OLD%"                                                   (set old_file_seems_to_be_gone=0)
                if     exist "%FILENAME_OLD%" .and. "%FILENAME_OLD%" == "%FILENAME_NEW%"        (set old_file_seems_to_be_gone=1)
                rem  debug: old_file_seems_to_be_gone==%lq%%old_file_seems_to_be_gone%%rq% %+ pause

                if "1" == "%old_file_seems_to_be_gone%" goto /i old_file_seems_to_be_gone
                        :we_are_not_fine
                        set HOLD_OUR_ANSWER=%ANSWER%
                        set  filename_old_size=%@FILESIZE["%FILENAME_OLD%"] 
                        set  filename_new_size=%@FILESIZE["%FILENAME_NEW%"] 
                        echo %ansi_color_warning_soft%%star2% %italics_on%FILENAME_OLD%italics_off% of %@COMMA[%filename_old_size%] bytes%ansi_color_warning_soft% still exists:%tab%%lq%%FILENAME_OLD%%rq%"
                        echo %ansi_color_advice%%zzzz%%star2% %italics_on%FILENAME_NEW%italics_off% of %@COMMA[%filename_new_size%] bytes%ansi_color_advice%%zzzz%  also exists:%tab%%lq%%FILENAME_NEW%%rq%"
                                                      set default_answer_to_use_for_deletion=no
                        if 0 eq %filename_old_size%   set default_answer_to_use_for_deletion=yes
                        call AskYN "Delete the old file" %default_answer_to_use_for_deletion% 60
                        %color_removal%
                        if "Y" == "%ANSWER%" *del "%FILENAME_OLD%"
                        %color_normal%
                        set ANSWER=%HOLD_OUR_ANSWER%
                        goto :check_that_it_is_actually_gone
                :old_file_seems_to_be_gone


            

goto /i :END_of_rn

rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :Rename_Sidecars_2022_OLD
            set BASENAME_OLD=%~n1
            set BASENAME_NEW=%@UNQUOTE[%@NAME["%FILENAME_NEW%"]]
            rem  pushd basedir
            for %%F in ("%~dp1%BASENAME_OLD%.*") do (
                if "%%~nxF" neq "%FILENAME_OLD%" (
                    set FILENAME_SIDECAR_OLD=%%~nxF
                    set FILENAME_SIDECAR_NEW=%BASENAME_NEW%%%~xF
                    %COLOR_SUCCESS%        %+   echo %FAINT_ON%     - Renaming sidecar file: %FILENAME_SIDECAR_OLD% 
                    %COLOR_SUCCESS%        %+   echo %FAINT_ON%                          To: %FILENAME_SIDECAR_NEW%%FAINT_OFF% %+ %COLOR_NORMAL%
                    %COLOR_SUBTLE%         %+  echos %FAINT_ON%%ITALICS_ON%                           ``
                    set comment=rem I’m not quite sure what we were validating here:
                    if not exist "%FILENAME_SIDECAR_OLD%"  call validate-environment-variable FILENAME_SIDECAR_OLD "Script currently doesn't rename sidecar files if they aren't in the current folder"
                                            %REN% "%FILENAME_SIDECAR_OLD%" "%FILENAME_SIDECAR_NEW%"
                    set UNDOCOMMAND_SIDECAR=%REN% "%FILENAME_SIDECAR_NEW%" "%FILENAME_SIDECAR_OLD%"
                    set REDOCOMMAND_SIDECAR=%REN% "%FILENAME_SIDECAR_OLD%" "%FILENAME_SIDECAR_NEW%"
                    echos %FAINT_OFF%%ITALICS_OFF%
                )
            )
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :DNE
                if "%3" == "recursive" goto :END_of_rn
                call warning "%faint_on%[rn]%faint_off% No action taken, because file does not exist: %lq%%1%rq% " 2
        goto :END_of_rn
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :oops_they_meant_to_do_ren_and_not_rn
                echo %ansi_color_warning_soft%%emoji_warning% Looks like you meant to use 'ren' and not 'rn', so we'll do that instead:
                echos %ansi_color_run%%star% ``
                ren "%@UNQUOTE["%1"]" "%@UNQUOTE["%2"]" 
                set UNDOCOMMAND=    ren "%@UNQUOTE["%2"]" "%@UNQUOTE["%1"]" 
                set LAST_RENAMED_TO=%@UNQUOTE[%2]
        goto :END_of_rn
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


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


:END_of_rn
        unset /q fix_run no_change
        iff "%1" == "" then 
                echo %ansi_color_fatal_error% rn %blink_on%WHAT?!%blink_off%?! %ansi_color_normal% *beep
                echo.
                echo %ansi_color_advice% USAGE: call rn {old_filename} - to interactivately rename it
                echo.
                echo %ansi_color_advice% USAGE: call rn {old_filename} {new_filename} - to behave like the “ren” command, but with the 
                echo %ansi_color_advice%                                                perks of the “rn” command, such as automatically 
                echo %ansi_color_advice%                                                renaming sidecar files and a chance for user-edit
                echo.
                echo %ansi_color_advice% USAGE: call rn {old_filename} {new_filename} auto - Like above, but skipping the user edit perk
                echo %ansi_color_advice%                                                     Great for renaming sidecar files
                echo.


RN_SKIP_USER_EDIT
        endiff

rem DEBUG:
        setdos /x-58
        rem   echo %ansi_color_debug%- DEBUG: filename_old of %lq%%FILENAME_OLD%%rq% does %@IF[not exist "%FILENAME_OLD%",not ,]exist [in %0:9554]     last_renamed_to=%lq%%last_renamed_to%%rq%
        set LAST_DEBUG_COMMENT_TO_SELF=DEBUG: filename_old of %lq%%FILENAME_OLD%%rq% does %@IF[not exist "%FILENAME_OLD%",not ,]exist [in %0:9554]     last_renamed_to=%lq%%last_renamed_to%%rq%
        setdos /x0


@echo %ansi_color_bright_green%-—━━━━━━━━━━━━━━━RN.BAT: END -—━━━━━━━━━━━━━━━%ansi_color_normal%
