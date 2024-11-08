@echo off


%COLOR_WARNING%
Echo *** DEPRECATED: Replaced by validate-important-playlists.bat ***
%COLOR_NROMAL%


call validate-environment-variable MP3PLAYERCAS

%MP3PLAYERCAS%:\PLAYLIST\
call validate-filelist "changerrecent to learn only.m3u" |:u8 cut-to-width
call validate-filelist "concert.m3u"                     |:u8 cut-to-width
call validate-filelist "Carolyn_alone.m3u"               |:u8 cut-to-width
