@echo off
@on break cancel

::::: DEBUG:
    SET DEBUG_SORT=0

::::: CYGWIN BRANCHING:
    if "%CYGWIN%" == "0" goto :nocygwin
    if "%CYGWIN%" ne ""  goto   :cygwin
                         goto :nocygwin

::::: DO IT:
	:nocygwin
		%Windir%\System32\sort.exe %*
	goto :END

	:cygwin
        call validate-environment-variable OPTIMAL_CPU_THREADS
		c:\cygwin\bin\sort.exe -f --parallel=%OPTIMAL_CPU_THREADS% %*
        :NOTE: cygsort --k=1.21 is equivalent to winsort /+22 
	goto :END



:END
