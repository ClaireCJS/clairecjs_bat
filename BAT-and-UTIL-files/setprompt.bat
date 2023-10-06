@Echo OFF
:echo on
if "%DEBUG_DEPTH%" eq "1" echo * setprompt.bat (batch=%_BATCH)



:if "%1"                     eq "BROADWAY" goto :NoAnsiPrompt
:if "%@UPPER[%MACHINENAME%]" eq "BROADWAY" goto :NoAnsiPrompt

call checkusername.bat



if "%@UPPER[%MACHINENAME%]" eq "WORK" goto :work
                                      goto %USERNAME%


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