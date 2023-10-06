@echo off

if "%USERNAME"=="" goto :bad
                   goto :good


:bad
	echo.
	echo.
	echo ERROR!!!!!!!!!!!!!!
	echo.
	echo     You do not have %%USERNAME defined!
	echo     This would normally be 'Claire' or 'carolyn'
	echo     This is required; please set this now.
	echo     Make sure you do it right the first time; no second chances.
	echo.
	echo.
	echo.
		pause
			 set USERNAME=claire
			eset USERNAME
			echo * You have set the username to '%USERNAME'.
		pause
goto :end


:good
:end
