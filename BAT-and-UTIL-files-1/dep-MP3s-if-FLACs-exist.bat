@Echo OFF
 on break cancel
if %1 eq "randcolor" (call randfg)
for %tmpfile in (*.flac) if exist "%@NAME[%tmpfile].mp3" call deprecate "%@NAME[%tmpfile%].mp3"
