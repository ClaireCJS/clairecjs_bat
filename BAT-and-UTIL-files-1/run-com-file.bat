@echo off
call validate-in-path msdos-player.exe
set FILE=%1
msdos-player.exe -e %FILE%