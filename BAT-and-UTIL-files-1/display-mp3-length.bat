@on break cancel
@Echo OFF

call validate-in-path               validate-environment-variable validate-file-extension display-mp3-tags grep sed

set                                         OUR_MP3=%1
call validate-environment-variable          OUR_MP3
call validate-file-extension               %OUR_MP3% *.mp3
set               PRETTY_OUR_MP3=%@UNQUOTE[%OUR_MP3%] 
set OUTPUT=%@EXECSTR[call display-mp3-tags %OUR_MP3% |:u8 grep -i length |:u8 sed -e "s/ 00:/ /" -e "s/ 0/  /" -e "s/ *:/:/" -e "s/^ *//ig" -e "s/:/:%ANSI_COLOR_IMPORTANT%%ITALICS_ON%/" ]


echo %STAR% %ANSI_COLOR_BRIGHT_GREEN%%OUTPUT% %ITALICS_OFF%%ANSI_COLOR_BRIGHT_YELLOW%%DASH% %ANSI_COLOR_YELLOW%for mp3: %ANSI_COLOR_BRIGHT_YELLOW%%@REPLACE[.mp3,%ANSI_COLOR_YELLOW%.mp3,%PRETTY_OUR_MP3%]
