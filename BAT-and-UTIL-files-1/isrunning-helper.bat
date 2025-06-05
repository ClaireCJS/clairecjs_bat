@loadbtm on
@on break cancel
@Echo OFF

rem DEBUG:
        rem  This breaks it actually . . . . if "%DEBUG%"=="1" Echo ON
        if "%DEBUG%"=="1" (Echo Off)

rem SET OUR TEMP:
        set rn=%_datetime                                
	set TEMPTARGET1=%TEMP%\isrunning-%_PID%-%rn%-1.txt
	set TEMPTARGET2=%TEMP%\isrunning-%_PID%-%rn%-2.txt
	set TEMPTARGET3=%TEMP%\isrunning-%_PID%-%rn%-3.txt
	set TEMPTARGET4=%TEMP%\isrunning-%_PID%-%rn%-4.txt
	set TEMPTARGET5=%TEMP%\isrunning-%_PID%-%rn%-5.txt

rem DEBUG STUFF:
	rem It actually breaks this to echo like this::echo  @taskList /L %=|grep -i %* %=| grep -i -v grep %=| grep -i -v keep-killing-if-running %=>:u8%TEMPTARGET%

rem GREP THE TASK LIST INTO THE TEMP FILE:
	taskList /l /o                                        >:u8   %TEMPTARGET1%
rem 	grep -i    "[0-9]  %1"             `<`%%TEMPTARGET1%%`>`:u8 %%TEMPTARGET2%% %+ REM 2023/08/26 changed from %* to %1 because 'quiet' as %2 was breaking things
rem	grep -i    "[0-9]  %1"                <%TEMPTARGET1%  >:u8   %TEMPTARGET2%  %+ REM 2023/08/26 changed from %* to %1 because 'quiet' as %2 was breaking things
	grep -i    "[0-9]  .*%1"              <%TEMPTARGET1%  >:u8   %TEMPTARGET2%  %+ REM 2025/06/05 changed \d  %1 to \d  .*%1 which would create complications but is necessary for the new way we launch python scripts
	grep -i -v grep                       <%TEMPTARGET2%  >:u8   %TEMPTARGET3% 
	grep -i -v keep-killing-if-running    <%TEMPTARGET3%  >:u8   %TEMPTARGET4%
	grep -i -v react-after-program-closes <%TEMPTARGET4%  >:u8   %TEMPTARGET5%

rem OUTPUT THE TEMP FILE:
	type %TEMPTARGET5%
