@Echo OFF

::::: purely cosmetic:
    if %1 eq "randcolor" (call randfg)

::::: do the thing:
    for %tmpfile in (*.wav) if exist "%@NAME[%tmpfile].mp3" (del "%@NAME[%tmpfile%].wav")


