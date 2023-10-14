@echo off

:: Loop through all the wav files in the current directory
    do f in *.wav
        call ffmpeg.bat -i "%f" -ab 320k -map_metadata 0 -id3v2_version 3 "%@name[%f].mp3"
    enddo

:: Ask the user if they want to delete the original flac files
    call askyn "Do you want to delete the original wav files" N
    if %ANSWER == 1 .or. (%SWEEPING% == 1 .and. %AUTODELETE% == 1) (call del-WAVs-if-mp3s-exist.bat)


 