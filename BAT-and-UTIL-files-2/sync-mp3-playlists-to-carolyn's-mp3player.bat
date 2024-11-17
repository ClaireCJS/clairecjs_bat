@echo off

:::: DEPRECATED! replaced by sync-mp3-playlists-to-location.bat (sync.bat NOT run in carolyn's mp3 player playlist folder)


::::: Check drive letter for mp3 is correct - code Carolyn claimed existed that never did:
echo Let's see if the drive letter for your mp3 player is right - currently set to %MP3PLAYERCAS
dir %MP3PLAYERCAS
pause
echo If it's wrong, you can change it now:
eset MP3PLAYERCAS


::::: Now that we know the drive letter, set up our locations:
set playlists=%mp3playercas:\playlist
set playlistsSource=%MP3OFFICIAL\lists
if not isdir %playlists call map-mp3-player.bat
if not isdir %playlists       (echo ERROR - playlists destination folder %playlists% does not exist %+ pause)
if not isdir %playlistsSource (echo ERROR - playlists source folder %playlistssource does not exist %+ pause)
%playlistsSource\
%playlists\

:step 1 - change / to \
:step 2 - change U:\mp3\ to \MUSIC\
copy %CONTACTS %mp3playercas:\
gosub TransformPlaylist best.m3u
gosub TransformPlaylist changer.m3u
gosub TransformPlaylist "changer to learn only.m3u"
gosub TransformPlaylist changerrecent.m3u
gosub TransformPlaylist "changerrecent without cheese.m3u"
gosub TransformPlaylist "changerrecent to learn only.m3u"
gosub TransformPlaylist "Carolyn_alone.m3u"
gosub TransformPlaylist concert.m3u
gosub TransformPlaylist "concert not learned by Carolyn.m3u"
gosub TransformPlaylist "concert not learned by Claire.m3u"
gosub TransformPlaylist "concert to learn only.m3u"
gosub TransformPlaylist concertnext.m3u
gosub TransformPlaylist "concertnext not learned by Carolyn.m3u"
gosub TransformPlaylist "concertnext not learned by Claire.m3u"
gosub TransformPlaylist "concertnext to learn all songs for both of us.m3u"
gosub TransformPlaylist "concertnext to learn only for Carolyn - for songs Claire already learned.m3u"
gosub TransformPlaylist "concertnext to learn only for Carolyn.m3u"
gosub TransformPlaylist "concertnext to learn only for Claire.m3u"
gosub TransformPlaylist "concertnext to learn only.m3u"
gosub TransformPlaylist Christmas.m3u
gosub TransformPlaylist preferred.m3u
gosub TransformPlaylist party.m3u
gosub TransformPlaylist "party without cheese.m3u"
gosub TransformPlaylist oh.m3u


echo Deleting trigger!
if exist %MP3OFFICIAL\LISTS\TRIGGER-CASMP3.TRG *del %MP3OFFICIAL\LISTS\TRIGGER-CASMP3.TRG

echo Deleting BAK files, so your player doesn't fill up with them....
echo This is a new feature; I'm alerting it to you with this pause so that you can see if it works or not.
echo If it works, ask me to take out this pause. Pause code 9D1.
pause
:FAIL: del /s %playlists\*.bak
:NEW:
:GOAT OH OH TEMPORARILY NOT DO THIS *del /s %playlists\..\music\*.bak

call validate-important-mp3-player-playlists.bat

goto :END

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TransformPlaylist [playlist]
echo Synching %playlist
echo sync-mp3-playlists-to-carolyn's-mp3player-helper.pl <%playlistsSource\%playlist >%playlists\%playlist
     sync-mp3-playlists-to-carolyn's-mp3player-helper.pl <%playlistsSource\%playlist >%playlists\%playlist
return
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END
echo.
echo.
echo.
Echo Remember: You can use "sync-filelist CRTL.m3u" to sync a particular playlist, like CRTL.m3u, to your player.
unset /q playlists
