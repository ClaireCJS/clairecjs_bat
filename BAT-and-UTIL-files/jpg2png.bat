@Echo OFF

set  validate_in_path_message=You need to install ffmpeg. Try this command: winget install Gyan.FFmpeg --verbose ... or download a build at https://www.gyan.dev/ffmpeg/builds/
call validate-in-path ffmpeg.exe

set                                in_file=%1
call validate-environment-variable in_file
set                               out_file=%@NAME[%in_file].png
if   "%2"   ne   ""          (set out_file=%@NAME[%2].png)
if   exist  "%out_file%"   (del "%out_file%")

call less_important "Converting %italics_on%%blink_on%%in_file%%italics_off%%blink_off% to %italics_on%%blink_on%%out_file%%italics_off%%blink_off%

ffmpeg.exe -i "%in_file" "%out_file"

