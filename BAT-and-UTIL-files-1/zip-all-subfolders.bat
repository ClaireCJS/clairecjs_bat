@Echo Off
 on break cancel

call print-if-debug *** zip-all-subfolders.bat %*


for /a:d %1   in ([@#$&_+=a-z0-9%=(%=)']*) gosub ZipAllFoldersInADir "%1"


goto :END


    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :ZipAllFoldersInADir [dirdir]
        :: strip quotes:
            set dirdirWithoutQuotes=%@STRIP[%=",%dirdir%]
            call print-if-debug - ZipAllFoldersInADir %dirdir%     (withoutQuotes=%dirdirWithoutQuotes%)

        :: quit if it's a bullshit folder like "", ".", "..", or the one we're actually in (forget why):
            if "%dir%" != "" .or. "%dir%" != "." .or. "%dir%" != ".." goto :return

        :: change into folder:
            cd %dirdir%

            :: do something in that folder:
                call print-if-debug * current folder = %_CWP   %+ if "%DEBUG%" != "1" pause
                call zip-all-folders %*                        %+ if "%DEBUG%" != "1" pause

        :: change back from folder:
            cd ..
    :return
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
