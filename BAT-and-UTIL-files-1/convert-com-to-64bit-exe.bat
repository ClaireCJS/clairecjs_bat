@echo off
 on break cancel
set oldname=%1
set newname=%@NAME[%oldname]64.exe
msdos -d -e -c%newname% %OLDNAME%