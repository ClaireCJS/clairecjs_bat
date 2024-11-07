@Echo Off



rem This is a ridiculous bat file!  Grew over decades, over different versions of EditPlus, 
rem including 2023 bugfix to workaround the EditPlus bug of the disallow multiple instances option not actually working.


::::: CONFIGURATION:
        :SUSPENDED: SET STARTOPTIONS=/min
        set TRADITIONAL_START=1

::::: SETUP:
        call get-command-line
        call nocar
        set DEBUG_LEVEL=unimportant

::::: BRANCH BASED ON PARAMETER:
        set ALL_ARGS=%*
        set ARGV1=%@UNQUOTE[%1]
        REM echo %DEBUG_LEVEL%: %0: all-args is %ALL_ARGS, %%ARGV1 is %ARGV1
        REM echo if "%ARGV1%" eq "USE EDITPLUS VERSION 3" 
        set NEW_INSTANCE=0
        if "%ARGV1%" eq "new" .or. "%ARGV1%" eq "new instance" set NEW_INSTANCE=1
        
        if "%ARGV1%" eq "USE EDITPLUS VERSION 3" (
            REM echo %DEBUG_LEVEL%: $0: editplus 3 override flagged
            set ALL_ARGS=%2$
            goto :v3
        )

::::: BRANCH BASED ON INSTALLED VERSION OR COMMAND-LINE:
        IF isdir "%util2%\Editplus 6"               goto :EditPlus6InUtil2
        if isdir "%[PROGRAMFILES]%\EditPlus 5"      goto :v5
        if "%OUR_COMMAND_LINE%" == "Anaconda"       goto :AnacondaStart
        :NO MORE!: if "%MACHINENAME"=="Hades"       goto :Hades
    REM if "%MACHINENAME%" eq "DEMONA"              goto :Demona
        if "%FOUR%" eq "YES" goto :v4
        if isdir "%[PROGRAMFILES(x86)]%\EditPlus 4" goto :v4
        if isdir  "%PROGRAMFILES%\EditPlus 2"       goto :v2
        if isdir  "%PROGRAMFILES%\EditPlus 3"       goto :v3
        if isdir "%[PROGRAMFILES(x86)]%\EditPlus 3" goto :v3b
        if isdir "%[PROGRAMFILES(x86)]%\EditPlus"   goto :vX

::::: IF NO BRANCH, WARN THAT WE ARE * Using THE DEFAULT:
        call warning "Using default editplus..."



        :EditPlus6InUtil2
            call %DEBUG_LEVEL% "Using UTIL2\EditPlus 6..."
            start %STARTOPTIONS% %@SFN["%UTIL2%\EditPlus 6\editplus.exe"]               %ALL_ARGS% %+ goto :END
	:default32bitOS
            call %DEBUG_LEVEL% "Using EditPlus Default32bitOS..."
            start %STARTOPTIONS% %@SFN["%PROGRAMFILES%\EditPlus\editplus.exe"]          %ALL_ARGS% %+ goto :END
	:v2
            call %DEBUG_LEVEL% "Using EditPlus 2..."
            start %STARTOPTIONS% %@SFN["%PROGRAMFILES%\EditPlus 2\editplus.exe"]        %ALL_ARGS% %+ goto :END
	:v3
            call %DEBUG_LEVEL% "Using EditPlus 3..."
            :tart %STARTOPTIONS% %@SFN["%PROGRAMFILES%\EditPlus 3\editplus.exe"]        %ALL_ARGS% %+ goto :END
            call wrapper start %STARTOPTIONS% "%PROGRAMFILES%\EditPlus 3\editplus.exe"  %ALL_ARGS% %+ goto :END
	:v3b
            call %DEBUG_LEVEL% "Using EditPlus 3B..."                                                      
            start %STARTOPTIONS% %@SFN["%[PROGRAMFILES(x86)]%\EditPlus 3\editplus.exe"] %ALL_ARGS% %+ goto :END
	:v4
            call sleep 1
            call %DEBUG_LEVEL% "Using EditPlus 4..."                                                      
            start %STARTOPTIONS% %@SFN["%[PROGRAMFILES(x86)]%\EditPlus 4\editplus.exe"] %ALL_ARGS% %+ goto :END
	:v5
            call %DEBUG_LEVEL% "Using EditPlus 5..."                                                      
            :tart %STARTOPTIONS% %@SFN["%[PROGRAMFILES]%\EditPlus 5\editplus.exe"]      %ALL_ARGS% %+ goto :END
            :tart %STARTOPTIONS%       "%[PROGRAMFILES]%\EditPlus 5\editplus.exe"       %ALL_ARGS% %+ goto :END
            set EDITPLUS_DIR=%[PROGRAMFILES]%\EditPlus 5\
            set EDITPLUS_EXE=%EDITPLUS_DIR%\EditPlus.exe
            call validate-environment-variable EDITPLUS_DIR EDITPLUS_EXE
            pushd .

            REM Calling 'EditPlus' with no options kept opening pesky new instances!
            if %NEW_INSTANCE eq 1 (
                    start /ELEVATED "%EDITPLUS_EXE%" 
            )

            if "%ALL_ARGS%" eq "" (
                REM If you run editplus.exe at the command line, it doesn't return the console unless you use the start command

                REM But if you use the start command, it creates multiple instances —— EVEN IF THAT FEATURE IS DISALLOWED IN EDTPLUS OPTIONS ——
                REM             if you start it off without any parameters.

                REM We got around this by not allowing EditPlus to start if no options were given, but this was not the preferred
                REM           solution because calling EditPlus with no parameters is usally how we open it!
                REM call %DEBUG_LEVEL% "- No options were given, so we aren't running EDITPLUS_EXE or we would create another instance."

                REM Finally, a kludgey solution was found. If no parameter is passed, open up EditPlus with a filename it can't
                REM            deal with.  It will open Editplus without creating a new instance, and give an error and a beep
                REM            that makes one want to hit the ESCAPE or ENTER key instinctively, after either of which we find 
                REM            ourselves in the exact situation that we've wanted to be this whole time -- focused on the 
                REM            **current**, **already-existing** instance of EditPlus rather than opening up a new one
                start /ELEVATED "%EDITPLUS_EXE%" "           !!!!!!!!!!!!!!!!!! HIT ESCAPE !!!!!!!!!!!!!!!!!!                     " 
            ) else (
                start /ELEVATED "%EDITPLUS_EXE%" %ALL_ARGS%
            )

            popd
            goto :END
	:vX
            call %DEBUG_LEVEL% "Using EditPlus X..."
            start %STARTOPTIONS% %@SFN["%[PROGRAMFILES(x86)]%\EditPlus\editplus.exe"]   %ALL_ARGS% %+ goto :END
	:Hades
            call %DEBUG_LEVEL% "Using EditPlus Hades..."
            start %STARTOPTIONS% %@SFN["%[PROGRAMFILES(x86)]%%\EditPlus\editplus.exe"]  %ALL_ARGS% %+ goto :END
	:Demona
            set EDITPLUSEXE=%@SFN["%PROGRAMFILES%\EditPlus 3\editplus.exe"]             
            call %DEBUG_LEVEL% Using EditPlus for Demona... %EDITPLUSEXE% %+ %COLOR_NORMAL%
            :call wrapper start %STARTOPTIONS% "%PROGRAMFILES%\EditPlus 3\editplus.exe" 
            :editplus.exe -a b.txt to add a file - but stil doesn't load it utf-8 like
            call debug "start %EDITPLUSEXE% %ALL_ARGS%"
                  start %EDITPLUSEXE% %ALL_ARGS% 
            goto :END
    :AnacondaStart
            echo * TODO edit this and make it work with editplus 5
            set EDITPLUSEXE="%PROGRAMFILES%\EditPlus 3\editplus.exe"
            %EDITPLUSEXE% %ALL_ARGS%
            goto :Anaconda_END



:END

rem CLEANUP:
        if "%MINIMIZE_AFTER" eq "1" windowhide.exe /min *EditPlus
        unset /q STARTOPTIONS

:Anaconda_END

rem AUDIT:
        set LAST_TEXTEDITOR_PARAMETERS_EDITPLUS=%ALL_ARGS%

