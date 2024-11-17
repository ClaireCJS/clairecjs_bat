@echo off
set  validate_in_path_message="pendmoves needs to be installed to your path, or C:\UTIL -- it's part of the SysInternals"
call validate-in-path pendmoves.exe
set  validate_in_path_message=
call validate-in-path important
cls
echo.
call important Pending file moves
pendmoves.exe %*