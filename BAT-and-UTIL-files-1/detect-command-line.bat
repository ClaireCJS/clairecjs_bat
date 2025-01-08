@Echo off
 on break cancel

:DESCRIPTION: Detects command line and sets OUR_COMMAND_LINE to one of the following values: CMD PowerShell Anaconda bash TCC.
rem           This one was tough to write, because it needs to run in all those command lines as well. Nigh impossible, but this is close.


setdos /x0

set ECHO=REM

%COLOR_UNIMPORTANT%

set OUR_COMMAND_LINE=unknown


if "%_4ver%" neq "" (
    %ECHO% You are running TCC.
    set OUR_COMMAND_LINE=TCC
    goto :END
)

if "%CONDA_DEFAULT_ENV%"=="" (
    if "%TCCRTVER%"=="" (
        if "%MSYSTEM%"=="MINGW64" (
            %ECHO% * You are running Bash on Windows using Git Bash.
            set OUR_COMMAND_LINE=bash
            goto :END
        ) else (
            %ECHO% * You are using PowerShell.
            set OUR_COMMAND_LINE=PowerShell
            REM goto :END
        )
    ) else (
        %ECHO% * You are using TCC.
        set OUR_COMMAND_LINE=TCC
        goto :END
    )
) else (
    %ECHO% * You are using the Anaconda command line.
    set OUR_COMMAND_LINE=Anaconda
    goto :END
)



if "%ComSpec%"=="%SystemRoot%\system32\cmd.exe" ( %ECHO% * You are running CMD. )
if "%ComSpec%"=="%SystemRoot%\system32\cmd.exe" ( set OUR_COMMAND_LINE=CMD)
:if "%ComSpec%"=="%SystemRoot%\system32\cmd.exe" ( goto :END)
if   "%ComSpec%"=="C:\WINDOWS\system32\cmd.exe" ( %ECHO% * You are running CMD. )
if   "%ComSpec%"=="C:\WINDOWS\system32\cmd.exe" ( set OUR_COMMAND_LINE=CMD )
:if   "%ComSpec%"=="C:\WINDOWS\system32\cmd.exe" ( goto :END )

%ECHO% check mingw
if "%MSYSTEM%"=="MINGW64" (
    %ECHO% * You are running Bash on Windows using Git Bash.
    set OUR_COMMAND_LINE=bash
    goto :END
) else (
    %ECHO% * You are not running Bash on Windows.
)


:END


:The_Very_End
    @%ECHO% - WARNING: Cannot properly detect powershell.
    @%ECHO% * %%OUR_COMMAND_LINE%% has been set to "%OUR_COMMAND_LINE%"
 


set POWERSHELLTEST = $host.Name
%ECHO% POWERSHELLTEST is %POWERSHELLTEST%
:if(($host.Name -match 'consolehost')) { set OUR_COMMAND_LINE=bleorp }

%COLOR_NORMAL%

