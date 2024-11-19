@Echo OFF
 on break cancel

rem For purely cosmetic reasons, we want each file to be a different color:
        if %1 eq "randcolor" (call randfg)

rem If an mp3+wav pair exists, delete the wav, because it is redundant:
        for %tmpfile in (*.wav) if exist "%@NAME[%tmpfile].mp3" .or. exist "%@NAME[%tmpfile].flac" del "%@NAME[%tmpfile%].wav"


