@Echo off 

:::::: Determine if we are using Cygwin's banner.exe, 
:::::: or standalone banner.exe from 2010ish,
:::::: or standalone say.com DOS version from the 1990s
    if "%CYGWIN" == "0"        (goto :Standalone_Banner_EXE)
    if "%CYGWIN" ne ""         (goto :CygWin_Banner_EXE    )
    if exist %UTIL%\banner.exe (goto :Standalone_Banner_EXE)
                               (goto :DOS_Version          )

    set WIDTH=%@EVAL[%_COLUMNS - 1]

	:CygWin_Banner_EXE
        rem Double check that the EXE is actually there, since 
        rem it isn't necessarily in a default cygwin installation:
            set CYGWIN_BANNER=c:\cygwin\bin\banner.exe
            if not exist %CYGWIN_BANNER% (goto :Standalone_Banner_EXE)

        rem Use internal %_COLUMNS var to set width of banner
            %CYGWIN_BANNER% -cO --width=%WIDTH% %* |:u8 sed -e "s/[^ ]/█/g"
            rem # was our character for a long time, but O is more readable
	goto :END

	:Standalone_Banner_EXE
        set                                 STANDALONE_BANNER=%UTIL%\banner.exe 
        call validate-environment-variables STANDALONE_BANNER  UTIL  WIDTH
        %STANDALONE_BANNER% -cO --w %WIDTH% %*
	goto :END

	:DOS_Version
        call warning "this doesn't work anymore"
        %UTIL%\sayold.com %*
        pause
	goto :END

:END
echos %@ANSI_MOVE_UP[1]