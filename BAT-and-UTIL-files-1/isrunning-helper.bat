@Echo OFF

::::: DEBUG:
	: This breaks it actually . . . . if "%DEBUG%"=="1" Echo ON
    if "%DEBUG%"=="1" (Echo Off)

::::: SET OUR TEMP:
	set TEMPTARGET1=%TEMP%\isrunning-%_PID%-1.txt
	set TEMPTARGET2=%TEMP%\isrunning-%_PID%-2.txt
	set TEMPTARGET3=%TEMP%\isrunning-%_PID%-3.txt
	set TEMPTARGET4=%TEMP%\isrunning-%_PID%-4.txt
	set TEMPTARGET5=%TEMP%\isrunning-%_PID%-5.txt

::::: DEBUG STUFF:
	:It actually breaks this to echo like this::echo  @taskList /L %=|grep -i %* %=| grep -i -v grep %=| grep -i -v keep-killing-if-running %=>:u8%TEMPTARGET%

::::: GREP THE TASK LIST INTO THE TEMP FILE:
	taskList /l /o                                       >:u8 %TEMPTARGET1%
    REM 2023/08/26 changed from %* to %1 because 'quiet' as %2 was breaking things:
	echo grep -i    "[0-9]  %1"         ``<%TEMPTARGET1% >:u8 %TEMPTARGET2%``
	grep -i    "[0-9]  %1"                <%TEMPTARGET1% >:u8 %TEMPTARGET2% 
	grep -i -v grep                       <%TEMPTARGET2% >:u8 %TEMPTARGET3% 
	grep -i -v keep-killing-if-running    <%TEMPTARGET3% >:u8 %TEMPTARGET4%
	grep -i -v react-after-program-closes <%TEMPTARGET4% >:u8 %TEMPTARGET5%

::::: OUTPUT THE TEMP FILE:
	type %TEMPTARGET5%
