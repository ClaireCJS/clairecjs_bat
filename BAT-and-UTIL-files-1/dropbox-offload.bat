@Echo OFF

:DESCRIPTION:  TO MOVE STUFF FROM DROPBOX TO OUR BACKUPS FOLDER, THEN REPLICATE TO ALL BACKUPS FOLDERS ON ALL MACHINES
:DEPENDENCIES: THIS SHOULD BE CALLED BY ASSIMILATE-NEW.BAT AS WELL, but only after it does its existing DROPBOX logic.


rem ENVIRONMENT VALIDATION:
        call check-that-we-are-running-on-the-master-machine
        call validate-environment-variable BACKUPS_DIRNAME DROPBOX DROPBOX_OVERFLOW_DIRNAME LOCAL_DROPBOX_OVERFLOW COLOR_DEBUG COLOR_IMPORTANT COLOR_NORMAL COLOR_SUBTLE LOCAL_BACKUPS_DRIVE LOCAL_BACKUPS_DIR LOCAL_DROPBOX_OVERFLOW
        call validate-in-path warning debug sync-a-folder-to-somewhere

rem PERFORM THE APPROPRIATE BACKUPS:
        gosub offloaddir "%DROPBOX%\BACKUPS\Samsung Galaxy S2"
        gosub offloaddir "%DROPBOX%\BACKUPS\Samsung Galaxy tablet"

rem SYNC THE DROPBOX_OVERFLOW BACKUP FOLDER TO ALL OTHER BACKUP REPOS:
            call important "Backing up the freshly-poplated dropbox overflow to all other backup repos"
            for %%letter in (%THE_ALPHABET%) gosub SyncDropboxOverflowBackupToDrive %letter%

goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::







    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :offloaddir [dir]
        :: narrate what's going on:
            call debug "offloading dropbox dir: %dir%"

        :: ensure passed directory exists:
            if not isdir %dir% (call warning "...Skipping becuase it does not exist: %dir%" %+ goto :returnOffloaddir)

        :: get the name ONLY of the directory:
            set TARGET_NAME_ONLY=%@NAME[%dir%]

        :: push passed directory into our overflow area:
            %COLOR_SUBTLE% 
                 echo.
                (echo yryryr|mv/ds %dir% "%@UNQUOTE[%dropbox_overflow%]\%target_name_only%")
            %COLOR_NORMAL%

        :returnOffloaddir
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :SyncDropboxOverflowBackupToDrive [drive]
        :: output for user
            call debug "Syncing backups to drive %drive%:..."

        :: validate that our goal is possible
            if   0 eq    "%@READY[%drive%]"            (%COLOR_WARNING% %+ echos NOT READY.               %+ echo. %+ goto return2)
            if not isdir "%drive%:\%BACKUPS_DIRNAME%"  (%COLOR_WARNING% %+ echos No %drive%:\BACKUPS\ dir %+ echo. %+ goto return2)

        :: backup that folder
            echo ...
            set  SYNCSOURCE=%LOCAL_DROPBOX_OVERFLOW%                         
            set  SYNCTARGET=%DRIVE%:\%BACKUPS_DIRNAME%\%DROPBOX_OVERFLOW_DIRNAME%
            set  SYNCTRIGER=__ last synced from master backup to backup on %DRIVE% __   
            call sync-a-folder-to-somewhere.bat            

        :return2
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END
