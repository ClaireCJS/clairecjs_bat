@Echo OFF
 on break cancel

:DESCRIPTION: Creates a "these.m3u" playlist file in any single folder that has audio in it
:DESCRIPTION: See also: create-all_m3u-playlists.bat, which create "all.m3u" playlist files for whole folder trees
:DESCRIPTION: if %EXITAFTER% is set to 1 {or EXITAFTER is passed as a parameter}, the shell will exit afterward

rem until 2025: sweep ( echos %@RANDFG[]%EMOJI_BROOM% %+ if exist %FILEMASK_AUDIO% (call    mp3index        >these.m3u ))
                sweep ( echos %@RANDFG[]%EMOJI_BROOM% %+ if exist %FILEMASK_AUDIO% (dir /b %FILEMASK_AUDIO% >these.m3u ))
rem after 2025: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

call exit-after %*


