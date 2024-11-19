@Echo OFF
 on break cancel

:DESCRIPTION: Creates "all.m3u" playlist files in any folder tree that has audio in it or any of the subfolders
:DESCRIPTION: See also: create-these_m3u-playlists.bat, which creates a "these.m3u" playlist file in any single folder that has audio only in that single folder
:DESCRIPTION: if %EXITAFTER% is set to 1 {or EXITAFTER is passed as a parameter}, the shell will exit afterward

rem NOTE: We did some fancy-ANSI cosmetic stuff when experimenting, but it doesn't matter at all to the cosmetics. We're realy just calling mp3-index /s in any folder that has audio files in it.

sweep ( echos %ANSI_POSITION_SAVE%%@ANSI_MOVE[2,1]%ANSI_ERASE_CURRENT_LINE%%BIG_TOP%%EMOJI_BROOM%   %@ANSI_MOVE[3,1]%ANSI_ERASE_CURRENT_LINE%%BIG_BOT%%EMOJI_BROOM%   %ANSI_POSITION_RESTORE%%@RANDFG[] %+ if %@FILES[/s,%FILEMASK_AUDIO%] gt 0 (call mp3index /s >all.m3u) )

REM this might be faster!:
REM sweep ( if %@FILES[/s,these.m3u] gt 0 (call mp3index /s >all.m3u  ))


call exit-after %*
