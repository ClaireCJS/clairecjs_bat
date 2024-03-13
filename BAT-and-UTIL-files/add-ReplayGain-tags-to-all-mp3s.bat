@echo off 

if not exist *.mp3 (%COLOR_IMPORTANT_LESS% %+ echo 🚫 No mp3s exist here. %+ goto :END)

::::: metamp3.exe doesn't properly process *.mp3 if the mp3's base filename also ends in a dot / there are 2 dots before mp3 (example: W.T.F..mp3). So we have to use *.* not *.mp3
::::: but if we use *.*, it totally bludgeons and corrupts every non-mp3 file -- even rendering cover.jpg files into corrupt jpgs.   So we have to sequester.

set                                SEQ_DIR=ohhhh
md                                %SEQ_DIR%
call validate-environment-variable SEQ_DIR
cd                                %SEQ_DIR%


set MOVE_DECORATOR=%@ANSI_RGB_BG[28,0,0]%ITALICS%%STRIKETHROUGH%%FAINT%

%COLOR_UNIMPORTANT% %+ mv ..\*.mp3
call randfg         %+ metamp3 --replay-gain *.*
call errorlevel        "something went wrong with adding replaygain tags in %0"
%COLOR_UNIMPORTANT% %+ echos %FAINT_ON%

set MOVE_DECORATOR=%ANSI_COLOR_SUCCESS%%@ANSI_RGB_BG[0,28,0]%ITALICS%%STRIKETHROUGH%%FAINT%

mv * ..
cd   ..
rd  %SEQ_DIR%



:END
color bright red on black

