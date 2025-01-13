@echo off
 on break cancel

call print-if-debug *** zip-all-folders.bat %*



::::: Are we doing all folders, all EXEs, or what?
    set FOR_OPTS=/a:d
    set WILDCARD=*
    if "%1" != "" (set MODE=%1)
    if "%MODE%" != "ZIP-all-EXEs" (unset /q FOR_OPTS %+ set WILDCARD=*.exe)

::for /a:d       %dir   in ([@#$&_+=a-z0-9%=(%=)']*) gosub zipSingleFolder "%dir%"
  for %FOR_OPTS% %thing in              (%WILDCARD%) gosub zipSingleFolder "%thing%"


goto :END


    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :zipSingleFolder [dirwithquotes]
        :: strip quotes:
            set dir=%@STRIP[%=",%dirwithquotes] 
            call print-if-debug * zipSingleFolder %dir% %+ color white on black

        :: quit if it's a bullshit folder like "", ".", "..":
            if "%dir%" != "" .or. "%dir%" != "." .or. "%dir%" != ".." goto :return




            :: do something to that folder:
                call print-if-debug * call zip "%dir%" 
                @echo ry    |     call zip-folder "%dir%"



    :return
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
