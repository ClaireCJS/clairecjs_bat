@on break cancel
@Echo OFF

rem *** CONFIGURATION: ***

    rem Echo each git command as it is issued:
        set DEBUG_GIT_COMMANDS=0

    rem Location of git.ee:
        set GIT_EXE=c:\UTIL2\git\bin\git.exe
        set GIT=%GET_EXE%
        set GIT_PYTHON_GIT_EXECUTABLE=%GIT%
        rem GIT_OUT=git.%_PID.%_DATETIME.out would be an ideal filename but these files are used elsewhere and we don't want to guess or store their name so let's just stick with git.out:
        set GIT_OUT=git.out
        set GIT_OUT_FILTERED=git2.out

rem *** GET USAGE: ***
    rem git init
    rem git add *
    rem git commit -m "initial add"
    rem git help:     Forgot a command? Type this into the command line to bring up the 21 most common git commands. You can also be more specific and type "git help init" or another term to figure out how to use and configure a specific git command.
    rem git config:   Short for "configure," this is most useful when you�re setting up Git for the first time.
    rem git status:   Check the status of your repository. See which files are inside it, which changes still need to be committed, and which branch of the repository you�re currently working on.
    rem git commit:   Git�s most important command. After you make any sort of change, you input this in order to take a "snapshot" of the repository. Usually it goes git commit -m "Message here." The -m indicates that the following section of the command should be read as a message.
    rem git checkout: Literally allows you to "check out" a repository that you are not currently inside. This is a navigational command that lets you move to the repository you want to check. You can use this command as git checkout master to look at the master branch, or git checkout cats to look at another branch.
    rem git merge:    When you�re done working on a branch, you can merge your changes back to the master branch, which is visible to all collaborators. git merge cats would take all the changes you made to the "cats" branch and add them to the master.
    rem git push:     If you�re working on your local computer, and want your commits to be visible online on GitHub as well, you "push" the changes up to GitHub with this command.
    rem git pull:     If you�re working on your local computer and want the most up-to-date version of your repository to work with, you "pull" the changes down from GitHub with this command.
    rem git branch:   Working with multiple collaborators and want to make changes on your own? This command will let you build a new branch, or timeline of commits, of changes and file additions that are completely your own. Your title goes after the command. If you wanted a new branch called "cats," you�d type git branch cats.


rem SETUP: Parameters and variables
    set ARGS=%*
    set ARGV1=%1
    set HOMEDRIVE=C:
    set TERM_TEMP=%TERM%
    set TERM=msys



    

rem ADVICE: Give it when appropriate
    if "%ARGV1" eq "rm"   (call important_less "adding '--cached' to 'rm' so we don't delete the local file" %+ set ARGV1=rm --cached %+ set ARGS=%@REPLACE[rm,rm --cached,%ARGS]) %+ REM Yeahhh, rm removes the file locally, and we don't want that! --cached just removes it from the repo
    if "%ARGV1" eq "pull" (call advice "'call git-config-set-commit-preferences-to-rebase' for 'you have divergent branches and need to specify how to reconcile them' situations")
    rem"%ARGV1" eq "push" (call subtle "If a pop-up comes up for credentials, choose manager-core twice")
    if "%ARGV1" eq "push" (call advice "If a pop-up comes up for credentials, choose manager-core twice")
    echo.
    if %DEBUG_GIT_COMMANDS eq 1 call subtle "%GIT_EXE% --no-pager %GIT_OPTIONS_TEMP% %ARGS%"



rem EXECUTE: Run our GIT command which won't work right without TERM=msys, filter out annoying warnings messages, check for errors

    rem BRANCHING: Anaconda needs to skip the more advanced command-line stuff, and pray
            call get-command-line
            goto :%OUR_COMMAND_LINE%

            :Anaconda
                echo Anaconda
                %GIT_EXE% --no-pager %GIT_OPTIONS_TEMP% %ARGS% 
            goto :END

    :TCC    
        call git-setvars
        %COLOR_RUN%         

        rem Output header:
                color bright blue on black
                echo %STAR% %DOUBLE_UNDERLINE%%ITALICS%%ANSI_BRIGHT_BLUE%Raw%ITALICS_OFF% GIT output%UNDERLINE_OFF%:
                rem color blue on black
                rem color cyan on black
                echos %@ANSI_FG[10,250,175]
                echo.
        
        rem Set up TEE:
                set TEE=*tee
                if exist   c:\cygwin\bin\tee.exe (set   TEE=c:\cygwin\bin\tee.exe)
                if exist c:\cygwin64\bin\tee.exe (set TEE=c:\cygwin64\bin\tee.exe)
                set TEECOLOR=%COLOR_UNIMPORTANT%
                rem NO! %TEECOLOR%
                
        rem Add --no-pager to git status commands, and display them our own way:
                iff "%1" eq "status" then
                        ((%GIT_EXE% --no-pager %GIT_OPTIONS_TEMP% %ARGS% |:u8 call highlight "^ *M.*$" |:u8 call highlight "^A *.*$" |&:u8 %tee% %GIT_OUT%) |:u8 cat_fast)
                        goto :git_status_skip_here
                else
                        ((%GIT_EXE% --no-pager %GIT_OPTIONS_TEMP% %ARGS%                                                             |&:u8 %tee% %GIT_OUT%) |:u8 cat_fast)
                endiff

        rem Size warning:
                rem if exist %GIT_OUT% .and. %@FILESIZE[%GIT_OUT] gt 0 (echo Some!)
                if not exist %GIT_OUT% .or.  %@FILESIZE[%GIT_OUT] eq 0 (echo None!)

        rem Potentially output the filtered output from our captured file for a more meaningful/processed set of output...
                iff     exist %GIT_OUT% .and. %@FILESIZE[%GIT_OUT] gt 0 then
                        ((type %GIT_OUT% |:u8 grep -v 'git-credential-manager-core was renamed to git-credential-manager') |:u8 grep -v 'https:..aka.ms.gcm.rename') >:u8%GIT_OUT_FILTERED%
                        
                        iff %@FILESIZE[%GIT_OUT%] eq %@FILESIZE[%GIT_OUT_FILTERED%] then                
                                rem Do nothing! We already displayed the unfiltered...
                        else
                                rem Filtered vs Non-filtered display:
                                echo.
                                color bright blue on black
                                echo %STAR% %DOUBLE_UNDERLINE%%ITALICS%%ANSI_BRIGHT_BLUE%Filtered%ITALICS_OFF% GIT output%UNDERLINE_OFF%:
                                echo.
                                iff exist %GIT_OUT_FILTERED% then
                                        echos %@ANSI_RGB[0,205,0]
                                        (type %GIT_OUT_FILTERED% |:u8 fast_cat)
                                endiff                                        
                                        rem piping to cat_fast fixes TCC+WT ansi rendering errors:
                                        rem (cat  %GIT_OUT% |:u8 grep -v 'git-credential-manager-core was renamed to git-credential-manager' |:u8 grep -v 'https:..aka.ms.gcm.rename') |:u8 cat_fast
                                        rem 2024/11/25 change from cat to type                    
                                        rem ((type %GIT_OUT% |:u8 grep -v 'git-credential-manager-core was renamed to git-credential-manager') |:u8 grep -v 'https:..aka.ms.gcm.rename') |:u8 cat_fast
                                        rem 2024/11/27 change to send to file, and moving upstream to diff first to see if we should bother with filter vs unfiltered {i.e. if both are the same}:
                                        rem endiff
                        else
                        endiff
                endiff
        
        :git_status_skip_here
        rem if exist %GIT_OUT%          (%COLOR_REMOVAL% %+ echo ray|del /q /r %GIT_OUT%         >nul)
        rem if exist %GIT_OUT_FILTERED% (%COLOR_REMOVAL% %+ echo ray|del /q /r %GIT_OUT_FILTERED%>nul)
        call errorlevel "a git error!?! how can this be?!?! Command line was: %0 %*"
    goto :END



:Done_With_Git
:END
    set TERM=%TERM_TEMP%


