@on break cancel
@echo off

for %tmpFile in (*.mp3) do gosub processfile "%tmpFile"

goto :END

    :processFile [file]
		%COLOR_IMPORTANT% %+ echo. %+ echo *** %file ***
		%COLOR_RUN%       %+ metamp3 --info %file%|:u8grep -i -a REPLAYGAIN
    :return


:END