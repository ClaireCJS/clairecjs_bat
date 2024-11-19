@Echo OFF
@on break cancel

rem If we're running this outside of TCC, skip this behavior:
        if "%comspec%" == "C:\Windows\system32\cmd.exe " goto :DoNotBother


rem Requires set-ansi to have been run:
        if "%ANSI_COLORS_HAVE_BEEN_SET%" != "1" (call warning "Ansi should have been set before running %0... Running now" %+ call set-ansi force)

rem Debug stuff:
        if "%DEBUG_DEPTH%" eq "1" (echo * se-tcursor.bat (batch=%_BATCH))

rem Machine-specific exceptions can go here:
        rem %1" eq "BROADWAY" .or. "%@UPPER[%MACHINENAME%]" eq "BROADWAY" (goto :DoNotBother)
        if  "%@UPPER[%MACHINENAME%]" eq "WORK"                            (goto :work       )

rem Branch to the current user's custom cursor:
        if defined USERNAME (goto %USERNAME%)

rem If we managed to get here, just continue on and use Claire's cursor:
		:claire
		:clio
			call cursor-Claire.bat
		goto :end

		:carolyn
			call cursor-Carolyn.bat
		goto :end

		:work
			call cursor-work.bat
		goto :end

        :DoNotBother            
        rem Don't do anything!
		goto :end

:end

rem This should adjust to the %ANSI_PREFERRED_CURSOR_COLOR_HEX% & %ANSI_PREFERRED_CURSOR_SHAPE% in environm.btm:
        set CURSOR_RESET=%@SET_CURSOR_COLOR_BY_HEX[%ANSI_PREFERRED_CURSOR_COLOR_HEX]%ANSI_PREFERRED_CURSOR_SHAPE%

rem But this is hard-coded to Claire's personal colors as a backup...
        set CUROSR_RESET_CLAIRE_HARDCODED=%@CHAR[27][ q%@CHAR[27]]12;#CF5500%@char[7]%@CHAR[27][1 q


rem Keep track that we've already set our cursor:
        set CURSOR_SET=1

