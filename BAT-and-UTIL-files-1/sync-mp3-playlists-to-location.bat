@echo off

:::: USAGE: sync-mp3-playlists-to-location.bat [ORIGINAL_PLAYLIST_FOLDER] [NEW_PLAYLIST_FOLDER] [NEW_MUSIC_FOLDER] [LOCAL_TRIGGER_FILE]
:::: USAGE: sync-mp3-playlists-to-location.bat C:\MP3\LISTS                J:\MUSIC\PLAYLIST     J:\MUSIC           %MP3OFFICIAL\LISTS\TRIGGER-CASMP3.TRG


::::: LEGACY STUFF FROM sync-mp3-playlists-to-carolyn's-mp3player.bat, where this originated:
::::: ::::: ::::: Check drive letter for mp3 is correct - code Carolyn claimed existed that never did:
::::: ::::: echo Let's see if the drive letter for your mp3 player is right - currently set to %MP3PLAYERCAS
::::: ::::: dir %MP3PLAYERCAS
::::: ::::: pause
::::: ::::: echo If it's wrong, you can change it now:
::::: ::::: eset MP3PLAYERCAS


::::: Now that we know the drive letter, set up our locations:
	set playlistsSource=%1
	set       playlists=%2
	set    musicBasedir=%3
	set         trigger=%4

    call validate-environment-variables PLAYLISTSSOURCE PLAYLISTS MUSICBASEDIR 

::::: Check that things exist:
:LEGACY: if not isdir %playlists call map-mp3-player.bat
	:201503 addition: just generate the playlists folder automatically; less harm in an extra existing than in sync's being harder to set up:
	if not isdir %playlists md %playlists%

	gosub CheckThatFoldersExist
	%playlistsSource\
	%playlists\

:step 1 - change / to \
:step 2 - change U:\mp3\ to \MUSIC\

:Also back up contacts file:
	:nah, let's not put personal information all over a bunch of random sdcards . . . . .copy %CONTACTS %musicBasedir

:Hard-coded lists to sync:
	gosub CheckThatFoldersExist
	gosub TransformPlaylist  best.m3u                                                                      %musicBaseDir%
	gosub TransformPlaylist  changer.m3u                                                                   %musicBaseDir%
	gosub TransformPlaylist "changer to learn only.m3u"                                                    %musicBaseDir%
	gosub TransformPlaylist "changer with non-music.m3u"                                                   %musicBaseDir%
	gosub TransformPlaylist  changerrecent.m3u                                                             %musicBaseDir% 
	gosub TransformPlaylist "changerrecent without cheese.m3u"                                             %musicBaseDir%
	gosub TransformPlaylist "changerrecent to learn only.m3u"                                              %musicBaseDir%
	gosub TransformPlaylist "CRTL.m3u"                                                                     %musicBaseDir%
	gosub TransformPlaylist "Carolyn_alone.m3u"                                                            %musicBaseDir%
	gosub TransformPlaylist "Claire_alone.m3u"                                                             %musicBaseDir%
	gosub TransformPlaylist  concert.m3u                                                                   %musicBaseDir%
	gosub TransformPlaylist "concert not learned by Carolyn.m3u"                                           %musicBaseDir%
	gosub TransformPlaylist "concert not learned by Claire.m3u"                                            %musicBaseDir%
	gosub TransformPlaylist "concert to learn only.m3u"                                                    %musicBaseDir%
	gosub TransformPlaylist  concertnext.m3u                                                               %musicBaseDir%
	gosub TransformPlaylist "concertnext not learned by Carolyn.m3u"                                       %musicBaseDir%
	gosub TransformPlaylist "concertnext not learned by Claire.m3u"                                        %musicBaseDir%
	gosub TransformPlaylist "concertnext to learn all songs for both of us.m3u"                            %musicBaseDir%
	gosub TransformPlaylist "concertnext to learn only for Carolyn - for songs Claire already learned.m3u" %musicBaseDir%
	gosub TransformPlaylist "concertnext to learn only for Carolyn.m3u"                                    %musicBaseDir%
	gosub TransformPlaylist "concertnext to learn only for Claire.m3u"                                     %musicBaseDir%
	gosub TransformPlaylist "concertnext to learn only.m3u"                                                %musicBaseDir%
	gosub TransformPlaylist  Christmas.m3u                                                                 %musicBaseDir%
	gosub TransformPlaylist  preferred.m3u                                                                 %musicBaseDir%
	gosub TransformPlaylist  party.m3u                                                                     %musicBaseDir%
	gosub TransformPlaylist "party without cheese.m3u"                                                     %musicBaseDir%
	gosub TransformPlaylist  oh.m3u                                                                        %musicBaseDir%
 

echo Deleting trigger!
	:if exist %MP3OFFICIAL\LISTS\TRIGGER-CASMP3.TRG *del %MP3OFFICIAL\LISTS\TRIGGER-CASMP3.TRG
	 if exist %trigger *del %trigger

echo Deleting BAK files, so your player doesn't fill up with them....
	gosub CheckThatFoldersExist
	:echo This is a new feature; I'm alerting it to you with this pause so that you can see if it works or not.
	:echo If it works, ask me to take out this pause. Pause code 9D1.
	:pause
		:FAIL:  del /s %playlists\*.bak
		:20xx: *del /s %playlists\..\music\*.bak
		:2011: triple-sync way: *del /s %musicBasedir\*.bak
		:2015: faster-sync way:
        pushd .
            %musicBaseDir%\
            global /q if exist *.bak *(*del *.bak)
        popd


if "%NOVALIDATE%" eq "1" goto :Validate_NO
	:Validate_YES
		gosub CheckThatFoldersExist
		call validate-important-playlists.bat %playlists
	:Validate_NO

goto :END

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:TransformPlaylist [playlist basedir]
		echo * Synching %playlist
		sync-mp3-playlists-to-location-helper.pl %mp3official %basedir <%playlistsSource\%playlist >%playlists\%playlist
	return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:CheckThatFoldersExist
		if not isdir %playlists       (echo ERROR - playlists destination folder %playlists% does not exist %+ pause)
		if not isdir %playlistsSource (echo ERROR - playlists source folder %playlistssource does not exist %+ pause)
	return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END
	echo.
	echo.
	echo.
		Echo Remember: You can use "sync-filelist CRTL.m3u" to sync a particular playlist, like CRTL.m3u, to your player.

	:Clean_Up		
		unset /q playlists
		unset /q playlistssource
		unset /q trigger

