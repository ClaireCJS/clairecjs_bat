@Echo ON
@on break cancel


rem Script for command-line running a slideshow. Used around 2010 and ran some tests in 2020 but not really used in 2024. Here more as an example.


rem CONFIGURATION:
        set SLIDESHOW_COMMAND=set-background-picture-for-johnsbackgroundswitcher


rem VALIDATIONS:
        SET param1=%1
        call validate-env-var SLIDESHOW_COMMAND param1 FILEMASK_IMAGE
        call validate-in-path SLIDESHOW_COMMAND 


rem COMMAND-LINE BEHAVIOR:
        if "%1"=="bg" .or. "%1"=="background" (goto :Background)

rem DEFAULT BEHAVIOR:
        rem goto :FastPicViewer —— this thing is no longer registered
            goto :Background


goto :END

                :PicViewer
                        call validate-in-path irfanview
                        if not exist filelist.txt call makefilelist
                        echo call irfanview.bat /fs /slideshow%==filelist.txt
                             call irfanview.bat /fs /slideshow%==filelist.txt
                goto :END

                :FastPicViewer
                        call validate-in-path FastPictureViewer.exe
                        set DIR=%_CWD\
                        pushd .
                            :-n prevent taking focus
                            :-LOCK 2048 stop changing auto advance mode
                            :-m2 = second monitor
                            :-[ar]:3000 advance/random 3000 ms
                            "C:\Program Files\FastPictureViewer\"
                            echo  FastPictureViewer.exe -c "%DIR%" -k -m:2 -a:3000 
                            start FastPictureViewer.exe -c "%DIR%" -k -m:2 -a:3000 
                            call sleep 2
                            LaunchKey "+a"
                        popd
                goto :END

                :Background
                        :or %1 in (*.jpg;*.bmp;*.png;*.gif) do call %SLIDESHOW_COMMAND% "%1"
                        for %1 in (%FILEMASK_IMAGE%)        do call %SLIDESHOW_COMMAND% "%1"
                goto :END

:END