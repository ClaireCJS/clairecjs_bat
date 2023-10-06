@echo off
set FILE=%1
call validate-environment-variable FILE
%COLOR_RUN%
call zip-old %FILE
echo.
echo.
%COLOR_SUCCESS%
dir /odt | tail -5