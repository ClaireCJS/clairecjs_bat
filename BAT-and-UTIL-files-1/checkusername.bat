@Echo off

:Restart
if "%USERNAME"=="" goto :bad
                   goto :good


:bad
	echo.
	echo.
	echo ERROR!!!!!!!!!!!!!!
	echo.
	echo     You do not have %%USERNAME defined!
	echo     This would normally be 'Claire' or 'Carolyn'
	echo     This is required; please set this now.
	echo.
	echo.
	echo.
		pause
			 set USERNAME=claire
			eset USERNAME
			echo * You have set the username to '%USERNAME'.
		pause
        goto :Restart
goto :end


:good
:end
