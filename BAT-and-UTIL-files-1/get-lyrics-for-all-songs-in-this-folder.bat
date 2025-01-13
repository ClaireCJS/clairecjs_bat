@loadbtm on
@on break cancel
@Echo OFF

call  validate-in-path               get-lyrics
call  validate-environment-variable  filemask_audio

for %file in (%filemask_audio%) do call get-lyrics "%file"

