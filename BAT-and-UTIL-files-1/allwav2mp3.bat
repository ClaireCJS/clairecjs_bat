@Echo off
 on break cancel

rem Loop through all the WAV files in the current directory and encode them to mp3
rem (note that ffmpeg.bat is simply ffmpeg.exe)
        do f in *.wav
            call ffmpeg.bat -i "%f" -ab 320k -map_metadata 0 -id3v2_version 3 "%@name[%f].mp3"
        enddo

rem Ask the user   if they want to delete the original WAV files:
        call askyn "Do you want to delete the original wav files" N
        if %ANSWER == 1 .or. (%SWEEPING% == 1 .and. %AUTODELETE% == 1) (call del-WAVs-if-mp3s-exist.bat)


 