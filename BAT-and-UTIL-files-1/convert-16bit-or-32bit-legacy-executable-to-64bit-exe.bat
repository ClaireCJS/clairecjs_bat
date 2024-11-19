@Echo OFF
 on break cancel

call validate-in-path msdos-player.exe

set OLD_NAME=%1
set NEW_NAME=%@NAME[%OLD_NAME]-64.exe

msdos-player.exe -d -e -c%NEW_NAME% %OLD_NAME%

