@loadbtm on
@Echo OFF
 on break cancel

rem Some trickery in case we call create-srt ai thinking it was create-srt-for-currently-playing-song but really it's create-srt-from-file
rem "%1" eq "ai" .or. "%1" eq "force" then
if "%1" == "current"       create-srt-file-for-currently-playing-song.bat
if "%1" != "current" @call create-srt-from-file.bat %*

