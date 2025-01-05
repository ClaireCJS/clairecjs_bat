@Echo OFF
@on break cancel

rem DEBUG:
    SET DEBUG_SORT=0

rem CYGWIN BRANCHING:
    if "%CYGWIN%" == "0" goto :nocygwin
    if "%CYGWIN%" ne ""  goto   :cygwin
                         goto :nocygwin

rem DO IT:

	:nocygwin
		%Windir%\System32\sort.exe %*
	goto :END


	:cygwin
                iff not defined OPTIMAL_CPU_THREADS then
                        call warning "OPTIMAL_CPU_THREADS should have already been defined in environm.btm ... setting to 12"
                        set OPTIMAL_CPU_THREADS=12
                endiff
		c:\cygwin\bin\sort.exe -f --parallel=%OPTIMAL_CPU_THREADS% %*
                rem :NOTE: cygsort --k=1.21 is equivalent to winsort /+22 
	goto :END



:END
