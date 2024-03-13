@Echo OFF
call display-mp3-tags %* | gr bitrate
