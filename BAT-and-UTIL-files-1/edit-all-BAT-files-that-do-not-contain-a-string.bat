@echo off
setlocal enabledelayedexpansion

set SEARCH_STRING=on break cancel


eset SEARCH_STRING

:: Check if %EDITOR% is set
if not defined EDITOR (
    echo Error: %EDITOR% environment variable is not set.
    exit /b 1
)

:: Loop through all .BAT files in the current directory
for %%F in (*.bat) do (
    :: Check if the file contains "on break cancel"
    findstr /i /c:"on break cancel" "%%F" >nul 2>&1
    if errorlevel 1 (
        echo Editing %%F...
        %EDITOR% "%%F"
    )
)

echo All applicable .BAT files have been edited.
