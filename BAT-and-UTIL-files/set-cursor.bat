@Echo OFF

rem If we're running this outside of TCC, skip this behavior:
        if "%comspec%" == "C:\Windows\system32\cmd.exe " goto :DoNotBother

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
