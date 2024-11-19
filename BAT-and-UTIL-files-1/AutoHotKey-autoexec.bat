@Echo OFF
 on break cancel

rem Kill old autohokey if it's running
        taskend /f autohotkey64* >nul

rem Need as-consistent-as-possible CapsLock/NumLock/ScrollLock/Insert keys, for our AutoHotKey that tracks them:
        rem we make sure insert is on because it syncs with the initial status in our insert-related code in autoexec.ahk:
                echos %SET_INSERT_ON%``
                rem (Keep in mind, insert is handled application-specific so it can never truly be consistent in this situation)

        rem we make sure caps lock/scroll lock/num lock is off because it syncs with the initial status in our insert-related code in autoexec.ahk:
                keybd /c0
                keybd /s0
                keybd /n0

rem Start our primary autohotkey script that contains everything we want permanently added to our environment
        call autohotkey.bat c:\bat\autoexec.ahk

