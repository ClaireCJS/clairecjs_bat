@echo off
@on break cancel

set playlistsGoto=%1
"%1"\


:DEBUG:
%COLOR_DEBUG %+ echo DEBUG: I am in %_CWP and about to validate playlists!






                          (%COLOR_WARNING% %+ call validate-filelist "changerrecent to learn only.m3u" |:u8 cut-to-width)
                          (%COLOR_WARNING% %+ call validate-filelist "concert.m3u"                     |:u8 cut-to-width)
if "%USERNAME"=="carolyn" (%COLOR_WARNING% %+ call validate-filelist "Carolyn_alone.m3u"               |:u8 cut-to-width)
if "%USERNAME"=="claire"  (%COLOR_WARNING% %+ call validate-filelist "Claire_alone.m3u"                |:u8 cut-to-width)


%COLOR_NORMAL%
