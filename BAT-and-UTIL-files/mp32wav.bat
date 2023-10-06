if "%2"=="" goto :Sorry


set TMP=%@UNIQUE[C:\]



    :using -ign is kind of iffy.
    :By ignoring the errors, you preserve content, which is most important.
    :But to do this, we must sacrifice quality control.

    c:\util\l3dec %@SFN["%1"] %TMP -wav -sa -ign %3 %4 %5 %6 %7 %8 %9
    mv %TMP %2
goto :End



:Sorry
    echo FATAL ERROR:
    echo              USAGE:  mp32wav.bat whatever.mp3 whatever.wav
:End
