@Echo OFF
@on break cancel

rem PRE-CHECK:
        call checkeditor
        call validate-environment-variables BAT MACHINENAME EDITORBG

rem SETUP:
        %BAT%\


rem GET DRIVE LETTER:
         set        NEW_DRIVE_LETTER=?
        eset        NEW_DRIVE_LETTER
         set DRIVE=%NEW_DRIVE_LETTER%


rem EDIT BAT/ENVIRONMENT FILES THAT MAY NEED TO REFER TO NEW HARDRIVE:
        %EDITORBG% environm.btm checkmappings.bat fr.bat index-video-helper.bat gather-cartoons-and-live-shows.bat
        rem        ^^^^ map-drives.btm removed in 2024 because it was so heavily abstarcted as to not need changes by 2018 or so
        rem        ^^^^ generate-filelists-by-attribute-audio.ini generate-filelists-by-video.ini removed in 2024 because features in our script allowed us to add 'potential collections' for each drive instead of having to hardcode real ones

rem EDIT FTP SERVER FILES:
    cls
    gosub question "* Do we still do stuff with the ftpserver? Maybe. Let's see (press a key to see)."
    pushd .
        call ftphome
        cd ..
        if exist links.txt (
            call advice "Note that editing the following file doesn't fix the FTP server problem of updating group permissions to include that drive letters"
            %EDITORBG% links.txt
        )
    popd

rem LET THEM KNOW THESE FILES ARE WAITING FOR THEM IN THE TEXT EDITOR:
    window restore
    gosub question "* Scripts that need to be edited have been opened up in the text editor!"
    pause

rem STUFF WE CAN ONLY DO IF THE DRIVE IS ACTUALLY READY RIGHT NOW:
    if "%@READY[%DRIVE%]" eq "1" goto :Ready_YES
                                 goto :Ready_NO
        :Ready_NO
            call error "%DRIVE% IS NOT READY YET! YOU NEED TO COME BACK AND DO THIS AGAIN LATER."
        goto :READY_DONE
        :Ready_YES

            rem CREATE FILE STORING THE DATE THIS HARDDRIVE CAME UP:
                set TARGET=%DRIVE%:\__ I awaken! __ %+ if not exist "%TARGET%" (>"%TARGET%" %+ attrib +r "%TARGET%")
                
            rem MAKE RECYCLED AND OTHER FOLDERS THAT OUR SCRIPTS TEND TO USE:
                call important "Making \MEDIA, \BACKUPS, \recycled, \recycled"
                %COLOR_LOGGING%
                set TARGET1=%DRIVE%:\MEDIA    %+ if not isdir %TARGET1% md %TARGET1%
                set TARGET2=%DRIVE%:\BACKUPS  %+ if not isdir %TARGET2% md %TARGET2%
                set TARGET3=%DRIVE%:\recycled %+ if not isdir %TARGET3% md %TARGET3%
                set TARGET4=%DRIVE%:\recycler %+ if not isdir %TARGET4% junction %TARGET4% %TARGET3%

            rem LABEL THE DRIVE:
                %COLOR_NORMAL %+ echo. %+ echo. 
                call drives
                gosub question "* Label the drive now. Follow above pattern." 
                label %DRIVE%:

            rem SHARE THE DRIVE:
                cls
                %COLOR_PROMPT% %+ echos *** Here is the pattern of network share names: *** %+ %COLOR_NORMAL% %+ echo.
                call env.bat|:u8grep -i "mapping_[a-z]="|:u8call "highlight [A-Z0-9]+$"
                gosub question "* Share the drive now:" %+ pause
                call MyComputer

            rem CREATE FOLDER-THAT-MATCHES-OUR-LABEL TO REDUCE CONFUSION WHEN VIEWING NETWORK SHARES
                call important "Making "!!! {DRIVE LABEL} !!!" folders on every drive... "
                %COLOR_LOGGING%   %+ call make-directory-matching-drive-label-on-every-drive %*
                %COLOR_NORMAL%    %+ cls

            rem REMIND OF environm.btm EDITS:
                call important "Update the code near '%blink_on%SET MEDIA_Q%blink_off%' in '%italics_on%environm.btm%italics_off%'... "
                pause

            rem DOUBLE CHECK THIS CONFUSING SITUATION THAT HAPPENS WHEN WE SHIFT DRIVE LETTERS AROUND:
                cls
                gosub question "* Click into each network share and make sure it matches what you think it does."
                call advice "...sometimes changing around drive letters leaves shares associated incorrectly."
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

call celebration "New harddrive woo!"

