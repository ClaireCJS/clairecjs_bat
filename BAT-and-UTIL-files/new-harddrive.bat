@Echo OFF

::::: PRE-CHECK:
    call checkeditor
    call validate-environment-variables BAT MACHINENAME

::::: SETUP:
    %BAT%\


::::: GET DRIVE LETTER:
     set        NEW_DRIVE_LETTER=?
    eset        NEW_DRIVE_LETTER
     set DRIVE=%NEW_DRIVE_LETTER%


::::: EDIT BAT/ENVIRONMENT FILES:
    %EDITORBG% environm.btm map-drives.btm checkmappings.bat fr.bat index-video-helper.bat generate-filelists-by-attribute-video.ini generate-filelists-by-video.ini gather-cartoons-and-live-shows.bat

::::: EDIT FTP SERVER FILES:
    cls
    gosub question "* Do we still do stuff with the ftpserver? Maybe. Let's see (press a key to see)."
    pushd .
    call ftphome
    cd ..
    if not exist links.txt goto :NoEditLinks
        %COLOR_ADVICE%
        echo * Note that editing the following file doesn't fix the problem of: UPDATING GROUP PERMISSIONS TO INCLUDE THAT DRIVE LETTERS
        %COLOR_NORMAL%
        %EDITORBG% links.txt
    :NoEditLinks
    popd

::::: LET THEM KNOW THESE FILES ARE WAITING FOR THEM IN THE TEXT EDITOR:
    window restore
    gosub question "* Scripts that need to be edited have been opened up in the text editor!"
    pause

::::: STUFF WE CAN ONLY DO IF THE DRIVE IS ACTUALLY READY RIGHT NOW:
    if "%@READY[%DRIVE%]" eq "1" goto :Ready_YES
                                 goto :Ready_NO
        :Ready_NO
            %COLOR_ALARM%
            echo * ERROR! %DRIVE% IS NOT READY YET! YOU NEED TO COME BACK AND DO THIS AGAIN LATER.
            pause %+ pause %+ pause %+ pause %+ pause
        goto :READY_DONE
        :Ready_YES

            ::::: CREATE FILE STORING THE DATE THIS HARDDRIVE CAME UP:
                set TARGET=%DRIVE%:\__ I awaken! __ %+ if not exist "%TARGET%" (>"%TARGET%" %+ attrib +r "%TARGET%")
                
            ::::: MAKE RECYCLED AND OTHER FOLDERS THAT OUR SCRIPTS TEND TO USE:
                %COLOR_IMPORTANT% %+ echo * Making \MEDIA, \BACKUPS, \recycled, \recycled %+ %COLOR_LOGGING%
                set TARGET1=%DRIVE%:\MEDIA    %+ if not isdir %TARGET1% md %TARGET1%
                set TARGET2=%DRIVE%:\BACKUPS  %+ if not isdir %TARGET2% md %TARGET2%
                set TARGET3=%DRIVE%:\recycled %+ if not isdir %TARGET3% md %TARGET3%
                set TARGET4=%DRIVE%:\recycler %+ if not isdir %TARGET4% junction %TARGET4% %TARGET3%

            ::::: LABEL THE DRIVE:
                %COLOR_NORMAL %+ echo. %+ echo. 
                call drives
                gosub question "* Label the drive now. Follow above pattern." 
                label %DRIVE%:

            ::::: SHARE THE DRIVE:
                cls
                %COLOR_PROMPT% %+ echos *** Here is the pattern of network share names: *** %+ %COLOR_NORMAL% %+ echo.
                call env|grep -i "mapping_[a-z]="|call "highlight [A-Z0-9]+$"
                gosub question "* Share the drive now:" %+ pause
                call MyComputer

            ::::: CREATE FOLDER-THAT-MATCHES-OUR-LABEL TO REDUCE CONFUSION WHEN VIEWING NETWORK SHARES
                %COLOR_IMPORTANT% %+ echo * Making "!!! {DRIVE LABEL} !!!" folders on every drive... ``
                %COLOR_LOGGING%   %+ call make-directory-matching-drive-label-on-every-drive %*
                %COLOR_NORMAL%    %+ cls

            ::::: DOUBLE CHECK THIS CONFUSING SITUATION THAT HAPPENS WHEN WE SHIFT DRIVE LETTERS AROUND:
                gosub question "* Click into each network share and make sure it matches what you think it does."
                %COLOR_ADVICE%
                echo   ...sometimes changing around drive letters leaves shares associated incorrectly.
                %COLOR_NORMAL%
                pause
                start \\%MACHINENAME%
                echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ 
                    pause
        :Ready_DONE


goto :END
        ::::::::::::::::::::::::::::::
        :question [question]
            echo. %+ echo.
            %COLOR_PROMPT% %+ echo %question%
            %COLOR_NORMAL%
        return
        ::::::::::::::::::::::::::::::
:END