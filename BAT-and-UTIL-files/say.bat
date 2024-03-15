@Echo off 

:::::: Determine if we are using Cygwin's banner.exe, 
:::::: or standalone banner.exe from 2010ish,
:::::: or standalone say.com DOS version from the 1990s
    if "%CYGWIN" == "0"        (goto :Standalone_Banner_EXE)
    if "%CYGWIN" ne ""         (goto :CygWin_Banner_EXE    )
    if exist %UTIL%\banner.exe (goto :Standalone_Banner_EXE)
                               (goto :DOS_Version          )

	:CygWin_Banner_EXE
        ::::: Double check that the EXE is actually there, since 
        ::::: it isn't necessarily in a default cygwin installation:
            set BANNER=c:\cygwin\bin\banner.exe
            if not exist %BANNER% (goto :Standalone_Banner_EXE)

        ::::: Use internal %_COLUMNS var to set width of banner
            set WIDTH=%@EVAL[%_COLUMNS - 1]
            %BANNER% -c# --width=%WIDTH% %*
	goto :END

	:Standalone_Banner_EXE
        %UTIL%\banner.exe %*
	goto :END

	:DOS_Version
        %UTIL%\sayold.com %*
	goto :END

:END