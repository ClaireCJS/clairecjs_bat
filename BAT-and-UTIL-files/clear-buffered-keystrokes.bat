@echo off


rem A suggested way:
        set ppp=dummy <nul >nul
        
rem Another:        
        rem set DUMMY=DUMMY
        rem set /p DUMMY=dummy <con: >nul

        
rem Another suggeste way:
        choice /n /d y /t 0 >nul

rem What i did, but doesn't quite seem to work....
        rem @input /C /w0 %%This_Line_Clears_The_Character_Buffer
