@Echo OFF

:20230307 seemed to work in t:\mp3-git-repo

REM Initialize git
    call git-setvars

REM run any pre-commit scripts
    if exist pre-commit.bat (call pre-commit.bat)
    if exist  precommit.bat (call  precommit.bat)
    

REM Show modified/uncommitted files
    echo.
    call important "Here is the current status of our files:"
    call git.bat status --short 
    call errorlevel
    echo.


REM Get reason to commit
    set REASON=%1 
    :Get_Reason
    if "%REASON%" eq "" .or. "%REASON%" eq "--verbose" (
        rem I liked this one:
                REM generate a very nice commit comment akin to "update on 2023/06/01 -- 5:14:10 PM -- Thursday /// README.md"
                REM call set-date-verynice
                REM call set-latestfile *.py;*.md;*.spec;*.exe;*.bat
                REM set REASON=%[latest_file] on %VERY_NICE_DATE% 
        rem But this one embraces the chaos that is my personality
            if %PATH_VALIDATED_GIT_COMMIT_VIP_SCPS ne 1 (
                call validate-in-path set-current_playing_song git.bat
                set PATH_VALIDATED_GIT_COMMIT_VIP_SCPS=1
            )
            call set-current_playing_song
            call set-nicetime
            set REASON=%_dow %nicetime: %@unquote[%currently_playing_song]
    )
    if "%NOPAUSE%" ne "1" .and. "%1" ne "nopause" .and. %GIT_SKIP_COMMIT_REASON_EDIT ne 1 (
        if "%1" ne "" (
            if "%1" ne "auto" .and. "%1" eq "" (                                   eset REASON %+ set EDIT=1)
            if "%1" ne "auto" .and. "%1" ne "" (set REASON=%* %EMDASH% %REASON% %+ eset REASON %+ set EDIT=1)
            if "%1" eq "auto" .and. "%2" ne "" (set REASON=%* %EMDASH% %REASON%                %+ set EDIT=0)
            if "%1" eq "auto" .and. "%2" eq "" (set EDIT=0                                                  ) %+ rem (reason remains its pre-existing value)
            if %EDIT eq 1 (
                echo.
                call important "Enter your commit reason:"
                %COLOR_INPUT%
                rem  window restore
                call window-restore
                rem  prompt-sound "Enter commit reason:" —— got tired of waiting for this to play before proceeding!
                call prompt-sound silent
                eset REASON
            ) else (
                echo.
                echo %ANSI_COLOR_SUBTLE%*%faint_on% Used automatic commit reason of:%faint_off%%NEWLINE%%TAB%%TAB%%italics_on%%REASON%%italics_off%%ANSI_RESET%
            )
        )       
        REM don't turn off the flag here, even though that might be safer, because it would break calling this recursively on subfolders
    )
    if "%REASON%" == "" (call warning "Reason must be provided!" %+ pause %+ goto :Get_Reason)


REM Generate commit command
UNSET /Q GIT_OPTIONS_TEMP
    set COMMITCOMMAND=call git.bat commit -a -m "%REASON%" --verbose %GIT_OPTIONS_TEMP% 


REM Actually commit the files
    echo.
    call important "Committing files..."
    %COLOR_SUCCESS%
    %COMMITCOMMAND%
    REM git commit returns errorlevel if nothing to commit, so this isn't helpful: call errorlevel "git commit failed?!"
    REM                                                     ..........but this is: call errorlevel "there were no files to commit"
    call errorlevel "there were no files to commit" "%NEWLINE%%STAR% %blink_on%Commit was successful!%blink_off% %PARTY_POPPER%"


REM Remind that commit and push are not the same
    if %no_push_warning ne 1 (
            echo.
            call warning "The files were not uploaded, though"
            call advice "%To do that: '%italics%push%italics_off%' (which which executes '%italics%git push origin main%italics_off%')"
            rem This option meant to expire after single use:
            unset /q no_push_warning
    )


:END
    rem this interfered when using this as a subordinate bat:  if %NOPAUSE ne 1 (keystack push)


