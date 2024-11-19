@on break cancel
@echo off
call validate-in-path exiflist.exe
exiflist.exe %*
