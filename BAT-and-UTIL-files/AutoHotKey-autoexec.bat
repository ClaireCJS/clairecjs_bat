@Echo OFF

rem Kill old autohokey if it's running
        taskend /f autohotkey64* >nul

rem we make sure insert is on because it syncs with the initial status in our insert-related code in autoexec.ahk:
        echos %SET_INSERT_ON%``

rem Start our primary autohotkey script that contains everything we want permanently added to our environment
        call autohotkey.bat c:\bat\autoexec.ahk

