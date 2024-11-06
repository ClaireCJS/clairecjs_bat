@Echo OFF

if %VALIDATED_DISPLAYMP3TAGS ne 1 (call validate-in-path metamp3 ffprobe eye3d sed)
set VALIDATED_DISPLAYMP3TAGS=1

metamp3 --info %*


ffprobe -i %*


rem nope ffprobe -v quiet -print_format json -show_entries format_tags=lyrics %*
rem Yup:
call display-lyrics %*
