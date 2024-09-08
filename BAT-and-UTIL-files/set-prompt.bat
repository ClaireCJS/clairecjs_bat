@Echo OFF

rem If we're running this outside of TCC, just do a generic prompt:
        if "%comspec%" == "C:\Windows\system32\cmd.exe " goto :NoAnsiPrompt

rem Debug stuff:
        if "%DEBUG_DEPTH%" eq "1" (echo * setprompt.bat (batch=%_BATCH))



rem Machine-specific exceptions can go here:
        :if "%1" eq "BROADWAY" .or. "%@UPPER[%MACHINENAME%]" eq "BROADWAY" (goto :NoAnsiPrompt)
        if "%@UPPER[%MACHINENAME%]" eq "WORK"                              (goto :work)



rem Branch to the current user's custom prompt:
        if defined USERNAME (goto %USERNAME%)

rem If we managed to get here, just continue on and use Claire's prompt:
		:claire
		:clio
			call prompt-Claire.bat
		goto :end

		:carolyn
			call prompt-Carolyn.bat
		goto :end

		:work
			call prompt-work.bat
		goto :end

        :NoAnsiPrompt
            prompt=$l$t$h$h$h$g $P$G
		goto :end

:end
