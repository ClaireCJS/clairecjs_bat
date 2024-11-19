@Echo OFF
 on break cancel

::::: purely cosmetic:
    if %1 eq "randcolor" (call randfg)

::::: do the thing:
    for %tmpfile in (*.mp3) if exist "%@NAME[%tmpfile].flac" (del "%@NAME[%tmpfile%].flac")


