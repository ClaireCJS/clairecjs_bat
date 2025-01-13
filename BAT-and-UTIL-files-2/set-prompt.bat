@rem ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ This is a speedup function to use a generated prompt rather than regenerating it.
@Echo OFF
@on break cancel

rem If we're running this outside of TCC, just do a generic prompt:
        if "%comspec%" == "C:\Windows\system32\cmd.exe " goto :NoAnsiPrompt

rem Debug stuff:
        if "%DEBUG_DEPTH%" == "1" (echo * setprompt.bat (batch=%_BATCH))



rem Machine-specific exceptions can go here:
        rem if "%1" == "BROADWAY" .or. "%@UPPER[%MACHINENAME%]" == "BROADWAY" (goto :NoAnsiPrompt)
        if "%@UPPER[%MACHINENAME%]" == "WORK"                              (goto :work)



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



rem Create a simpler .CMD version of the generated prompt, which can be used in CMD.EXE and other shells,
rem but which unfortunately has any realtime-generated values like CPU usage or time of day statically frozen:
        set SETPROMPT_CMD=c:\bat\setprompt.cmd
        set THIS_SCRIPT=c:\bat\%0.bat
        if not exist %SETPROMPT_CMD% (
                echo %@CHAR[55356]%@CHAR[57119] Creating setprompt.cmd cause it doesn't exist
                echo prompt %prompt%>%SETPROMPT_CMD%
        ) else (
                set age_diff=%@EVAL[%@FILEAGE[%THIS_SCRIPT%] - %@FILEAGE[%SETPROMPT_CMD%]]
                if %@FILEAGE[%THIS_SCRIPT%] gt %@FILEAGE[%SETPROMPT_CMD%]  (
                        echo %@CHAR[55356]%@CHAR[57119] Creating setprompt.cmd cause setprompt.bat is newer than setprompt.cmd [age_diff=%age_diff%]
                        echo @prompt %prompt%>%SETPROMPT_CMD%
                )
        )
        

