@Echo OFF
 on break cancel


call validate-in-path magick.exe    "You need ImageMagick's %italics_n%magic.exe%italics_off%, which can be done with the command: %italics_on%winget install ImageMagick.ImageMagick%italics_off%"
call validate-in-path deprecate.bat "You need deprecate.bat to rename the BMPs to .dep afterward, so they don't get picked up by slideshow programs, google smart frames, etc, without actually losing the bmp file"

rem echo %ansi_color_debug%- DEBUG: COMMAND IS: for `%%`tmpfile in (*.bmp) convert.exe -quality 100 -verbose '`%`tmpfile' '%@NAME[`%%`tmpfile].jpg'%ansi_color_normal%


for   %%tmpfile in (*.bmp) magick.exe -quality 100 -verbose   "%tmpfile" "%@NAME[%tmpfile].jpg"


call pause-for-x-seconds 20 "Press any key to deprecate the BMP files...This will keep them, but rename them so they don't get picked up by slideshow viewers, google smart frames, etc etc"

%COLOR_REMOVAL%

call deprecate.bat *.bmp

%COLOR_normal%


