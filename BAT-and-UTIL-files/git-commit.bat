@Echo OFF

:20230307 seemed to work in t:\mp3-git-repo

REM Initialize git
    call git-setvars


REM Show modified/uncommitted files
    echo.
    call important "Here is the current status of our files:"
    call git.bat status --short | highlight "^ M.*$" | highlight "^A .*$"
    echo.


REM Get reason to commit
    set REASON=%1 
    if "%REASON%" eq "" .or. "%REASON%" eq "--verbose" (
        rem I liked this one:
                REM generate a very nice commit comment akin to "update on 2023/06/01 -- 5:14:10 PM -- Thursday /// README.md"
                REM call set-date-verynice
                REM call set-latestfile *.py;*.md;*.spec;*.exe;*.bat
                REM set REASON=%[latest_file] on %VERY_NICE_DATE% 
        rem But this one embraces the chaos that is my personality
            if %PATH_VALIDATED_GIT_COMMIT_VIP_SCPS ne 1 (
                call validate-in-path set-current_playing_song
                set PATH_VALIDATED_GIT_COMMIT_VIP_SCPS=1
            )
            call set-current_playing_song
            call set-nicetime
            set REASON=%_dow %nicetime: %currently_playing_song
    )
    if "%NOPAUSE%" ne "1" .and. "%1" ne "nopause" .and. %GIT_SKIP_COMMIT_REASON_EDIT ne 1 (
        call important "Enter your commit reason:"
        %COLOR_INPUT%
        call prompt-sound
        eset REASON
        REM don't turn off the flag here, even though that might be safer, because it would break calling this recursively on subfolders
    )


REM Generate commit command
UNSET /Q GIT_OPTIONS_TEMP
    set COMMITCOMMAND=call git commit -a -m "%REASON%" --verbose %GIT_OPTIONS_TEMP% 


REM Actually commit the files
    echo.
    call important "Committing files..."
    %COLOR_SUCCESS%
    %COMMITCOMMAND%
    REM git commit returns errorlevel if nothing to commit, so this isn't helpful: call errorlevel "git commit failed?!"
    REM                                                     ..........but this is: call errorlevel "there were no files to commit"
    call errorlevel "there were no files to commit" "%NEWLINE%%STAR% Commit was successful! %PARTY_POPPER%"


REM Remind that commit and push are not the same
    echo.
    call warning "The files were not uploaded, though"
    call advice "%To do that: '%italics%push%italics_off%' (which which executes '%italics%git push origin main%italics_off%')"
    if %NO_PAUSE ne 1 keystack push



