@if "%1" == "quick" goto :quick
@echo off
 on break cancel


rem A suggested way:
        rem set ppp=dummy <nul >nul
        
rem Another:        
        rem set DUMMY=DUMMY
        rem set /p DUMMY=dummy <con: >nul

        
rem Another suggested way:
        rem choice /n /d y /t 0 >nul

rem What i did, but doesn't quite seem to work....
        :quick
        @inkey /C /w0 %%This_Line_Clears_The_Character_Buffer

