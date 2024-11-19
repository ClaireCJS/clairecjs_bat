@Echo OFF
 on break cancel

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

rem FORK BEHAVIOR BASED ON WHAT FOLDER WE ARE IN:
    ::::: Future note: If we run into future situations where we want a whole tree to behave a certain way, we will have to use regex
	if "%_CWP"=="\GAMES-REPOSITORY\RHYTHM & MUSIC\Rocksmith"       gosub :rocksmithdlc
	if "%_CWP"==                                      "\DLC"       gosub :rocksmithdlc
	if "%_CWP"=="\MEDIA\DELETE-AFTER-WATCHING"                     gosub :videoWatchingRepo
	if "%_CWP"==      "\DELETE-AFTER-WATCHING"                     gosub :videoWatchingRepo
	if "%_CWP"=="\MEDIA\DELETE-AFTER-WATCHING\HANGOUT"             gosub :videoWatchingRepo
	if "%_CWP"==      "\DELETE-AFTER-WATCHING\HANGOUT"             gosub :videoWatchingRepo
	if "%_CWP"==                            "\HANGOUT"             gosub :videoWatchingRepo
	if "%_CWP"=="\MEDIA\FOR-REVIEW\DO_LATERRRRRRRRRRRRRRRRRRRRRRR" gosub :incomingVideo
	if "%_CWP"=="\MEDIA\FOR-REVIEW"                                gosub :incomingVideo
	if "%_CWP"==      "\FOR-REVIEW"                                gosub :incomingVideo
	if "%_CWP"==      "\FOR-REVIEW\DO_LATERRRRRRRRRRRRRRRRRRRRRRR" gosub :incomingVideo
	if "%_CWP"==                 "\DO_LATERRRRRRRRRRRRRRRRRRRRRRR" gosub :incomingVideo
	if "%_CWP"==                 "\DBCU"                           gosub :dbcu
	if "%_CWP"==                 "\dropbox\Camera Uploads"         gosub :dbcu

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:DEFAULT
    %color_run%
    echo.
    echo * clean.bat: default clean
    %color_normal%
	gosub delIfExists *.stackdump
	gosub delIfExists thumbs.db

    if exist *.dep                     goto :CleanupImages_Yes
    if exist attrib.lst if exist *.jpg goto :CleanupImages_Yes
                                       goto :CleanupImages_No
        :CleanupImages_Yes  
            if not isdir dep mkdir dep
            if isdir deprecated mv/ds deprecated dep
            if exist *.dep mv *.dep dep
            if exist *.deprecated mv *.deprecated dep
        :CleanupImages_No   
goto :END

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:videoWatchingRepo
	gosub sayRole "VIDEO_WATCHING_REPO (%DELETEAFTERWATCHING%)"
    gosub delIfExists *.nfo
return

:rocksmithdlc
    call debug "is rocksmith!"
    call clean-rocksmith-dlc-dir %*
return

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:incomingVideo
	gosub sayRole "INCOMING_VIDEO"
    if exist *.cb[zr] if not isdir %NEWCL\comics md %NEWCL\comics
    if exist *.cb[zr] mv *.cb[zr]  %NEWCL\comics 
    if exist *.apk mv *.apk        %NEWCL
     gosub delIfExists "Torrent downloaded from*"
     gosub delIfExists "Torrent-downloaded-from*"
     gosub delIfExists *.bak
     gosub delIfExists ~utorrent*.dat
     gosub delIfExists del www.*
     gosub delIfExists catalog.txt
     gosub delIfExists NZBROYALTY.com.txt
     gosub delIfExists the.cleveland.show.*dimension.txt
     gosub delIfExists bobs.burgers*dimension.txt
     gosub delIfExists american.dad*dimension.txt
     gosub delIfExists RARBG.com.txt
     gosub delIfExists "Downlaoded From*"
     gosub delIfExists "Downloaded From*"
     gosub delIfExists *.sfv
     gosub delIfExists Torrent_downloaded_from_*
     gosub delIfExists Black-Sam.txt
     gosub delIfExists 4KiDS.txt
     gosub delIfExists www.Torrenting.com.txt
     gosub delIfExists www.TorrentDay.com.txt
     gosub delIfExists sample.*
    :gosub delIfExists 
    :gosub delIfExists 
    :gosub delIfExists 
    if exist *.nfo ren *.nfo *.txt
return

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



    ::::::::::::::::::::::::::::::::::::::::
    :dbcu
        call clean-dbcu %*
    return
    ::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	:::::::::::::::::::::::::::::::::::::::::::
	:delIfExists [filename]
		if exist %filename (*del /z %filename)
	return
	:::::::::::::::::::::::::::::::::::::::::::

    :::::::::::::::::::::::::::::::::::::::::::::::::::
    :sayRole [role]
    	echo.
        color bright blue on black
        echo * Cleaning using clean-role of: %role%
        color white on black
        echo.
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::






:END
