@Echo OFF
@on break cancel

::::: VALIDATE ENVIRONMENT
    call validate-in-path frpost settemp sync-filelist-helper.pl fix-window-title fatal_error 

::::: INCORRECT USAGES:
	if "%1"  ==  "" goto :Usage
	if not exist %1 goto :SourcePlaylistDoesNotExist
	if not isdir %2 goto :DestinationDirDoesNotExist

::::: GENERATE WINDOW TITLE:
	title * Syncing files listed in: "%1" to destination: "%2 "

::::: GENERATE TEMP-SCRIPT FILENAME:
	rem call settemp
	rem set TEMPBAT="%TEMP\sync-filelist-%_PID.bat"
        call set-temp-file sync_filelist_bat
        set TEMPBAT=%tmpfile%.bat

::::: CREATE AND RUN TEMP-SCRIPT:
	echo * sync-filelist-helper.pl %1 %2 
	echo * sync-filelist-helper.pl %1 %2     to %TEMPBAT
	REM    sync-filelist-helper.pl %1 %2 |& tee %TEMPBAT
	       sync-filelist-helper.pl %1 %2    >:u8%TEMPBAT
	call %TEMPBAT
	call fix-window-title
goto :END



		::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
		:SourcePlaylistDoesNotExist
			call fatal_error "Playlist/filelist of %1 does not exist! This must be an existing list of files"
		goto :END
		::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

		::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
		:DestinationDirDoesNotExist
			call fatal_error "Destination folder of %2 does not exist! This must be an existing folder."
		goto :END
		::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

		::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
		:Usage
            %COLOR_ERROR%
			echo ERROR! NO PARAMETERS GIVEN!
			echo .
			echo .
			echo USAGE: sync-filelist.bat PLAYLIST.m3u e:\music-location\ 
			echo .
			echo .     Above example will copy all mp3s from PLAYLIST.m3u into e:\music-location\
			echo .     Folders like c:\mp3\Metallica\ and such will be become  e:\music-location\Metallica\ , for example
			echo .
			echo This can also be used with non-playlists. Any list of files can be sync'ed with this. But you may need to add directory transformations to the code...
		goto :END
		::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





:END
	free|:u8frpost
	unset /q TEMPBAT
	if "%EXITAFTER"=="1" exit

